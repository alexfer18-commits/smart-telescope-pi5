"""Stepper control for the alt-az mount: two NEMA 17 via A4988 carriers.

Two back ends share one interface:

* ``GpioBackend`` drives STEP/DIR/EN directly from the Pi's GPIO with gpiozero
  (lgpio pin factory). This is the default and needs no extra hardware.
* ``SerialBackend`` emits one line per step to a microcontroller, for when
  Linux scheduling jitter becomes the dominant pointing error. The firmware
  side is documented in firmware/README.md.

``MockBackend`` is what the tests use, and what the benchmark uses on a host
without GPIO.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Protocol

STEPS_PER_REV = 200
MICROSTEPS = 16
STEPS_PER_DEG = STEPS_PER_REV * MICROSTEPS / 360.0


@dataclass(frozen=True)
class AxisPins:
    step: int
    direction: int
    enable: int


AZ_PINS = AxisPins(step=17, direction=27, enable=22)
ALT_PINS = AxisPins(step=5, direction=6, enable=13)


class StepBackend(Protocol):
    def enable(self, on: bool) -> None: ...
    def set_direction(self, axis: str, forward: bool) -> None: ...
    def pulse(self, axis: str, high_s: float) -> None: ...
    def close(self) -> None: ...


class GpioBackend:
    """Direct GPIO pulse generation. A4988 needs >= 1 us on the STEP pin."""

    def __init__(self, az: AxisPins = AZ_PINS, alt: AxisPins = ALT_PINS) -> None:
        from gpiozero import DigitalOutputDevice
        from gpiozero.pins.lgpio import LGPIOFactory

        self._factory = LGPIOFactory()          # required on Pi 5
        self._pins = {"az": az, "alt": alt}
        self._dev = {
            axis: {
                "step": DigitalOutputDevice(p.step, pin_factory=self._factory),
                "dir": DigitalOutputDevice(p.direction, pin_factory=self._factory),
                "en": DigitalOutputDevice(p.enable, active_high=False,
                                          initial_value=False,
                                          pin_factory=self._factory),
            }
            for axis, p in self._pins.items()
        }

    def enable(self, on: bool) -> None:
        for dev in self._dev.values():
            dev["en"].value = not on        # A4988 EN is active low

    def set_direction(self, axis: str, forward: bool) -> None:
        self._dev[axis]["dir"].value = forward

    def pulse(self, axis: str, high_s: float) -> None:
        step = self._dev[axis]["step"]
        step.on()
        time.sleep(high_s)
        step.off()

    def close(self) -> None:
        for dev in self._dev.values():
            for d in dev.values():
                d.close()


class SerialBackend:
    """One ASCII line per step, e.g. ``AZ 1 20`` (axis, dir, high_us)."""

    def __init__(self, port: str = "/dev/ttyACM0", baudrate: int = 115200) -> None:
        import serial

        self._ser = serial.Serial(port, baudrate, timeout=1)

    def enable(self, on: bool) -> None:
        self._ser.write(f"EN {int(on)}\n".encode())

    def set_direction(self, axis: str, forward: bool) -> None:
        self._ser.write(f"DIR {axis.upper()} {int(forward)}\n".encode())

    def pulse(self, axis: str, high_s: float) -> None:
        self._ser.write(f"STEP {axis.upper()} {int(high_s * 1e6)}\n".encode())

    def close(self) -> None:
        self._ser.close()


@dataclass
class MockBackend:
    """Records calls; used by tests and by host-side dry runs."""

    calls: list[tuple] = field(default_factory=list)
    enabled: bool = False
    on_pulse: object | None = None       # callable(count) -> None, test hook

    def enable(self, on: bool) -> None:
        self.enabled = on
        self.calls.append(("enable", on))

    def set_direction(self, axis: str, forward: bool) -> None:
        self.calls.append(("dir", axis, forward))

    def pulse(self, axis: str, high_s: float) -> None:
        self.calls.append(("pulse", axis, high_s))
        if self.on_pulse is not None:
            self.on_pulse(len(self.calls))

    def close(self) -> None:
        self.calls.append(("close",))


class StepperAxis:
    """One axis: converts degrees to steps and keeps a step-count position."""

    def __init__(self, name: str, backend: StepBackend,
                 gear_ratio: float = 1.0, max_speed_dps: float = 6.0) -> None:
        self.name = name
        self.backend = backend
        self.gear_ratio = gear_ratio
        self.max_speed_dps = max_speed_dps
        self.position_deg = 0.0
        self._abort = False

    def move(self, delta_deg: float, speed_dps: float | None = None) -> None:
        """Move relative to the current position; blocks until done or aborted."""
        self._abort = False
        speed = min(speed_dps or self.max_speed_dps, self.max_speed_dps)
        steps = round(abs(delta_deg) * STEPS_PER_DEG * self.gear_ratio)
        if steps == 0:
            return
        self.backend.set_direction(self.name, delta_deg > 0)
        period = 1.0 / (speed * STEPS_PER_DEG * self.gear_ratio)
        high_s = min(period * 0.5, 10e-6)
        pulsed = 0
        for _ in range(steps):
            if self._abort:
                break
            self.backend.pulse(self.name, high_s)
            pulsed += 1
            time.sleep(max(period - high_s, 0.0))
        self.position_deg += (pulsed / (STEPS_PER_DEG * self.gear_ratio)) * (
            1 if delta_deg > 0 else -1)

    def stop(self) -> None:
        self._abort = True


class MotorController:
    """Two-axis facade used by the control loop.

    Soft limits live here, not in the driver: an A4988 will happily drive a
    mount into its own frame, and a shared MQTT credential is not a safety
    interlock. Altitude is clamped to the mechanically safe range; azimuth is
    wrapped, because a full rotation is legitimate.
    """

    ALT_MIN_DEG = -5.0
    ALT_MAX_DEG = 95.0

    def __init__(self, backend: StepBackend, az_gear: float = 1.0,
                 alt_gear: float = 1.0) -> None:
        self.backend = backend
        self.az = StepperAxis("az", backend, az_gear)
        self.alt = StepperAxis("alt", backend, alt_gear)
        self.backend.enable(True)

    def move_az(self, angle_deg: float, speed_dps: float | None = None) -> None:
        if abs(angle_deg) > 360.0:
            raise ValueError("azimuth move must be a single rotation or less")
        self.az.move(angle_deg, speed_dps)

    def move_alt(self, angle_deg: float, speed_dps: float | None = None) -> None:
        target = self.alt.position_deg + angle_deg
        if not self.ALT_MIN_DEG <= target <= self.ALT_MAX_DEG:
            raise ValueError(
                f"altitude target {target:.1f} deg outside "
                f"[{self.ALT_MIN_DEG}, {self.ALT_MAX_DEG}]")
        self.alt.move(angle_deg, speed_dps)

    def stop(self) -> None:
        self.az.stop()
        self.alt.stop()
        self.backend.enable(False)

    def close(self) -> None:
        self.backend.enable(False)
        self.backend.close()

    def __enter__(self) -> "MotorController":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
