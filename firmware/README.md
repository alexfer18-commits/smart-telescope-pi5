# Firmware

There are two ways to turn a step command into a pulse on the A4988, and this
folder covers the second one.

**Default: no firmware.** `pi5-software/motor_controller.py` drives STEP/DIR/EN
directly from the Pi's GPIO through gpiozero's lgpio backend. For a 200 mm
guidescope at 6.9 arcsec/px this is sufficient: one step is 0.45 arcsec at
1:1 and the loop closes every few seconds, so Linux scheduling jitter of a few
hundred microseconds costs well under a pixel.

**Optional: `stepper_bridge.ino`.** When jitter does matter — long focal
length, high microstepping, or a mount with a large reduction ratio — move the
pulse train onto a microcontroller and let the Pi send one line per step over
USB serial. That is the protocol `SerialBackend` in `motor_controller.py`
speaks. Flash the sketch to any AVR/ESP32 board, wire the drivers to it, and
construct `MotorController(SerialBackend("/dev/ttyACM0"))`.

## A4988 setup, because getting this wrong destroys motors

| Setting | Value | Note |
|---|---|---|
| Microstepping | 1/16 | MS1, MS2, MS3 all high; matches `MICROSTEPS = 16` |
| Current limit | 0.8 A | Vref = I × 8 × Rsense; with 0.1 Ω sense, Vref = 0.64 V |
| Decay mode | mixed | leave floating |
| Supply | 12 V | **never** feed the Pi's 5 V rail into VMOT |
| Step pulse | ≥ 1 µs | the driver latches on the rising edge |
| Enable | active low | `EN` pulled high disables the coils (holding torque lost) |

The driver heatsink is not decorative. At 0.8 A continuous the carrier reaches
~70 °C; without airflow the thermal shutdown trips mid-slew and the mount
silently loses position. Mount the drivers where air moves, or add a 40 mm fan.

## Protocol

```
EN 1                 enable both drivers
EN 0                 disable (coils off, mount free to move by hand)
DIR AZ 1             azimuth forward
DIR ALT 0            altitude reverse
STEP AZ 20           one pulse, 20 µs high
```

One line per step is deliberate: it is slow enough for a 115200 baud link
(~11 ksteps/s ceiling) and simple enough that a dropped byte is a lost step the
watchdog can detect, rather than a corrupted multi-byte frame.
