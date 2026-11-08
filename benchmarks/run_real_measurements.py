#!/usr/bin/env python3
"""Real measurements on the Raspberry Pi 5: latency, throughput, energy.

    # on the Pi, with a quantized model and the INA219 wired
    python benchmarks/run_real_measurements.py \
        --model ml-model/mnv3_int8.onnx --episodes 300 --ina219

    # without the shunt (energy is then reported as null, never estimated)
    python benchmarks/run_real_measurements.py --model ml-model/mnv3_int8.tflite

Unlike ``compare_inference.py``, this script has no fallback: if a runtime or a
model is missing it says so and skips that substrate. Every row it writes is
``"source": "measured"`` or absent — there is no synthetic path here on purpose,
because this is the script whose output goes into the paper.

Output: ``data/real_measurements.json``
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import threading
import time
from pathlib import Path

import numpy as np

from compare_inference import (CAPEX_USD, CLOUD_USD_PER_INFERENCE, hailo_runtime_available,
                               measure_hailo, measure_onnx, measure_tflite)

ROOT = Path(__file__).resolve().parent.parent


class PowerSampler:
    """Integrates INA219 power over the measurement window.

    Sampling at 10 Hz is enough for a workload whose shortest event is tens of
    milliseconds; it is not enough to resolve per-inference energy, which is why
    energy is reported per 1000 inferences and per session, never per call.
    """

    def __init__(self, enabled: bool) -> None:
        self.available = False
        self._ina = None
        self._samples: list[tuple[float, float]] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        if not enabled:
            return
        try:
            from ina219 import INA219  # type: ignore

            self._ina = INA219(shunt_ohms=0.1)
            self._ina.configure()
            self.available = True
        except Exception as exc:
            print(f"INA219 unavailable: {exc}")

    def _run(self) -> None:
        started = time.monotonic()
        while not self._stop.is_set():
            try:
                self._samples.append((time.monotonic() - started,
                                      float(self._ina.power()) / 1000.0))
            except Exception:
                pass
            self._stop.wait(0.1)

    def start(self) -> None:
        if not self.available:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> tuple[float, float] | None:
        """Return (mean watts, watt-hours) for the window, or None."""
        if not self.available or self._thread is None:
            return None
        self._stop.set()
        self._thread.join(timeout=2.0)
        if len(self._samples) < 2:
            return None
        times = np.array([s[0] for s in self._samples])
        watts = np.array([s[1] for s in self._samples])
        watt_hours = float(np.trapz(watts, times) / 3600.0)
        return float(watts.mean()), watt_hours


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=300)
    parser.add_argument("--ina219", action="store_true")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "real_measurements.json")
    args = parser.parse_args()

    if not args.model.exists():
        raise SystemExit(f"model not found: {args.model}")

    rng = np.random.default_rng(0)
    runners = {}
    if args.model.suffix == ".tflite":
        runners["cpu_tflite"] = measure_tflite
    elif args.model.suffix == ".onnx":
        runners["cpu_onnx"] = measure_onnx
    elif args.model.suffix == ".hef":
        runners["hailo8l"] = measure_hailo
    else:
        raise SystemExit("model must be .tflite, .onnx, or .hef")

    power = PowerSampler(args.ina219)
    rows = []
    for name, runner in runners.items():
        print(f"measuring {name} with {args.model.name} ...")
        power.start()
        started = time.monotonic()
        samples = runner(args.model, args.episodes, rng)
        elapsed = time.monotonic() - started
        energy = power.stop()

        if samples is None:
            print(f"  skipped: {name} runtime not available on this host")
            continue

        mean_ms = float(samples.mean())
        row = {
            "backend": name,
            "source": "measured",
            "n": int(samples.size),
            "p50_ms": round(float(np.percentile(samples, 50)), 3),
            "p95_ms": round(float(np.percentile(samples, 95)), 3),
            "mean_ms": round(mean_ms, 3),
            "throughput_per_s": round(1000.0 / mean_ms, 2),
            "wall_clock_s": round(elapsed, 2),
        }
        if energy is not None:
            watts, watt_hours = energy
            row.update({
                "energy_source": "measured (INA219)",
                "mean_watts": round(watts, 3),
                "energy_wh_per_1000": round(watts * (mean_ms / 1000.0) * 1000.0 / 3600.0, 4),
                "energy_wh_total": round(watt_hours, 4),
            })
        else:
            row.update({"energy_source": "not measured", "mean_watts": None,
                        "energy_wh_per_1000": None, "energy_wh_total": None})
        rows.append(row)
        print(f"  p50 {row['p50_ms']} ms | p95 {row['p95_ms']} ms | "
              f"{row['throughput_per_s']} inf/s")

    if not rows:
        raise SystemExit(
            "nothing measured. Install a runtime (pip install onnxruntime or "
            "tflite-runtime) and pass a matching model, or run the synthetic "
            "harness: python benchmarks/compare_inference.py")

    payload = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": platform.python_version(), "node": platform.node()},
        "model": {"path": str(args.model), "sha256": _sha256(args.model),
                  "bytes": args.model.stat().st_size},
        "hailo_available": hailo_runtime_available(),
        "assumptions": {"capex_usd": CAPEX_USD,
                        "cloud_usd_per_inference": CLOUD_USD_PER_INFERENCE},
        "results": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
