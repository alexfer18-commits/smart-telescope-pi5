# Lista de compras — montura alt-azimut

Solo lo que falta: la Pi 5 (8 GB) y **los dos** NEMA 17 (17HS4401) ya están en
casa. Precios indicativos en USD, noviembre 2026.

> Both NEMA 17 in possession → $15 less to buy than the previous revision of the
> BOM, and $30 less than the first sketch, which still listed two motors as
> purchases. Total hardware cost to complete the instrument: **$168 without
> Hailo** ($238 with it).

## Camino crítico — $70

Los tres artículos con más plazo de entrega y sin los cuales no hay instrumento.
Pídelos juntos y el mismo día: son los que marcan la fecha de la primera prueba.

| Componente | Especificación | Cant. | Precio | Link | Prioridad |
|---|---|---|---|---|---|
| Pi Camera Module 3 | standard, 12 MP, 1.55 µm, autofoco, CSI-2 | 1 | $25 | [Adafruit #5657](https://www.adafruit.com/product/5657) | **Alta** |
| Fuente 12 V | 5 A mínimo, conector 5.5×2.1 mm, regulada | 1 | $15 | [Amazon](https://www.amazon.com/s?k=12V+5A+power+supply+5.5mm+barrel) | **Alta** |
| Extrusión 2020 | 4 × 500 mm + esquinas + T-nuts | 1 kit | $30 | [Amazon](https://www.amazon.com/s?k=2020+aluminum+extrusion+kit) | **Alta** |

**Subtotal crítico: $70.** Con la cámara se mide, con la fuente se mueve y con la
extrusión se sostiene. Sin los tres, ninguna de las tres cosas.

Los dos A4988 y el buck **también son obligatorios** para energizar el sistema,
pero no son camino crítico: se encuentran en cualquier tienda local y llegan en
días, mientras que la cámara y el kit de extrusión vienen de fuera. Van en el
mismo carrito si el envío es gratis a partir de cierto monto.

## Electrónica de control

| Componente | Especificación | Cant. | Precio | Link | Prioridad |
|---|---|---|---|---|---|
| A4988 | módulo con disipador, Rs = 0.1 Ω, 1/16 | 2 | $10 | [Amazon](https://www.amazon.com/s?k=A4988+stepper+driver+with+heatsink) | **Alta** |
| Buck 12→5 V | 5 V / 5 A, salida ajustable o USB-C, ≥ 90 % | 1 | $8 | [Amazon](https://www.amazon.com/s?k=12V+to+5V+5A+buck+converter+USB-C) | **Alta** |

**Subtotal control: $18.** Un A4988 por eje; no se comparte driver entre azimut y
altitud.

## Mecánica y óptica

| Componente | Especificación | Cant. | Precio | Link | Prioridad |
|---|---|---|---|---|---|
| Tornillería | M2, M2.5, M3, M4, M5, M6 + tuercas nyloc | 1 kit | $12 | [Amazon](https://www.amazon.com/s?k=m3+m4+m5+stainless+socket+head+assortment) | **Alta** |
| Rodamientos 608ZZ | 8×22×7 mm, sellados | 4 | $6 | [Amazon](https://www.amazon.com/s?k=608ZZ+bearing+8x22x7) | **Alta** |
| Anillo de empuje | lazy susan Ø150 mm, acero | 1 | $10 | [Amazon](https://www.amazon.com/s?k=lazy+susan+bearing+150mm) | Media |
| Eje Ø8 | acero inoxidable, 8 mm × 300 mm | 1 | $8 | [Amazon](https://www.amazon.com/s?k=8mm+stainless+steel+rod+300mm) | Media |
| Insertos térmicos | M3 y M4, para PETG | 1 kit | $9 | [Amazon](https://www.amazon.com/s?k=heat+set+inserts+m3+m4+kit) | Media |
| Guidescope | 50 mm, 200 mm FL, con anillas | 1 | $55 | [Amazon](https://www.amazon.com/s?k=50mm+guidescope+200mm) | **Alta** |
| Trípode | cualquier EQ-1/GEM con plato de 1/4" o 3/8" | 1 | — | ya disponible | Media |

**Subtotal mecánica y óptica: $100** (sin trípode, sin la extrusión del camino
crítico).

## Medición y opcionales

| Componente | Especificación | Cant. | Precio | Link | Prioridad |
|---|---|---|---|---|---|
| INA219 | shunt I²C, 0x40, 26 V / 3.2 A | 1 | $5 | [Adafruit #904](https://www.adafruit.com/product/904) | Media |
| Condensador | 100 µF / 25 V electrolítico | 2 | $2 | [Amazon](https://www.amazon.com/s?k=100uF+25V+electrolytic+capacitor) | **Alta** |
| Correa GT2 | 2 poleas 20T + correa 200 mm (reducción 5:1) | 1 | $15 | [Amazon](https://www.amazon.com/s?k=GT2+timing+belt+pulley+20T+kit) | Baja |
| TMC2209 | driver silencioso, 1/256, UART | 2 | $16 | [Amazon](https://www.amazon.com/s?k=TMC2209+stepper+driver+UART) | Baja |
| Hailo-8L AI HAT+ | 13 TOPS, para E2 (requiere host x86) | 0–1 | $70 | [Amazon](https://www.amazon.com/s?k=Raspberry+Pi+AI+HAT+13+TOPS) | Baja |

El condensador de 100 µF no es opcional aunque esté en esta tabla: el A4988 sin
él oscila y se recalienta. Uno por driver; van en el pedido crítico si no tienes
alguno suelto.

## Resumen

| Bloque | Coste |
|---|---|
| Camino crítico (Camera 3, fuente, extrusión) | $70 |
| Electrónica de control (2× A4988, buck) | $18 |
| Mecánica y óptica (tornillería, rodamientos, anillo, eje, insertos, guidescope) | $100 |
| Medición (INA219 + 2 condensadores) | $7 |
| **Total del carrito** | **$195** |
| Opcionales (correa 5:1 + 2× TMC2209) | +$31 |
| Opcional Hailo-8L (más host x86) | +$70 |

**El carrito son $195; el instrumento son $168.** La diferencia ($27) es
consumible que no entra en el BOM por pieza: el kit de tornillería y el de
insertos térmicos se compran por surtido y sobran, y los dos condensadores son
recambio. El BOM presupuesta la mecánica en bloque a $50; esta lista la detalla
en $75, que es lo que cuesta de verdad pedirla. Para pagar, usa el carrito; para
citar el coste del instrumento, usa el BOM.

## Orden de pedido sugerido

Qué pedir, y en qué orden llega:

1. **Extrusión 2020 ($30).** Es el plazo más largo y lo que permite imprimir y
   montar la estructura. Mientras espera, se imprimen las piezas de
   `hardware/*.scad` y se prueba el ajuste de los rodamientos.
2. **Tornillería + rodamientos + eje + insertos + anillo ($45)**, en el mismo
   pedido: sin ellos la extrusión no se puede montar aunque llegue antes.
3. **Pi Camera Module 3 ($25).** Con la estructura armada y el eje de altitud
   girando, la cámara es lo que convierte el montaje en instrumento.
4. **Fuente 12 V + 2× A4988 + buck ($33).** Último bloque, cuando ya hay algo
   que mover: así no se acumulan drivers sin montura donde probarlos.
5. **Guidescope ($55)** cuando ambos ejes giren: sin óptica no se puede medir el
   error de apuntado, pero sí se puede validar la mecánica.
6. **INA219 ($5)** antes de la primera sesión de medición real, no antes.
7. **Correa 5:1 y TMC2209 ($31)** solo si el apuntado medido no baja de
   10 arcmin. `docs/mechanical_analysis.md` §2.3 explica por qué la correa va
   antes que el driver.
8. **Hailo-8L ($70)** solo cuando exista el host x86 para compilar el `.hef`;
   comprarlo antes no desbloquea la condición E2.

**Critical path: Pi Camera 3 + fuente 12V + aluminio 2020 = $70 (sin esto no se puede energizar el sistema).**
