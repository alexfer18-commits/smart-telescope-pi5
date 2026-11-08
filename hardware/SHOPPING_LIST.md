# Lista de compras — montura alt-azimut

Solo lo que falta: la Pi 5 (8 GB) y un NEMA 17 (17HS4401) ya están en casa.
Precios indicativos en USD, noviembre 2026.

## Crítico — sin esto no se enciende

| Componente | Especificación | Cant. | Precio | Link | Prioridad |
|---|---|---|---|---|---|
| Pi Camera Module 3 | standard, 12 MP, 1.55 µm, autofoco, CSI-2 | 1 | $25 | [Adafruit #5657](https://www.adafruit.com/product/5657) | **Alta** |
| NEMA 17 | 17HS4401: 42.3 mm, 1.8°/paso, 1.7 A/fase, 40 N·cm | 1 | $15 | [Amazon](https://www.amazon.com/s?k=NEMA+17+17HS4401+stepper+motor) | **Alta** |
| Fuente 12 V | 5 A mínimo, conector 5.5×2.1 mm, regulada | 1 | $15 | [Amazon](https://www.amazon.com/s?k=12V+5A+power+supply+5.5mm+barrel) | **Alta** |
| A4988 | módulo con disipador, Rs = 0.1 Ω, 1/16 | 2 | $10 | [Amazon](https://www.amazon.com/s?k=A4988+stepper+driver+with+heatsink) | **Alta** |
| Buck 12→5 V | 5 V / 5 A, salida ajustable o USB-C, ≥ 90 % | 1 | $8 | [Amazon](https://www.amazon.com/s?k=12V+to+5V+5A+buck+converter+USB-C) | **Alta** |

**Subtotal crítico: $73.** Es el mínimo para mover un eje y fotografiar el cielo.
Con esto la montura funciona en un eje y se puede validar el lazo de control.

## Estructura y óptica

| Componente | Especificación | Cant. | Precio | Link | Prioridad |
|---|---|---|---|---|---|
| Trupancha de aluminio | extrusión 2020, 4 × 500 mm + esquinas + T-nuts | 1 kit | $28 | [Amazon](https://www.amazon.com/s?k=2020+aluminum+extrusion+kit) | **Alta** |
| Tornillería | M2, M2.5, M3, M4, M5, M6 + tuercas nyloc | 1 kit | $12 | [Amazon](https://www.amazon.com/s?k=m3+m4+m5+stainless+socket+head+assortment) | **Alta** |
| Rodamientos 608ZZ | 8×22×7 mm, sellados | 4 | $6 | [Amazon](https://www.amazon.com/s?k=608ZZ+bearing+8x22x7) | **Alta** |
| Anillo de empuje | lazy susan Ø150 mm, acero | 1 | $10 | [Amazon](https://www.amazon.com/s?k=lazy+susan+bearing+150mm) | Media |
| Eje Ø8 | acero inoxidable, 8 mm × 300 mm | 1 | $8 | [Amazon](https://www.amazon.com/s?k=8mm+stainless+steel+rod+300mm) | Media |
| Insertos térmicos | M3 y M4, para PETG | 1 kit | $9 | [Amazon](https://www.amazon.com/s?k=heat+set+inserts+m3+m4+kit) | Media |
| Guidescope | 50 mm, 200 mm FL, con anillas | 1 | $55 | [Amazon](https://www.amazon.com/s?k=50mm+guidescope+200mm) | **Alta** |
| Trípode | cualquier EQ-1/GEM con plato de 1/4" o 3/8" | 1 | — | ya disponible | Media |

**Subtotal estructura: $128** (sin trípode).

## Medición y opcionales

| Componente | Especificación | Cant. | Precio | Link | Prioridad |
|---|---|---|---|---|---|
| INA219 | shunt I²C, 0x40, 26 V / 3.2 A | 1 | $5 | [Adafruit #904](https://www.adafruit.com/product/904) | Media |
| Condensador | 100 µF / 25 V electrolítico | 2 | $2 | [Amazon](https://www.amazon.com/s?k=100uF+25V+electrolytic+capacitor) | **Alta** |
| Correa GT2 | 2 poleas 20T + correa 200 mm (reducción 5:1) | 1 | $15 | [Amazon](https://www.amazon.com/s?k=GT2+timing+belt+pulley+20T+kit) | Baja |
| TMC2209 | driver silencioso, 1/256, UART | 2 | $16 | [Amazon](https://www.amazon.com/s?k=TMC2209+stepper+driver+UART) | Baja |
| Hailo-8L AI HAT+ | 13 TOPS, para E2 (requiere host x86) | 0–1 | $70 | [Amazon](https://www.amazon.com/s?k=Raspberry+Pi+AI+HAT+13+TOPS) | Baja |

El condensador de 100 µF no es opcional aunque esté en esta tabla: el A4988 sin
él oscila y se recalienta. Va en el pedido crítico si no tienes alguno suelto.

## Resumen

| Bloque | Coste |
|---|---|
| Crítico (Camera 3, NEMA 17, fuente, 2× A4988, buck) | $73 |
| Estructura y óptica (sin trípode) | $128 |
| Medición (INA219 + condensadores) | $7 |
| **Total para arrancar** | **$208** |
| Opcionales (correa 5:1 + 2× TMC2209) | +$31 |
| Opcional Hailo-8L (más host x86) | +$70 |

## Orden de compra sugerido

1. **Todo el bloque crítico de una vez ($73).** Pedirlo por separado duplica el
   envío y retrasa la primera prueba una semana por cada pieza que falte.
2. **Extrusión + tornillería + rodamientos ($46)** en el mismo pedido.
3. **Guidescope ($55)** cuando el eje de altitud ya gire: sin óptica no se puede
   medir el error de apuntado, pero sí se puede validar la mecánica.
4. **INA219 ($5)** antes de la primera sesión de medición real, no antes.
5. **Correa 5:1 y TMC2209 ($31)** solo si el apuntado medido no baja de
   10 arcmin. `docs/mechanical_analysis.md` §2.3 explica por qué la correa va
   antes que el driver.

**Critical path: Pi Camera 3 + segundo NEMA 17 + fuente 12V (sin esto no se puede energizar el sistema).**
