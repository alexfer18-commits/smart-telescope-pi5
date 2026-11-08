#!/usr/bin/env python3
"""Synthetic campaign for protocol v3: 3 architectures x 3 illuminations x 30.

    python experiments/simulate_v3.py
    python experiments/simulate_v3.py --seed 7 --out data/simulated_results_v3.csv

Every row is written with ``source = "synthetic"``. There is no code path in
this file that produces any other value, and the Hailo rows additionally carry
``measurement_status = "not_measured"`` because no ``.hef`` exists to measure
them with. The numbers exist to exercise the statistics pipeline, not to
describe the instrument.

The rows are built from the same event shapes the broker carries, so the
simulator and the real harness agree on the log schema: state on
``telescope/status/state``, commands on ``telescope/commands/cmd``, refusals on
``telescope/pi/rejected``. ``--publish`` replays them to a live broker.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "benchmarks"))

from compare_inference import LATENCY_MODEL_MS, POWER_W  # noqa: E402

ARCHITECTURES = ["cpu_onnx", "hailo8l", "cloud_lambda"]
ILLUMINATIONS = ["dark", "suburban", "moonlight"]
REPETITIONS = 30

# Same topic names as pi5-software/mqtt_bridge.py and docker/mosquitto/acl_file.
TOPICS = {
    "state": "telescope/status/state",
    "command": "telescope/commands/cmd",
    "rejected": "telescope/pi/rejected",
}

# Sky conditions, as measured with an SQM at the zenith.
SKY = {
    "dark":      {"sqm": 21.5, "stars": (40, 120), "fwhm": 2.4},
    "suburban":  {"sqm": 18.5, "stars": (15, 40),  "fwhm": 2.9},
    "moonlight": {"sqm": 16.5, "stars": (6, 15),   "fwhm": 3.4},
}

# Pointing-error model, arcmin. Documented so it can be argued with, and so the
# synthetic origin is obvious: these are chosen constants, not fitted values.
BASE_ARCMIN = {"cpu_onnx": 4.0, "hailo8l": 3.7, "cloud_lambda": 4.6}
ILLUM_PENALTY = {"dark": 0.0, "suburban": 1.3, "moonlight": 2.9}
# Longer correction latency costs more when the solve is already marginal, so
# the interaction is not symmetric: the cloud path pays twice under moonlight
# (fewer stars, more retries, a coarser correction cadence).
INTERACTION = {
    ("cpu_onnx", "dark"): 0.0, ("cpu_onnx", "suburban"): 0.0,
    ("cpu_onnx", "moonlight"): 0.4,
    ("hailo8l", "dark"): 0.0, ("hailo8l", "suburban"): 0.1,
    ("hailo8l", "moonlight"): 0.3,
    ("cloud_lambda", "dark"): 0.0, ("cloud_lambda", "suburban"): 0.3,
    ("cloud_lambda", "moonlight"): 1.6,
}
SIGMA_ARCMIN = 1.1          # episode-to-episode
SIGMA_NIGHT = 0.4           # night-to-night (seeing, transparency)

OBJECTS = ["M31", "M42", "M45", "M51", "M57", "M63", "M64", "M65", "M81", "M82",
           "M87", "M92", "M101", "M104", "M106", "NGC253", "NGC869", "NGC884",
           "NGC891", "NGC7000", "NGC7331", "IC1396", "IC5070", "M13", "M15",
           "M27", "M33", "M35", "M44", "M97"]


def episode(arch: str, illum: str, rep: int, night_rng: float,
            rng: np.random.Generator) -> dict:
    sky = SKY[illum]
    median, sigma = LATENCY_MODEL_MS[arch]
    latency_ms = float(rng.lognormal(math.log(median), sigma))

    mean = (BASE_ARCMIN[arch] + ILLUM_PENALTY[illum]
            + INTERACTION[(arch, illum)] + night_rng)
    error = float(rng.normal(mean, SIGMA_ARCMIN))

    lo, hi = sky["stars"]
    stars = int(np.clip(rng.normal((lo + hi) / 2, (hi - lo) / 6), lo, hi))
    fwhm = float(np.clip(rng.normal(sky["fwhm"], 0.35), 1.8, 4.6))
    ambient = float(rng.normal(11.0, 3.0))

    energy_wh = None
    if POWER_W[arch] > 0:
        energy_wh = round(POWER_W[arch] * (latency_ms + 3000.0) / 3_600_000.0, 6)

    return {
        "episode_id": f"{arch}-{illum}-{rep:03d}",
        "night_id": "2026-11-14",
        "architecture": arch,
        "illumination": illum,
        "repetition": rep,
        "object_id": OBJECTS[(rep - 1) % len(OBJECTS)],
        "latency_ms": round(latency_ms, 3),
        "error_arcmin": round(error, 3),
        "n_stars": stars,
        "fwhm_arcsec": round(fwhm, 2),
        "ambient_c": round(ambient, 1),
        "energy_wh": energy_wh,
        "valid": "true",
        # The only provenance this file can honestly emit.
        "source": "synthetic",
        "measurement_status": ("not_measured" if arch == "hailo8l" else "synthetic"),
        "sqm": sky["sqm"],
    }


def status_payload(row: dict) -> dict:
    """The same shape the Pi publishes on telescope/status/state."""
    return {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ra_deg": 210.0,
        "dec_deg": 54.0,
        "tracking": True,
        "error_arcmin": row["error_arcmin"],
        "source": row["source"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261108)
    parser.add_argument("--out", type=Path,
                        default=ROOT / "data" / "simulated_results_v3.csv")
    parser.add_argument("--publish", action="store_true",
                        help="replay states to the live broker (needs MQTT_USER)")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    # one shared "night" per architecture-illumination cell, as in the protocol
    night = {(a, l): float(rng.normal(0, SIGMA_NIGHT))
             for a in ARCHITECTURES for l in ILLUMINATIONS}

    rows = [episode(a, l, r, night[(a, l)], rng)
            for a in ARCHITECTURES for l in ILLUMINATIONS
            for r in range(1, REPETITIONS + 1)]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    assert len(rows) == 270, len(rows)
    assert all(r["source"] == "synthetic" for r in rows)
    assert sum(r["measurement_status"] == "not_measured" for r in rows) == 90

    print(f"wrote {args.out} ({len(rows)} rows, all source=synthetic)")

    if args.publish:
        import os

        import paho.mqtt.client as mqtt

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                             client_id="simulate-v3")
        client.username_pw_set(os.environ["MQTT_USER"], os.environ["MQTT_PASSWORD"])
        client.tls_set(ca_certs=str(ROOT / "docker/mosquitto/certs/ca.crt"))
        client.connect(os.environ.get("MQTT_HOST", "localhost"),
                       int(os.environ.get("MQTT_PORT", "8883")))
        client.loop_start()
        for row in rows:
            client.publish(TOPICS["state"], json.dumps(status_payload(row)), qos=0)
            time.sleep(0.01)
        client.loop_stop()
        client.disconnect()
        print(f"replayed {len(rows)} states on {TOPICS['state']}")


if __name__ == "__main__":
    main()
