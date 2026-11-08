# Architecture

```
                        ┌──────────────────────────────┐
                        │  phone (Expo / React Native) │
                        │  wss 9001 · https 8443       │
                        └──────────────┬───────────────┘
                                       │ TLS
                        ┌──────────────▼───────────────┐
                        │ mosquitto (Docker, arm64)    │
                        │ 8883 mqtt · 9001 ws · ACL    │
                        └──────┬───────────────┬───────┘
                               │               │
                telescope/status/state    telescope/commands/cmd
                               │               │
        ┌──────────────────────▼───────────────▼─────────────────────┐
        │ Raspberry Pi 5, 8 GB — Raspberry Pi OS 64-bit              │
        │                                                            │
        │  ┌────────────┐   ┌──────────────┐   ┌─────────────────┐   │
        │  │ Picamera2  │──▶│ plate_solver │──▶│ PID / MPC       │   │
        │  │ 2304×1296  │   │ detector +   │   │ residual → rate │   │
        │  └────────────┘   │ WCS + error  │   └────────┬────────┘   │
        │                   └──────┬───────┘            │            │
        │                          │ INT8 graph         │ steps      │
        │              ┌───────────┴──────────┐          │            │
        │              │ ONNX Runtime (CPU)   │          │            │
        │              │ HailoRT (Hailo-8L)   │          │            │
        │              └───────────┬──────────┘          │            │
        │                          │ optional offload   │            │
        └──────────────────────────┼─────────────────────┼────────────┘
                                   │                     │
                          ┌────────▼────────┐   ┌────────▼─────────┐
                          │ AWS Lambda      │   │ 2× A4988         │
                          │ (E3 only)       │   │ 2× NEMA 17       │
                          └─────────────────┘   └──────────────────┘
```

## Loops

Two rates, deliberately separate.

**Fast loop (200 Hz, on the Pi or the MCU).** Reads the step counter, emits
pulses, applies backlash compensation by always approaching from the same
direction. No inference, no network, no allocation. This loop must never block.

**Slow loop (per exposure, ~0.1 Hz).** Capture → detect → solve → residual →
controller. This is where the inference substrate matters, and it is the only
loop the benchmark instruments.

Keeping them separate is what makes the cloud condition honest: a 400 ms solve
cannot destabilise a loop that runs every ten seconds, and that is precisely the
claim the experiment tests.

## Data flow per episode

1. `motor_controller` slews to the model's predicted position.
2. `picamera2` captures 2 s; the frame stays in memory.
3. `plate_solver.detect_stars` → centroids (learned detector or OpenCV fallback).
4. Blind match: local `solve-field`, or the ONNX/Hailo stage if the model is
   deployed. Returns `SolveResult` with RA, Dec, `error_arcmin`, `latency_ms`.
5. `pid_controller` converts the residual into a rate command.
6. `mqtt_bridge` publishes state at 1 Hz, retained, QoS 1.
7. `dashboard` keeps the last 120 solves for the plot; the experiment writes
   one JSON episode to `experiments/`.

## Failure modes, and what the design does about each

| Failure | Behaviour | Mitigation in this repo |
|---|---|---|
| Network down (E3) | solve fails | CPU path is the default; cloud is never a dependency |
| Model missing | detector falls back to OpenCV | `DEFAULT_MODEL` existence check |
| Accelerator absent | HailoRT import fails | `--runtime auto` falls back to ONNX/TFLite |
| `solve-field` absent | `SolverUnavailable` | explicit error, not a silent bad solve |
| Star field too sparse | < 3 centroids | explicit `SolverUnavailable` |
| Broker unreachable | publish error logged | control loop unaffected |
| Step loss | position drifts | serial protocol ACKs each step (MCU path) |
| Mount limit exceeded | move refused | soft limits in `MotorController` |

## Hailo-8L Compilation Constraint

The Hailo-8L does not run ONNX. It runs a **HEF** (Hailo Executable Format), a
pre-compiled binary produced by the **Hailo Dataflow Compiler (DFC)**, and the
DFC does not run on the Pi.

This is an architectural constraint, not a packaging inconvenience:

| Stage | Where it runs | Why |
|---|---|---|
| Train the detector | GPU host | PyTorch/TensorFlow |
| Export and quantize to INT8 ONNX | any x86 or arm64 host | ONNX Runtime |
| Parse, optimize, compile to `.hef` | **x86_64 Linux only** | DFC is distributed as x86 binaries; no arm64 build exists |
| Execute the `.hef` | Raspberry Pi 5 + Hailo-8L | HailoRT runtime only |

So the Pi is an *inference* target, never a compiler target. `HailoRT` on the Pi
loads a `.hef` and schedules it; if you hand it an ONNX file it has nothing to
do with it. Consequences for the study:

- **Condition E2 cannot be built on the instrument alone.** It needs an x86
  machine in the loop at least once, before the experimental campaign starts.
- **The compile is a one-time cost per model variant**, not per episode. Two
  backbones means two compiles, not ninety.
- **Operator coverage must be checked before the campaign.** Any layer the DFC
  cannot place on the NPU falls back to the Pi's CPU, and a partially offloaded
  graph silently destroys the latency comparison. `benchmarks/compare_inference.py`
  records `hailo_available` in its JSON for exactly this reason.

Three ways to satisfy the constraint, in ascending order of cost:

1. **x86 VM on an Apple Silicon or ARM laptop** — Parallels, UTM, or VMware
   Fusion running Ubuntu 22.04 x86_64. Sufficient: the DFC needs CPU and RAM,
   not a GPU. Slowest compile of the three, and the least reproducible when the
   VM is rebuilt, but it costs nothing new.
2. **Remote x86 server** — a university lab machine or a cloud instance, reached
   over SSH. Best throughput and the easiest to document for reproducibility;
   requires a data-transfer agreement for the model and the calibration frames.
3. **Dedicated x86 workstation** — no dependency on anyone else's hardware.
   Justified if the Hailo condition becomes a permanent part of the
   instrument rather than a one-off experiment.

Until one of these exists, E2 is documented but not measured. The benchmark
reports `hailo_available: false` rather than inventing a number, and the
proposal states the constraint explicitly rather than discovering it in month 4.

## Why the camera is not the main telescope

The guidescope is a separate optical train at 200 mm. It gives a stable plate
scale and a wide field, so the solver sees dozens of stars even when the main
instrument is pointed at a blank patch of sky. Pointing and imaging are
decoupled on purpose: it is how the commercial mounts do it, and it means the
error metric is not contaminated by the target's own appearance.
