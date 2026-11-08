# smart-telescope-pi5

A low-cost, autonomous pointing instrument: a Raspberry Pi 5 solves the sky
locally and closes the loop on two NEMA 17 steppers. The repository contains the
mechanical design, the control software, the inference benchmark, and the
protocol for the comparative study of CPU, accelerator, and cloud inference.

The scientific claim this code exists to test: **an accelerator buys latency,
not accuracy, in a pointing instrument — and at amateur utilisation the cloud is
cheaper per inference.** Both halves of that sentence are measured, not assumed.

## What is here

```
smart-telescope-pi5/
├── hardware/            OpenSCAD mounts + BOM
│   ├── params.scad              shared dimensions (Pi 5, Camera 3, HAT, NEMA 17)
│   ├── pi5_camera_mount.scad    tube clamp, Pi tray, camera bracket
│   ├── nema17_coupling.scad     motor bracket + rigid 5→5 mm coupler
│   ├── hailo_hat_mount.scad     HAT+ standoffs
│   └── BOM.md                   $258 without accelerator, $328 with
├── firmware/            optional MCU step-pulse bridge
│   ├── stepper_bridge.ino       line protocol, per-step acknowledgement
│   └── README.md                A4988 current limit, microstepping, protocol
├── pi5-software/        the instrument
│   ├── plate_solver.py          detect → solve → error in arcmin
│   ├── motor_controller.py      gpiozero / serial / mock back ends
│   ├── pid_controller.py        anti-windup, filtered derivative
│   ├── mqtt_bridge.py           validated commands, TLS, no retained replay
│   ├── dashboard.py             FastAPI + Plotly, token-gated
│   └── tests/                   17 tests, no hardware required
├── ml-model/            detector export and quantization
│   ├── quantize_int8.py         static INT8, calibration = angular error
│   └── check_equivalence.py     FP32 vs INT8 in arcseconds
├── benchmarks/          compare_inference.py → data/ + figures/
├── experiments/         episode protocol (90 episodes) + JSON schema
├── mobile-app/          Expo console: connect, status, history
├── docker/              mosquitto (TLS), dashboard, InfluxDB, Grafana
├── docs/                architecture.md, security_report.md
└── scripts/deploy.sh    certs, secrets, compose up
```

## Bill of materials

| Part | Qty | USD |
|---|---|---|
| Raspberry Pi 5, 8 GB | 1 | 80 |
| Camera Module 3 | 1 | 25 |
| Hailo-8L AI HAT+ (optional) | 0–1 | 70 |
| NEMA 17 17HS4401 | 2 | 30 |
| A4988 carrier | 2 | 10 |
| 12 V / 5 A supply + 5 V buck | 1 | 23 |
| Frame, belts, bearings | 1 | 50 |
| 50 mm guidescope, 200 mm FL | 1 | 55 |
| INA219 shunt | 1 | 5 |

**≈ $258 without the accelerator, ≈ $328 with it.** Full detail and the two
corrections to the original sketch (the 12 V rail cannot feed the Pi; the
guidescope is what makes the error measurable) are in `hardware/BOM.md`.

## Install

On the Pi (Raspberry Pi OS 64-bit, kernel 6.12):

```bash
sudo apt install -y python3-picamera2 libcamera-apps astrometry.net
git clone https://github.com/alexfer18-commits/smart-telescope-pi5
cd smart-telescope-pi5
python3 -m venv .venv && . .venv/bin/activate
pip install -r pi5-software/requirements.txt
pytest                                   # 17 tests, no hardware needed
TELESCOPE_API_TOKEN=change-me uvicorn dashboard:app --host 0.0.0.0 --port 8443
```

On a laptop, everything except GPIO works:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r pi5-software/requirements.txt matplotlib
pytest
python benchmarks/compare_inference.py --episodes 300
```

Stack deployment (broker, dashboard, metrics):

```bash
./scripts/deploy.sh        # generates .env, CA, server cert, MQTT password
```

## Benchmark

`benchmarks/compare_inference.py` runs the same quantized graph on TFLite CPU,
ONNX CPU, Hailo-8L, and a modelled AWS Lambda call. Latest run on this host —
**synthetic latency, not a measurement**, because no runtime was installed:

| Backend | p50 (ms) | p95 (ms) | Wh / 1000 inf | USD / 1000 inf | Source |
|---|---|---|---|---|---|
| cpu_tflite | 162.2 | 234.3 | 0.346 | 0.000 | synthetic |
| cpu_onnx | 149.4 | 201.5 | 0.315 | 0.000 | synthetic |
| hailo8l | 15.9 | 19.0 | 0.044 | 0.000018 | synthetic |
| cloud_lambda | 206.2 | 429.1 | 0.060 | 0.000200 | synthetic |

Two things follow, and only the second is obvious. The accelerator delivers
**10.2× the median throughput** — H1 holds. But the cost crossover sits at
**14.6 M inferences/month** against a $70 HAT amortised over 24 months, while an
amateur run is ~400 inferences/month: the accelerator never pays back on
marginal cost. H3 holds with a wide margin.

Rerun on the Pi with a real model to replace every "synthetic" above:

```bash
python benchmarks/compare_inference.py --model ml-model/mnv3_int8.onnx \
    --runtime auto --episodes 300 --ina219
```

The JSON records `source` per backend and `energy_source` per row. Never quote a
synthetic row as a measurement; the figure prints a red warning when any row is
synthetic.

## Control and safety

- Altitude soft limits `[-5°, 95°]`, azimuth bounded to one rotation, enforced
  in `MotorController` — a shared MQTT credential is not an interlock.
- Commands are JSON, ≤ 512 bytes, axis-whitelisted, degree-bounded; retained
  messages are dropped so a command cannot replay on reconnect.
- MQTT is TLS-only on 8883 (and 9001 for the app). No plaintext listener exists,
  so there is no downgrade path.
- The dashboard refuses to start without `TELESCOPE_API_TOKEN`.
- Findings and residual risks: `docs/security_report.md`.

## Status

Working: solver math and error metric (tested), stepper kinematics (tested), PID
(tested), MQTT validation (tested), benchmark and figure (runs), Docker stack
(compose-validated, not deployed), OpenSCAD (syntax reviewed, **not rendered** —
OpenSCAD is not installed on this machine).

Not yet done: detector training and the INT8 checkpoint, the 90-episode campaign,
the Hailo HEF compile (needs the Dataflow Compiler on an x86 host), and the
mobile app's typecheck (needs `npm install`).

## License

MIT. See `LICENSE`.
