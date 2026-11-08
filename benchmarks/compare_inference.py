#!/usr/bin/env python3
"""Benchmark the three inference substrates for the plate-solving workload.

    python benchmarks/compare_inference.py --episodes 200
    python benchmarks/compare_inference.py --model models/star_detector_int8.onnx --runtime auto

What is measured and what is modelled
-------------------------------------
* Latency and throughput: measured when a runtime is present (TFLite, ONNX
  Runtime, HailoRT), otherwise drawn from a documented latency model and
  flagged ``"source": "synthetic"`` in the JSON. Never report synthetic numbers
  as measurements.
* Energy: measured on the Pi through an INA219 shunt when ``--ina219`` is
  given; otherwise estimated from CPU utilisation and the board's power
  envelope, and flagged ``"energy_source": "modelled"``.
* Cost: computed from a stated utilisation model, not measured.

Outputs ``data/benchmark_results.json`` and ``figures/benchmark_comparison.pdf``.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
FIG_DIR = ROOT / "figures"

# Documented latency models, milliseconds. Sources: vendor datasheets and the
# edge-AI comparison literature surveyed in the SLR (Jeong 2026; Podbucki 2026).
LATENCY_MODEL_MS = {
    "cpu_tflite": (165.0, 0.22),     # median, lognormal sigma
    "cpu_onnx": (150.0, 0.20),
    "hailo8l": (16.0, 0.12),
    "cloud_lambda": (210.0, 0.45),   # includes network transit and cold starts
}

# Power envelope of the board plus peripherals, watts.
POWER_W = {"cpu_tflite": 7.5, "cpu_onnx": 7.5, "hailo8l": 9.8, "cloud_lambda": 0.0}

CLOUD_USD_PER_INFERENCE = 2.0e-7
CAPEX_USD = {"cpu_tflite": 0.0, "cpu_onnx": 0.0, "hailo8l": 70.0, "cloud_lambda": 0.0}
AMORTISE_MONTHS = 24


@dataclass
class Result:
    backend: str
    source: str
    n: int
    p50_ms: float
    p95_ms: float
    mean_ms: float
    throughput_per_s: float
    energy_wh_per_1000: float
    energy_source: str
    usd_per_1000: float


def _lognormal_samples(median_ms: float, sigma: float, n: int,
                       rng: np.random.Generator) -> np.ndarray:
    return median_ms * np.exp(rng.normal(0.0, sigma, n))


def _measure_onnx(model: Path, n: int, rng: np.random.Generator) -> np.ndarray | None:
    try:
        import onnxruntime as ort
    except ImportError:
        return None
    session = ort.InferenceSession(str(model), providers=["CPUExecutionProvider"])
    shape = session.get_inputs()[0].shape
    shape = [d if isinstance(d, int) else 1 for d in shape]
    tensor = rng.standard_normal(shape).astype(np.float32)
    name = session.get_inputs()[0].name
    for _ in range(3):                       # warm-up, excluded from samples
        session.run(None, {name: tensor})
    samples = np.empty(n)
    for i in range(n):
        started = time.perf_counter()
        session.run(None, {name: tensor})
        samples[i] = (time.perf_counter() - started) * 1000.0
    return samples


def _measure_tflite(model: Path, n: int, rng: np.random.Generator) -> np.ndarray | None:
    try:
        from tflite_runtime.interpreter import Interpreter  # type: ignore
    except ImportError:
        try:
            from tensorflow.lite.python.interpreter import Interpreter  # type: ignore
        except ImportError:
            return None
    interp = Interpreter(model_path=str(model), num_threads=4)
    interp.allocate_tensors()
    detail = interp.get_input_details()[0]
    tensor = rng.standard_normal(detail["shape"]).astype(detail["dtype"])
    interp.set_tensor(detail["index"], tensor)
    for _ in range(3):
        interp.invoke()
    samples = np.empty(n)
    for i in range(n):
        started = time.perf_counter()
        interp.invoke()
        samples[i] = (time.perf_counter() - started) * 1000.0
    return samples


def _measure_hailo(model: Path, n: int, rng: np.random.Generator) -> np.ndarray | None:
    try:
        from hailo_platform import VDevice  # type: ignore
    except ImportError:
        return None
    if model.suffix != ".hef":
        return None
    with VDevice() as device:
        network = device.create_infer_model(str(model))
        network.set_batch_size(1)
        with network.configure() as configured:
            for _ in range(3):
                configured.run([np.zeros((1, 256, 256, 1), np.uint8)])
            samples = np.empty(n)
            for i in range(n):
                started = time.perf_counter()
                configured.run([np.zeros((1, 256, 256, 1), np.uint8)])
                samples[i] = (time.perf_counter() - started) * 1000.0
    return samples


def _cpu_fraction(samples: np.ndarray, baseline_ms: float) -> float:
    """Rough duty cycle the workload imposes on the board."""
    return float(np.clip(baseline_ms / max(samples.mean(), 1e-6), 0.05, 1.0))


def benchmark(model: Path | None, n: int, runtime: str,
              ina219: bool, seed: int = 0) -> list[Result]:
    rng = np.random.default_rng(seed)
    results: list[Result] = []
    cpu_power = POWER_W["cpu_tflite"]
    hailo_power = POWER_W["hailo8l"]

    measured: dict[str, np.ndarray | None] = {"cpu_tflite": None, "cpu_onnx": None,
                                              "hailo8l": None}
    if model is not None and runtime in {"auto", "tflite"}:
        measured["cpu_tflite"] = _measure_tflite(model, n, rng)
    if model is not None and runtime in {"auto", "onnx"}:
        measured["cpu_onnx"] = _measure_onnx(model, n, rng)
    if model is not None and runtime in {"auto", "hailo"}:
        measured["hailo8l"] = _measure_hailo(model, n, rng)

    energy = EnergyMeter(ina219)

    for name, median_sigma in LATENCY_MODEL_MS.items():
        samples = measured.get(name)
        source = "measured" if samples is not None else "synthetic"
        if samples is None:
            samples = _lognormal_samples(median_sigma[0], median_sigma[1], n, rng)

        if name.startswith("cpu"):
            watts = energy.watts(cpu_power, _cpu_fraction(samples, median_sigma[0]))
            energy_source = energy.source
        elif name == "hailo8l":
            watts = energy.watts(hailo_power, 1.0)
            energy_source = energy.source
        else:
            # cloud: amortise the server's share; 0.06 kWh per 1000 inferences
            # at a documented PUE of 1.2 is the figure used in the paper.
            watts = 0.0
            energy_source = "modelled (datasheet)"

        wh_per_1000 = (watts * (samples.mean() / 1000.0) * 1000.0 / 3600.0
                       if watts else 0.06)

        capex = CAPEX_USD[name]
        usd_per_1000 = (capex / (AMORTISE_MONTHS * 30 * 24 * 3600)
                        * (samples.mean() / 1000.0) * 1000.0
                        + (CLOUD_USD_PER_INFERENCE * 1000.0 if name == "cloud_lambda" else 0.0))

        results.append(Result(
            backend=name, source=source, n=int(samples.size),
            p50_ms=round(float(np.percentile(samples, 50)), 3),
            p95_ms=round(float(np.percentile(samples, 95)), 3),
            mean_ms=round(float(samples.mean()), 3),
            throughput_per_s=round(1000.0 / float(samples.mean()), 2),
            energy_wh_per_1000=round(float(wh_per_1000), 4),
            energy_source=energy_source,
            usd_per_1000=round(float(usd_per_1000), 6),
        ))
    return results


class EnergyMeter:
    """INA219 when present, otherwise a documented power model."""

    def __init__(self, use_ina219: bool) -> None:
        self._ina = None
        self.source = "modelled"
        if use_ina219:
            try:
                from ina219 import INA219  # type: ignore
                self._ina = INA219(shunt_ohms=0.1)
                self._ina.configure()
                self.source = "measured (INA219)"
            except Exception as exc:
                print(f"INA219 unavailable ({exc}); falling back to the power model")

    def watts(self, max_watts: float, fraction: float) -> float:
        if self._ina is not None:
            return float(self._ina.power()) / 1000.0
        return max_watts * (0.45 + 0.55 * fraction)   # idle floor + load share


def crossover_utilisation(results: list[Result], sessions_per_month: int = 8,
                          solves_per_session: int = 50) -> dict:
    """Monthly inferences at which accelerator and cloud costs are equal."""
    accel = next((r for r in results if r.backend == "hailo8l"), None)
    if accel is None:
        return {}
    monthly = sessions_per_month * solves_per_session
    accel_monthly = CAPEX_USD["hailo8l"] / AMORTISE_MONTHS
    cloud_monthly = monthly * CLOUD_USD_PER_INFERENCE
    breakeven = accel_monthly / CLOUD_USD_PER_INFERENCE if CLOUD_USD_PER_INFERENCE else math.inf
    return {
        "amateur_monthly_inferences": monthly,
        "amateur_cost_accelerator_usd": round(accel_monthly, 2),
        "amateur_cost_cloud_usd": round(cloud_monthly, 4),
        "breakeven_inferences_per_month": round(breakeven, 0),
        "cheaper_at_amateur_utilisation": ("cloud" if cloud_monthly < accel_monthly
                                          else "accelerator"),
    }


def plot(results: list[Result], out_path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = [r.backend for r in results]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.0, 3.6))

    x = np.arange(len(names))
    ax1.bar(x - 0.2, [r.p50_ms for r in results], 0.4, label="p50")
    ax1.bar(x + 0.2, [r.p95_ms for r in results], 0.4, label="p95")
    ax1.set_xticks(x, names, rotation=20, ha="right")
    ax1.set_ylabel("latency (ms)")
    ax1.set_title("Solve latency")
    ax1.legend(frameon=False)

    utilisation = np.logspace(1, 6, 120)          # inferences per month
    cloud = utilisation * CLOUD_USD_PER_INFERENCE
    ax2.plot(utilisation, cloud, label="cloud (per inference)")
    for r in results:
        if r.backend == "hailo8l":
            ax2.axhline(CAPEX_USD["hailo8l"] / AMORTISE_MONTHS, ls="--",
                        label="Hailo-8L (amortised capex)")
        if r.backend == "cpu_tflite":
            ax2.axhline(0.01, ls=":", label="CPU (sunk)")
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel("inferences per month")
    ax2.set_ylabel("USD per month")
    ax2.set_title("Cost crossover")
    ax2.legend(frameon=False, fontsize=7)

    synthetic = any(r.source == "synthetic" for r in results)
    note = ("SYNTHETIC latency model — not a measurement" if synthetic
            else "measured on this host")
    fig.text(0.01, 0.01, note, fontsize=7, color="crimson" if synthetic else "black")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    print(f"figure -> {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=None,
                        help="ONNX, TFLite, or HEF file to run")
    parser.add_argument("--episodes", type=int, default=200)
    parser.add_argument("--runtime", choices=["auto", "tflite", "onnx", "hailo"],
                        default="auto")
    parser.add_argument("--ina219", action="store_true",
                        help="measure power from the INA219 shunt on the Pi")
    parser.add_argument("--out", type=Path, default=DATA_DIR / "benchmark_results.json")
    parser.add_argument("--figure", type=Path, default=FIG_DIR / "benchmark_comparison.pdf")
    args = parser.parse_args()

    results = benchmark(args.model, args.episodes, args.runtime, args.ina219)
    payload = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": platform.python_version()},
        "assumptions": {
            "cloud_usd_per_inference": CLOUD_USD_PER_INFERENCE,
            "capex_usd": CAPEX_USD,
            "amortise_months": AMORTISE_MONTHS,
            "latency_model_ms": LATENCY_MODEL_MS,
        },
        "results": [asdict(r) for r in results],
        "crossover": crossover_utilisation(results),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))
    plot(results, args.figure)


if __name__ == "__main__":
    main()
