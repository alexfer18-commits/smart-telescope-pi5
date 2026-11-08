# Bill of Materials

Prices are indicative retail, USD, November 2026. The design target is a
pointing instrument, not an imaging rig: the guidescope is deliberately modest.

**Status legend.** ✅ already owned · 🛒 still to buy. The running total at the
bottom counts **only the 🛒 rows**, because the ✅ rows are already paid for.

| # | Componente | Modelo | Cant. | Unit. (USD) | Subtotal | Estado | Proveedor sugerido |
|---|---|---|---|---|---|---|---|
| 1 | Compute | Raspberry Pi 5, 8 GB | 1 | 80 | 80 | ✅ En posesión | — |
| 2 | Steppers (azimut + altitud) | NEMA 17, 17HS4401 | 2 | 15 | 30 | ✅ En posesión (2 unidades) | — |
| 3 | Sensor | Raspberry Pi Camera Module 3 (standard) | 1 | 25 | 25 | 🛒 Por comprar | [Adafruit #5657](https://www.adafruit.com/product/5657) |
| 4 | Drivers | A4988 carrier with heatsink | 2 | 5 | 10 | 🛒 Por comprar | [Amazon](https://www.amazon.com/s?k=A4988+stepper+driver+with+heatsink) |
| 5 | PSU | 12 V / 5 A brick | 1 | 15 | 15 | 🛒 Por comprar | [Amazon](https://www.amazon.com/s?k=12V+5A+power+supply+5.5mm+barrel) |
| 6 | DC-DC | 12 V → 5 V / 5 A buck (Pi 5 rail) | 1 | 8 | 8 | 🛒 Por comprar | [Amazon](https://www.amazon.com/s?k=12V+to+5V+5A+buck+converter+USB-C) |
| 7 | Frame | Extrusión 2020: 4 × 500 mm + esquinas + T-nuts | 1 kit | 30 | 30 | 🛒 Por comprar | [Amazon](https://www.amazon.com/s?k=2020+aluminum+extrusion+kit) |
| 8 | Mechanics | 4 × 608ZZ, eje Ø8 × 300, tornillería M2–M6, insertos | 1 kit | 20 | 20 | 🛒 Por comprar | [Amazon](https://www.amazon.com/s?k=608ZZ+bearing+8x22x7) + 3D print |
| 9 | Optics | 50 mm guidescope, 200 mm FL | 1 | 55 | 55 | 🛒 Por comprar | [Amazon](https://www.amazon.com/s?k=50mm+guidescope+200mm) |
| 10 | Telemetry | INA219 shunt monitor | 1 | 5 | 5 | 🛒 Por comprar | [Adafruit #904](https://www.adafruit.com/product/904) |
| 11 | Accelerator (opcional) | Hailo-8L AI HAT+ (13 TOPS) | 0–1 | 70 | 0 / 70 | 🛒 Por comprar | [Amazon](https://www.amazon.com/s?k=Raspberry+Pi+AI+HAT+13+TOPS) |

## Total

| Escenario | Suma |
|---|---|
| En posesión (ya pagado) | **$110** (líneas 1–2: Pi 5 + 2 × NEMA 17) |
| **Por comprar, sin acelerador** | **$168** (líneas 3–10) |
| Por comprar, con Hailo-8L | $238 (líneas 3–11) |
| Coste total del instrumento, sin acelerador | $278 |
| Coste total del instrumento, con acelerador | $348 |

Los motores son la única línea que cambia respecto a la revisión anterior: allí
el segundo NEMA 17 estaba en "por comprar" a $15, así que pasa de 🛒 a ✅ y **la
compra baja $15, de $183 a $168**. El coste total del instrumento **no cambia**
($278), porque los dos motores siempre estuvieron en la suma; lo que cambia es
cuánto falta por pagar. Respecto al primer esbozo del BOM, que listaba los dos
motores como compra, el ahorro sí es de **$30**.

## Note on the two NEMA 17 in possession

> Both motors are 17HS4401 (1.8°/step, 1.7A/phase, 40 N·cm holding torque).
> Verify they are identical before assembly — mismatched motors would break the
> control loop symmetry.

A quick check, before they go on the mount: same label on both bodies, and the
four coil leads read ~2.4 Ω per phase pair with a multimeter (§3.2 of the
assembly guide). Two different 17HS4401 batches rarely differ, but a 40 N·cm and
a 45 N·cm unit on opposite axes show up as unequal settling times and a control
loop tuned for one axis that overshoots on the other.

The same note in Spanish, kept from the previous revision because it is what
fixes the driver current:

> El NEMA 17 en posesión (17HS4401) tiene 1.8°/step, 1.7 A por fase. Verificar
> que el driver A4988 soporte esta corriente (máx 2 A con disipador).

Verificado, y la respuesta corta es **no a 1.7 A, sí a 1.2 A**. El A4988 lleva
un puente en H con 1 A continuos por fase sin disipador y ~2 A con disipador y
aire forzado, así que 1.7 A está en el límite absoluto del chip, no en su punto
de trabajo. La solución no es comprar otro driver: es ajustar la corriente.
`docs/mechanical_analysis.md` calcula que el par necesario con el tubo
equilibrado es ~0.045 N·m contra los 0.28 N·m disponibles, así que **1.2 A
(Vref ≈ 0.96 V) da más de 6× de margen** y mantiene el driver frío.

Fórmula de Vref para el A4988 con Rs = 0.1 Ω (el valor habitual en los módulos
verdes de Pololu y clones):

```
I_fase = Vref / (8 × Rs)  →  Vref = I_fase × 0.8
Vref(1.20 A) = 0.96 V      Vref(1.70 A) = 1.36 V  ← no usar
```

Procedimiento y advertencias en `hardware/ASSEMBLY_GUIDE.md` §4. Los dos drivers
se ajustan **al mismo Vref**, o el eje de altitud se quedará corto antes que el
de azimut.

## Two corrections to the original sketch of this BOM

1. **The 12 V rail cannot feed the Pi.** A4988 needs 8–35 V for the steppers;
   the Pi 5 needs a clean 5 V / 5 A. A buck converter is not optional — it is
   the difference between a working instrument and a brown-out loop.
2. **The guidescope adds $55.** It is in the BOM because the plate scale
   (≈ 6.9 arcsec/px at 200 mm with 1.55 µm pixels, 2×2 binned) is what makes
   the pointing-error claim measurable. Without it the camera has a 66° field
   and no astrometric solution is stable enough to be a reference.

Costs exclude the host used for model training, any 3D-printing time, and the
x86 host needed to compile the Hailo HEF (`docs/architecture.md`).
Print files: `hardware/*.scad` (OpenSCAD 2021.01 or newer).
