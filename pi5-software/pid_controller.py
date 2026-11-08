"""PID controller with conditional-integration anti-windup and filtered derivative.

Used on the slow pointing loop: the error is the angular residual in arcminutes,
the output is a rate command in degrees per second.
"""

from __future__ import annotations

from dataclasses import dataclass


def _clamp(value: float, limit: float) -> float:
    return max(-limit, min(limit, value))


@dataclass(frozen=True)
class PIDConfig:
    kp: float = 1.0
    ki: float = 0.0
    kd: float = 0.0
    output_limit: float = 1.0      # deg/s
    integral_limit: float = 2.0    # arcmin*s, bounds the wound-up term
    derivative_tau: float = 0.2    # s, first-order filter on the derivative


class PIDController:
    def __init__(self, config: PIDConfig | None = None) -> None:
        self.config = config or PIDConfig()
        self.reset()

    def reset(self) -> None:
        self._integral = 0.0
        self._derivative = 0.0
        self._previous: float | None = None

    def update(self, setpoint: float, measurement: float, dt: float) -> float:
        """Return the command for this step. `dt` is in seconds."""
        if dt <= 0.0:
            raise ValueError("dt must be positive")
        cfg = self.config
        error = setpoint - measurement

        raw_derivative = (0.0 if self._previous is None
                          else -(measurement - self._previous) / dt)
        alpha = dt / (cfg.derivative_tau + dt)
        self._derivative += alpha * (raw_derivative - self._derivative)
        self._previous = measurement

        candidate = cfg.kp * error + cfg.ki * (self._integral + error * dt) \
            + cfg.kd * self._derivative
        saturated = abs(candidate) > cfg.output_limit
        unwinding = error * (cfg.kp * error + cfg.ki * self._integral
                             + cfg.kd * self._derivative) < 0.0
        if not saturated or unwinding:
            self._integral = _clamp(self._integral + error * dt,
                                    cfg.integral_limit)

        command = cfg.kp * error + cfg.ki * self._integral + cfg.kd * self._derivative
        return _clamp(command, cfg.output_limit)

    @property
    def integral(self) -> float:
        return self._integral
