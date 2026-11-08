#!/usr/bin/env python3
"""Compare the FP32 and INT8 graphs by the only metric that matters: arcseconds.

    python ml-model/check_equivalence.py model.onnx model_int8.onnx \
        --frames data/calibration_frames --plate-scale-arcsec 6.9

Reports the maximum and 95th-percentile centroid displacement between the two
graphs. Displacement is measured on the probability map's local maxima, which is
what the solver consumes; a global pixel L2 is not informative because a
sub-pixel shift of the whole map is exactly the error we are looking for.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def _centroids(prob: np.ndarray, threshold: float = 0.5) -> np.ndarray:
    import cv2
    mask = (prob > threshold).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    points = []
    for label in range(1, n):
        if stats[label, cv2.CC_STAT_AREA] < 2:
            continue
        ys, xs = np.nonzero(labels == label)
        weights = prob[ys, xs].astype(np.float64)
        points.append((float((xs * weights).sum() / weights.sum()),
                       float((ys * weights).sum() / weights.sum())))
    return np.array(points).reshape(-1, 2)


def _nearest(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    if len(a) == 0 or len(b) == 0:
        return np.array([np.nan])
    return np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2).min(axis=1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fp32", type=Path)
    parser.add_argument("int8", type=Path)
    parser.add_argument("--frames", type=Path, required=True)
    parser.add_argument("--plate-scale-arcsec", type=float, default=6.9)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    import onnxruntime as ort

    a = ort.InferenceSession(str(args.fp32), providers=["CPUExecutionProvider"])
    b = ort.InferenceSession(str(args.int8), providers=["CPUExecutionProvider"])
    name = a.get_inputs()[0].name
    shape = [d if isinstance(d, int) else 1 for d in a.get_inputs()[0].shape]

    import cv2
    frames = sorted(p for p in args.frames.iterdir()
                    if p.suffix.lower() in {".png", ".jpg", ".jpeg"})[: args.limit]
    if not frames:
        raise SystemExit(f"no frames under {args.frames}")

    displacements = []
    for frame in frames:
        image = cv2.imread(str(frame), cv2.IMREAD_GRAYSCALE)
        image = cv2.resize(image, (shape[2], shape[1])).astype(np.float32) / 255.0
        tensor = image.reshape(shape)
        pa = a.run(None, {name: tensor})[0].squeeze()
        pb = b.run(None, {name: tensor})[0].squeeze()
        ca, cb = _centroids(pa), _centroids(pb)
        if len(ca) and len(cb):
            displacements.append(np.nanmax(_nearest(ca, cb)))

    if not displacements:
        raise SystemExit("no stars detected in either graph; check the model output")

    d = np.array(displacements)
    print(f"frames: {len(d)}")
    print(f"max displacement: {d.max():.3f} px "
          f"({d.max() * args.plate_scale_arcsec:.1f} arcsec)")
    print(f"p95 displacement: {np.percentile(d, 95):.3f} px "
          f"({np.percentile(d, 95) * args.plate_scale_arcsec:.1f} arcsec)")
    verdict = "OK" if d.max() <= 0.2 else "REVIEW: quantization shifted centroids"
    print(verdict)


if __name__ == "__main__":
    main()
