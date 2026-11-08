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
                  telescope/state        telescope/cmd
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

## Why the camera is not the main telescope

The guidescope is a separate optical train at 200 mm. It gives a stable plate
scale and a wide field, so the solver sees dozens of stars even when the main
instrument is pointed at a blank patch of sky. Pointing and imaging are
decoupled on purpose: it is how the commercial mounts do it, and it means the
error metric is not contaminated by the target's own appearance.
