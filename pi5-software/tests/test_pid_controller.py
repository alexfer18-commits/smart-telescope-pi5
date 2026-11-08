"""Tests for the PID controller: tracking, anti-windup, derivative filtering."""

from __future__ import annotations

import pytest

from pid_controller import PIDConfig, PIDController


def test_proportional_only_is_gain_times_error() -> None:
    pid = PIDController(PIDConfig(kp=0.5, ki=0.0, kd=0.0, output_limit=10.0))
    assert pid.update(setpoint=4.0, measurement=2.0, dt=0.1) == pytest.approx(1.0)


def test_output_is_clamped() -> None:
    pid = PIDController(PIDConfig(kp=100.0, output_limit=1.0))
    assert pid.update(setpoint=10.0, measurement=0.0, dt=0.1) == pytest.approx(1.0)


def test_integral_does_not_wind_up_while_saturated() -> None:
    cfg = PIDConfig(kp=1.0, ki=5.0, integral_limit=2.0, output_limit=0.5)
    pid = PIDController(cfg)
    for _ in range(200):
        pid.update(setpoint=100.0, measurement=0.0, dt=0.1)
    assert abs(pid.integral) <= cfg.integral_limit + 1e-9


def test_integral_removes_steady_state_error() -> None:
    """Closed loop against a first-order plant with a disturbance offset."""
    pid = PIDController(PIDConfig(kp=0.8, ki=0.6, kd=0.0, output_limit=5.0,
                                  integral_limit=10.0))
    measurement, dt, tau = 0.0, 0.05, 0.4
    for _ in range(2000):
        command = pid.update(setpoint=1.0, measurement=measurement, dt=dt)
        measurement += (0.9 * command - 0.2 - measurement) * dt / tau
    assert abs(1.0 - measurement) < 0.01


def test_derivative_does_not_kick_on_setpoint_change() -> None:
    pid = PIDController(PIDConfig(kp=0.0, ki=0.0, kd=1.0, output_limit=100.0))
    pid.update(setpoint=0.0, measurement=0.0, dt=0.1)
    assert pid.update(setpoint=50.0, measurement=0.0, dt=0.1) == pytest.approx(0.0)


def test_non_positive_dt_rejected() -> None:
    with pytest.raises(ValueError):
        PIDController().update(1.0, 0.0, 0.0)
