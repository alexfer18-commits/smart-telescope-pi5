"""Tests for stepper kinematics and the plate-solver error metric."""

from __future__ import annotations

import numpy as np
import pytest
from astropy.wcs import WCS

from motor_controller import (MICROSTEPS, STEPS_PER_REV, MockBackend,
                              MotorController, StepperAxis)
from plate_solver import crossval_error_arcmin, fit_wcs


def test_full_revolution_emits_the_right_number_of_steps() -> None:
    backend = MockBackend()
    axis = StepperAxis("az", backend)
    axis.move(360.0, speed_dps=100000.0)   # speed only affects sleep, not count
    pulses = [c for c in backend.calls if c[0] == "pulse"]
    assert len(pulses) == STEPS_PER_REV * MICROSTEPS


def test_direction_follows_sign() -> None:
    backend = MockBackend()
    axis = StepperAxis("alt", backend)
    axis.move(-1.0, speed_dps=100000.0)
    assert ("dir", "alt", False) in backend.calls
    assert axis.position_deg < 0


def test_stop_aborts_mid_move() -> None:
    axis: StepperAxis

    def stop_after_ten(count: int) -> None:
        if count >= 10:
            axis.stop()

    backend = MockBackend(on_pulse=stop_after_ten)
    axis = StepperAxis("az", backend)
    axis.move(90.0, speed_dps=100000.0)
    assert 0.0 < axis.position_deg < 90.0


def test_controller_disables_driver_on_stop() -> None:
    backend = MockBackend()
    controller = MotorController(backend)
    controller.stop()
    assert backend.enabled is False


def test_altitude_soft_limit_is_enforced() -> None:
    controller = MotorController(MockBackend())
    with pytest.raises(ValueError):
        controller.move_alt(120.0)
    controller.move_alt(90.0, speed_dps=100000.0)      # inside the range
    with pytest.raises(ValueError):
        controller.move_alt(10.0)                       # would end above 95


def test_azimuth_move_is_bounded_to_one_rotation() -> None:
    controller = MotorController(MockBackend())
    with pytest.raises(ValueError):
        controller.move_az(361.0)


def test_retained_and_malformed_commands_are_rejected() -> None:
    from mqtt_bridge import CommandRejected, parse_command

    assert parse_command(b'{"cmd": "stop"}') == {"cmd": "stop"}
    for payload in (b"", b"[]", b'{"cmd": "reboot"}',
                    b'{"cmd": "move", "axis": "x", "deg": 1}',
                    b'{"cmd": "move", "axis": "az", "deg": 999}',
                    b"x" * 600):
        with pytest.raises(CommandRejected):
            parse_command(payload)


def _synthetic_field(n: int = 40, seed: int = 3):
    wcs = WCS(naxis=2)
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    wcs.wcs.crval = [210.0, 54.0]
    wcs.wcs.crpix = [512.0, 512.0]
    wcs.wcs.cdelt = [-6.9 / 3600.0, 6.9 / 3600.0]
    rng = np.random.default_rng(seed)
    pixels = rng.uniform(100, 900, size=(n, 2))
    sky = wcs.all_pix2world(pixels, 0)
    return wcs, pixels, sky


def test_fit_wcs_recovers_the_projection() -> None:
    _, pixels, sky = _synthetic_field()
    fitted, rms_arcmin = fit_wcs(pixels, sky)
    assert rms_arcmin < 0.01
    ra, dec = fitted.all_pix2world([[512.0, 512.0]], 0)[0]
    assert abs(ra - 210.0) < 0.01 and abs(dec - 54.0) < 0.01


def test_crossval_error_is_small_on_clean_data() -> None:
    wcs, pixels, _ = _synthetic_field()
    assert crossval_error_arcmin(wcs, pixels) < 0.05


def test_crossval_error_grows_with_centroid_noise() -> None:
    wcs, pixels, _ = _synthetic_field()
    rng = np.random.default_rng(7)
    noisy = pixels + rng.normal(0.0, 1.0, pixels.shape)
    assert crossval_error_arcmin(wcs, noisy) > crossval_error_arcmin(wcs, pixels)


def test_fit_wcs_rejects_mismatched_inputs() -> None:
    _, pixels, sky = _synthetic_field(10)
    with pytest.raises(ValueError):
        fit_wcs(pixels, sky[:-1])
