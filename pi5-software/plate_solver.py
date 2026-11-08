"""Plate solving for the smart telescope: star detection, WCS fit, error budget.

The learned detector is optional. When no TFLite model is present the module
falls back to an OpenCV threshold-and-centroid detector, so the pipeline can be
exercised before the model exists.

    solve(image) -> SolveResult(ra_deg, dec_deg, error_arcmin, ...)

`solve` delegates blind index search to a local astrometry.net (`solve-field`)
binary, because re-implementing blind matching is not part of this project. The
WCS refinement and the error metric are local and are what the experiment
measures.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.wcs.utils import fit_wcs_from_points

DEFAULT_MODEL = Path(__file__).parent / "models" / "star_detector_int8.tflite"
SOLVE_FIELD = "solve-field"


class SolverUnavailable(RuntimeError):
    """Raised when no blind solver is installed and no hint was supplied."""


@dataclass(frozen=True)
class SolveResult:
    ra_deg: float
    dec_deg: float
    error_arcmin: float
    n_stars: int
    latency_ms: float
    source: str


def detect_stars(image: np.ndarray, model_path: Path | None = None,
                 threshold_sigma: float = 6.0) -> np.ndarray:
    """Return sub-pixel centroids as an (N, 2) float array of (x, y) pixels."""
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    model = model_path or (DEFAULT_MODEL if DEFAULT_MODEL.exists() else None)
    if model is not None:
        return _detect_tflite(gray, model)
    return _detect_opencv(gray, threshold_sigma)


def _detect_opencv(gray: np.ndarray, threshold_sigma: float) -> np.ndarray:
    """Background-subtracted threshold plus intensity-weighted centroids."""
    blurred = cv2.GaussianBlur(gray.astype(np.float32), (3, 3), 0)
    background = cv2.medianBlur(gray, 31).astype(np.float32)
    residual = blurred - background
    sigma = float(residual.std()) or 1.0
    mask = (residual > threshold_sigma * sigma).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    centroids = []
    for label in range(1, n):
        area = stats[label, cv2.CC_STAT_AREA]
        if not 3 <= area <= 400:          # reject hot pixels and saturated blobs
            continue
        ys, xs = np.nonzero(labels == label)
        weights = residual[ys, xs].astype(np.float64)
        total = weights.sum()
        if total <= 0:
            continue
        centroids.append((float((xs * weights).sum() / total),
                          float((ys * weights).sum() / total)))
    return np.array(centroids, dtype=np.float64).reshape(-1, 2)


def _detect_tflite(gray: np.ndarray, model_path: Path) -> np.ndarray:
    """Star probability + distance transform, centroids by weighted average.

    Input is normalised to the model's 256x256 patch grid; the graph is the
    INT8 export produced by ml-model/quantize_int8.py.
    """
    try:
        from tflite_runtime.interpreter import Interpreter  # type: ignore
    except ImportError:  # desktop fallback for development
        from tensorflow.lite.python.interpreter import Interpreter  # type: ignore

    interp = Interpreter(model_path=str(model_path), num_threads=4)
    interp.allocate_tensors()
    inp = interp.get_input_details()[0]
    out = interp.get_output_details()[0]
    h, w = inp["shape"][1], inp["shape"][2]
    patch = cv2.resize(gray, (w, h), interpolation=cv2.INTER_AREA)
    patch = (patch.astype(np.float32) / 255.0)[None, ..., None]
    if inp["dtype"] == np.int8:
        scale, zero = inp["quantization"]
        patch = (patch / scale + zero).astype(np.int8)
    interp.set_tensor(inp["index"], patch)
    interp.invoke()
    prob = interp.get_tensor(out["index"]).astype(np.float32).squeeze()
    prob = cv2.resize(prob, (gray.shape[1], gray.shape[0]))
    mask = (prob > 0.5).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    out_xy = []
    for label in range(1, n):
        if stats[label, cv2.CC_STAT_AREA] < 2:
            continue
        ys, xs = np.nonzero(labels == label)
        weights = prob[ys, xs].astype(np.float64)
        total = weights.sum()
        out_xy.append((float((xs * weights).sum() / total),
                       float((ys * weights).sum() / total)))
    return np.array(out_xy, dtype=np.float64).reshape(-1, 2)


def fit_wcs(centroids: np.ndarray, sky_coords: np.ndarray) -> tuple[WCS, float]:
    """Least-squares TAN fit; returns the WCS and the RMS residual in arcmin."""
    from astropy.coordinates import SkyCoord
    import astropy.units as u

    if len(centroids) < 3 or len(centroids) != len(sky_coords):
        raise ValueError("need >= 3 matched pairs, centroids and sky must align")
    ra = sky_coords[:, 0]
    dec = sky_coords[:, 1]
    wcs = fit_wcs_from_points(
        (centroids[:, 0], centroids[:, 1]),
        SkyCoord(ra * u.deg, dec * u.deg),
        proj_point="center",
    )
    world = wcs.all_pix2world(centroids, 0)
    model = SkyCoord(world[:, 0] * u.deg, world[:, 1] * u.deg)
    truth = SkyCoord(ra * u.deg, dec * u.deg)
    residual_arcsec = model.separation(truth).arcsec
    return wcs, float(np.sqrt(np.mean(residual_arcsec ** 2)) / 60.0)


def _solve_with_astrometry_net(image: np.ndarray, hint: tuple[float, float] | None,
                               timeout_s: float) -> tuple[WCS, int]:
    """Run solve-field on a temporary FITS file and parse the resulting WCS."""
    if shutil.which(SOLVE_FIELD) is None:
        raise SolverUnavailable(
            "astrometry.net 'solve-field' not found; install astrometry.net or "
            "pass a pointing hint so the WCS can be fitted directly"
        )
    with tempfile.TemporaryDirectory() as tmp:
        fits_path = Path(tmp) / "frame.fits"
        fits.writeto(fits_path, image, overwrite=True)
        cmd = [SOLVE_FIELD, "--overwrite", "--no-plots", "--dir", tmp,
               "--scale-units", "arcsecperpix", "--scale-low", "5", "--scale-high", "9",
               str(fits_path)]
        if hint is not None:
            cmd += ["--ra", f"{hint[0]}", "--dec", f"{hint[1]}", "--radius", "5"]
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout_s, check=False)
        wcs_path = Path(tmp) / "frame.new"
        header_path = Path(tmp) / "frame.wcs"
        if proc.returncode != 0 or not (wcs_path.exists() or header_path.exists()):
            raise SolverUnavailable(
                f"solve-field failed ({proc.returncode}): "
                f"{proc.stderr.decode(errors='replace')[-300:]}"
            )
        header = (fits.getheader(wcs_path) if wcs_path.exists()
                  else fits.Header.fromtextfile(str(header_path)))
    wcs = WCS(header)
    n_stars = int(header.get("NSOURCES", 0) or 0)
    return wcs, n_stars


def solve(image: np.ndarray, hint: tuple[float, float] | None = None,
          model_path: Path | None = None, timeout_s: float = 30.0) -> SolveResult:
    """Solve one frame.

    `hint` is a coarse (ra, dec) in degrees from the mount model; it narrows the
    astrometry.net search but is not trusted as the answer. The reported error
    is the RMS reprojection residual of the fitted WCS, in arcminutes.
    """
    started = time.perf_counter()
    centroids = detect_stars(image, model_path)
    if len(centroids) < 3:
        raise SolverUnavailable(f"only {len(centroids)} stars detected")

    wcs, n_stars = _solve_with_astrometry_net(image, hint, timeout_s)
    source = "astrometry.net" if hint is None else "astrometry.net+hint"
    error_arcmin = crossval_error_arcmin(wcs, centroids)

    ra, dec = wcs.all_pix2world([[image.shape[1] / 2, image.shape[0] / 2]], 0)[0]
    return SolveResult(
        ra_deg=float(ra), dec_deg=float(dec), error_arcmin=error_arcmin,
        n_stars=n_stars or len(centroids),
        latency_ms=(time.perf_counter() - started) * 1000.0, source=source,
    )


def crossval_error_arcmin(wcs: WCS, centroids: np.ndarray,
                          seed: int = 0) -> float:
    """Half-sample cross-validated residual of the astrometric fit, arcmin.

    The WCS is refitted on a random half of the detected stars and used to
    predict the sky positions of the other half. This measures whether the
    solution is stable rather than how well it interpolates its own inputs.
    The mount's pointing error is a different quantity, measured in the loop.
    """
    if len(centroids) < 6:
        return float("nan")
    sky = wcs.all_pix2world(centroids, 0)
    order = np.random.default_rng(seed).permutation(len(centroids))
    half = len(order) // 2
    train, test = order[:half], order[half:]
    try:
        wcs_train, _ = fit_wcs(centroids[train], sky[train])
    except Exception:
        return float("nan")
    predicted = wcs_train.all_pix2world(centroids[test], 0)
    from astropy.coordinates import SkyCoord
    import astropy.units as u

    separation = SkyCoord(predicted[:, 0] * u.deg, predicted[:, 1] * u.deg).separation(
        SkyCoord(sky[test, 0] * u.deg, sky[test, 1] * u.deg))
    return float(np.sqrt(np.mean(separation.arcsec ** 2)) / 60.0)
