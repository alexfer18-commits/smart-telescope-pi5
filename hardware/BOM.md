# Bill of Materials

Prices are indicative retail, USD, November 2026. The design target is a
pointing instrument, not an imaging rig: the guidescope is deliberately modest.

| Component | Model | Qty | Unit (USD) | Supplier |
|---|---|---|---|---|
| Compute | Raspberry Pi 5, 8 GB | 1 | 80 | Adafruit / Amazon |
| Sensor | Raspberry Pi Camera Module 3 (standard) | 1 | 25 | Adafruit |
| Accelerator (optional) | Hailo-8L AI HAT+ (13 TOPS) | 0–1 | 70 | Hailo / Seeed |
| Steppers | NEMA 17, 17HS4401 | 2 | 15 | Amazon |
| Drivers | A4988 carrier with heatsink | 2 | 5 | Amazon |
| PSU | 12 V / 5 A brick | 1 | 15 | Amazon |
| DC-DC | 12 V → 5 V / 5 A buck (Pi 5 rail) | 1 | 8 | Amazon |
| Mechanics | Alt-az frame, belts, bearings, fasteners | 1 | 50 | 3D print + hardware |
| Optics | 50 mm guidescope, 200 mm FL | 1 | 55 | Amazon |
| Telemetry | INA219 shunt monitor | 1 | 5 | Amazon |

**Total without accelerator: ≈ $258. Total with Hailo-8L: ≈ $328.**

Two corrections to the original sketch of this BOM, both of which matter:

1. **The 12 V rail cannot feed the Pi.** A4988 needs 8–35 V for the steppers;
   the Pi 5 needs a clean 5 V / 5 A. A buck converter is not optional — it is
   the difference between a working instrument and a brown-out loop. It adds
   $8 and is included above.
2. **The guidescope adds $55.** It is in the BOM because the plate scale
   (≈ 6.9 arcsec/px at 200 mm with 1.55 µm pixels, 2×2 binned) is what makes
   the pointing-error claim measurable. Without it the camera has a 66° field
   and no astrometric solution is stable enough to be a reference.

Costs exclude the host used for model training and any 3D-printing time.
Print files: `hardware/*.scad` (OpenSCAD 2021.01 or newer).
