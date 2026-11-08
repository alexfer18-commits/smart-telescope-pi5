# Measurement plan (real hardware)

This is the bridge between the synthetic numbers in `data/benchmark_results.json`
and the numbers the paper must report. Nothing in this file is optional if the
result is going to be published.

## 1. Hardware checklist

| Item | Spec | Check before starting |
|---|---|---|
| Compute | Raspberry Pi 5, 8 GB | `cat /proc/device-tree/model` |
| Storage | ≥ 32 GB A2 microSD or NVMe | model load time is dominated by this |
| Sensor | Camera Module 3 (standard) | `rpicam-hello --list-cameras` shows it |
| Accelerator (optional) | Hailo-8L AI HAT+ 13 TOPS | `hailo device info` sees it |
| Motors | 2 × NEMA 17 17HS4401 | holding torque with `EN` low |
| Drivers | 2 × A4988, heatsinked | Vref = 0.64 V set with a meter |
| Supply | 12 V / 5 A brick | measured under load, not label |
| DC-DC | 12 V → 5 V / 5 A buck | 5.0–5.1 V at the Pi's GPIO header |
| Monitor | INA219 on the 5 V rail | `i2cdetect -y 1` shows 0x40 |
| Optics | 50 mm guidescope, 200 mm FL | plate scale ≈ 6.9 arcsec/px |

Log the serial numbers and the measured Vref. A result produced on a different
driver current is not comparable with one produced on this one.

## 2. Install the runtimes on the Pi 5

Raspberry Pi OS Bookworm, 64-bit, Python 3.11.

```bash
sudo apt update
sudo apt install -y python3-picamera2 python3-venv i2c-tools astrometry.net
sudo raspi-config nonint do_i2c 0            # enable I2C for the INA219
python3 -m venv ~/telescope-venv && . ~/telescope-venv/bin/activate
pip install --upgrade pip

# ONNX Runtime: aarch64 wheels ship on PyPI from 1.16 onward.
pip install onnxruntime

# TFLite: the classic runtime, if a wheel exists for this Python version.
pip install tflite-runtime || echo "no tflite-runtime wheel; use LiteRT below"

# LiteRT is the current name of TFLite. Use it when tflite-runtime has no wheel.
pip install ai-edge-litert

# Everything else the software needs.
pip install astropy opencv-python-headless paho-mqtt gpiozero fastapi uvicorn \
            pyserial numpy scipy matplotlib ina219
```

Verify:

```bash
python -c "import onnxruntime; print('onnxruntime', onnxruntime.__version__)"
python -c "import tflite_runtime.interpreter as t; print('tflite ok')" \
  || python -c "from ai_edge_litert.interpreter import Interpreter; print('litert ok')"
python -c "from ina219 import INA219; i=INA219(0.1); i.configure(); print(i.power(),'mW')"
hailo device info          # only if the HAT is fitted
```

If `tflite-runtime` has no wheel for your Python, do **not** pin an old Python
to get one. Use LiteRT, or export the model to ONNX only — the comparison does
not require the TFLite backend.

## 3. Run the measurements

```bash
# CPU, ONNX, with energy
python benchmarks/run_real_measurements.py \
    --model ml-model/mnv3_int8.onnx --episodes 300 --ina219

# CPU, TFLite (if available)
python benchmarks/run_real_measurements.py \
    --model ml-model/mnv3_int8.tflite --episodes 300 --ina219

# Accelerator — only after the HEF exists (section 5)
python benchmarks/run_real_measurements.py \
    --model ml-model/mnv3.hef --episodes 300 --ina219
```

`run_real_measurements.py` writes `data/real_measurements.json` with
`"source": "measured"`, the model's SHA-256, the host, and — when the shunt is
present — mean watts and Wh per 1000 inferences. If the INA219 is absent it
writes `null`, never an estimate.

Three runs per substrate, spaced by a 15-minute thermal soak. Report the run
with the median p50; keep all three in `data/` so the variance is visible.

## 4. Acceptance criteria

| Metric | Threshold | If it fails |
|---|---|---|
| p95 latency, E1 | < 2000 ms | model too large for the Pi; shrink the input resolution |
| p95 latency, E2 | < 200 ms | operator fallback to CPU; audit the HEF coverage |
| Pointing error | < 5 arcmin RMS | optics or centroiding, not the substrate |
| Energy stability | < 10 % between runs | thermal drift; re-soak and repeat |
| INA219 present | required for energy claims | otherwise report latency only |

## 5. Compile the HEF on an x86 host

The Pi cannot do this. See `docs/architecture.md`, "Hailo-8L Compilation
Constraint".

**Host requirements:** Ubuntu 20.04 or 22.04, x86_64, Python 3.8–3.10, 16 GB
RAM, 20 GB free. No GPU required. The Dataflow Compiler is a licensed download
from the Hailo Developer Zone (developer.hailo.ai); it is not on PyPI.

```bash
# 1. on the x86 host
python3 -m venv ~/hailo-dfc && . ~/hailo-dfc/bin/activate
pip install hailo_dataflow_compiler-<version>-py3-none-linux_x86_64.whl
hailo --version                       # DFC 3.x

# 2. stage the model and calibration frames (both produced on the Pi or a GPU host)
scp ml-model/mnv3_int8.onnx   user@x86host:~/hef/
scp -r data/calibration_frames user@x86host:~/hef/

# 3. parse → optimize → compile
hailo parser onnx ~/hef/mnv3_int8.onnx --hw-arch hailo8l -y
hailo optimize ~/hef/mnv3_int8.har --hw-arch hailo8l -y
hailo compile  ~/hef/mnv3_int8.har --hw-arch hailo8l -y

# 4. copy back and run
scp ~/hef/mnv3_int8.hef pi@telescope.local:~/smart-telescope-pi5/ml-model/mnv3.hef
```

**Check the coverage report before trusting the latency.** `hailo optimize`
prints which layers ran on the NPU and which fell back to the host. Any fallback
in the backbone invalidates the comparison — a graph that is 90 % accelerated is
not 10× faster, it is 10× faster minus a CPU round trip per inference.

Record in the lab notebook: DFC version, HailoRT version on the Pi, the coverage
percentage, and the compile command line. Two HEFs compiled with different DFC
versions are different artifacts.

## 6. What goes into the paper

- Latency: p50 and p95 from `data/real_measurements.json`, three runs each.
- Energy: Wh per 1000 inferences **and** per session (50 solves), measured.
- Cost: recomputed with the measured latency, not the modelled one.
- Dataset: frames, timings, and logs, released with a persistent identifier.
- Provenance: every table states `measured` or `modelled`. No mixing in one row.
