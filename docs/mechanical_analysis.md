# Análisis mecánico: ¿alcanza esta montura?

Todas las cifras de abajo son cálculos de diseño, no medidas. Cada una lleva su
fórmula y sus supuestos para que se puedan refutar.

**Parámetros de partida**

| Símbolo | Valor | De dónde |
|---|---|---|
| `m` | 2.5 kg | tubo 60 mm + cámara + saddle + abrazadera (rango 2–3 kg) |
| `g` | 9.81 m/s² | — |
| `r` | 0.20 m | brazo de palanca supuesto si el tubo NO está equilibrado |
| `τ_motor` | 0.40 N·m | par de retención de **cada** 17HS4401 (los dos son idénticos) a 1.7 A = 40 N·cm |
| `I_fase` | 1.20 A | ajuste recomendado del A4988 (Vref 0.96 V) |
| `L_tubo` | 0.50 m | guidescope de 200 mm de focal con tubo de 500 mm |

> Both axes use identical NEMA 17 motors. Azimuth axis has no gravity load
> (horizontal rotation); altitude axis requires counterweight to balance the
> tube.

Las dos premisas anteriores son las que justifican que un solo modelo de motor
sirva para los dos ejes, y explican por qué el presupuesto de par se gasta casi
entero en altitud. Los cálculos de abajo valen para cualquiera de las dos
unidades, porque son el mismo 17HS4401; si apareciera un motor distinto, el eje
que lo lleve hay que recalcularlo.

---

## 1. Par requerido — el resultado incómodo

### 1.1 Tubo desequilibrado (el caso que pide el enunciado)

```
τ_grav = m · g · r = 2.5 × 9.81 × 0.20 = 4.91 N·m = 491 N·cm
```

| Masa del tubo | τ gravitatorio | vs 0.40 N·m del motor | Déficit |
|---|---|---|---|
| 2.0 kg | 3.92 N·m | 0.40 N·m | **9.8×** |
| 2.5 kg | 4.91 N·m | 0.40 N·m | **12.3×** |
| 3.0 kg | 5.89 N·m | 0.40 N·m | **14.7×** |

**Conclusión: no hay margen. El motor no puede con el tubo desequilibrado, y no
es cuestión de ajustarlo — le falta un orden de magnitud.** Cualquier montura
directa con un brazo de 20 cm necesita una reducción de ~17:1 solo para
mantenerse, antes de poder moverse.

Además, a 1.2 A el par disponible no es el de catálogo:

```
τ(1.2 A) ≈ τ(1.7 A) × 1.2/1.7 = 0.40 × 0.706 = 0.282 N·m
```

El déficit real es **17.4×**, no 12.3×.

### 1.2 Tubo equilibrado (el caso que sí funciona)

Con el centro de masa sobre el eje de altitud, la gravedad no ejerce par: el
brazo es cero. Lo que queda es inercia y fricción.

**Inercia.** Tubo de 2.5 kg y 0.5 m, tratado como varilla alrededor de su centro:

```
I = m·L²/12 = 2.5 × 0.25 / 12 = 0.0521 kg·m²
```

Aceleración de slew de 20 °/s² = 0.349 rad/s²:

```
τ_inercia = I · α = 0.0521 × 0.349 = 0.018 N·m
```

**Fricción.** Rodamiento 608ZZ con 24.5 N de carga axial:

```
τ_rodamiento = μ · F · r_eje = 0.003 × 24.5 × 0.004 = 0.0003 N·m
```

Contacto del anillo de empuje, μ ≈ 0.05 a r = 20 mm:

```
τ_anillo = 0.05 × 24.5 × 0.020 = 0.025 N·m
```

**Total ≈ 0.045 N·m contra 0.282 N·m disponibles → margen 6.3×.**

### 1.3 Cuánto desequilibrio tolera cada opción

Despejando `r` de `τ = m·g·r` con el par disponible:

| Reducción | τ disponible | Desequilibrio tolerado | Con factor 1.5 |
|---|---|---|---|
| 1:1 (directa) | 0.282 N·m | 11.5 mm | **7.7 mm** |
| 5:1 (correa GT2) | 1.41 N·m | 57 mm | 38 mm |
| 10:1 | 2.82 N·m | 115 mm | 77 mm |
| 17.4:1 | 4.91 N·m | 200 mm | 133 mm |

**La conclusión de diseño: equilibrar el tubo cuesta una cinta y cinco minutos;
una reducción 17:1 cuesta dos poleas, una correa y una carcasa. Equilibra
primero.** El número accionable es **±8 mm**: si el centro de masa cae dentro de
8 mm del eje de altitud, la tracción directa sobra.

### 1.4 El eje de azimut no tiene este problema

El eje azimutal es **vertical**, y la gravedad es paralela a él: no genera par
alrededor del eje, por mucho que el conjunto esté descentrado. Su carga es
fricción del anillo de empuje más inercia del plato y la horquilla:

```
I_plato ≈ 0.5 · 150 mm · 8 mm PETG (≈ 0.4 kg) → I ≈ 1.1e-3 kg·m²
I_horquilla + tubo ≈ 0.0521 + 0.004 = 0.056 kg·m²
τ = 0.056 × 0.349 = 0.020 N·m
```

Margen > 10×. **El eje crítico es el de altitud, no el de azimut** — y por eso
el contrapeso, si hace falta, va en altitud.

---

## 2. Resolución angular — suficiente en el papel, justa en la práctica

### 2.1 La cuenta

```
paso completo      1.8°            = 108 arcmin
1/16 microstep     1.8/16 = 0.1125° = 6.75 arcmin/step
1/32 microstep     1.8/32 = 0.05625° = 3.375 arcmin
1/256 (TMC2209)    1.8/256 = 0.00703° = 0.42 arcmin
```

Objetivo: **10 arcmin**.

### 2.2 El veredicto

6.75 arcmin < 10 arcmin, así que **un microstep cabe dentro del objetivo, pero
consume el 67.5 % del presupuesto** y deja 3.25 arcmin para todo lo demás:
centroidado (2–4 arcmin con 200 mm de focal), holgura, alineación, flexión y
residual del modelo. En la práctica no alcanza: no porque el step sea grande,
sino porque no queda nada para el resto.

Y hay algo peor que la resolución: **la precisión del paso**. Un stepper tiene
un error de ángulo de paso de ±5 %, no acumulativo:

```
±5 % × 1.8° = ±0.09° = ±5.4 arcmin
```

El microstepping interpola **dentro** de un paso; no corrige dónde caen los
pasos completos. Con tracción directa, el motor solo aporta ±5.4 arcmin de error
sistemático contra un presupuesto de 10. **La resolución no es el límite; la
precisión del paso sí.**

### 2.3 Qué lo arregla de verdad

| Solución | Error de paso | Resolución | Coste |
|---|---|---|---|
| Directa 1/16 | ±5.4 arcmin | 6.75 arcmin | la actual |
| Correa 5:1 + 1/16 | ±1.08 arcmin | 1.35 arcmin | ~$15 |
| Directa con TMC2209 1/256 | ±5.4 arcmin | 0.42 arcmin | ~$8/driver |
| Correa 5:1 + TMC2209 | ±1.08 arcmin | 0.27 arcmin | ambos |

**Una reducción 5:1 divide el error de paso por cinco; el microstepping no lo
toca.** Por eso, si hay que elegir una sola mejora, es la correa.

> **If the 6.75 arcmin/step resolution is insufficient, consider a 5:1 belt
> reduction or a TMC2209 driver with 256 microsteps.** La correa baja el error
> de paso a ±1.08 arcmin y la resolución a 1.35 arcmin/step; el TMC2209 baja la
> resolución a 0.42 arcmin/step y, sobre todo, elimina el ruido audible y la
> resonancia del A4988 a velocidades bajas. Las dos juntas dan 0.27 arcmin/step
> con ±1.08 arcmin de exactitud, que es el margen que el objetivo de 10 arcmin
> necesita para no depender de que todo lo demás salga perfecto.

---

## 3. Centro de gravedad — dónde va el tubo

### 3.1 El tubo no está centrado en su punto medio

Un tubo de 500 mm con la cámara en la culata:

```
x_CG = Σ m_i x_i / Σ m_i
     = (2.35 kg × 250 mm + 0.15 kg × 500 mm) / 2.50 kg
     = (587.5 + 75) / 2.5 = 265 mm desde el objetivo
```

El centro de masa está **15 mm por detrás del punto medio geométrico**. Si
montas el saddle en el centro del tubo, ya arrastras 15 mm de desequilibrio —
más del doble del margen de 7.7 mm de la tracción directa.

### 3.2 Procedimiento

1. Pon el tubo sobre un tarugo redondo y encuentra su punto de equilibrio real.
   No lo calcules: mide. La cámara, el buscador y el ocular mueven ese punto
   decenas de milímetros.
2. Marca ese punto y colócalo sobre el eje de altitud.
3. Añade masa en la culata solo si el ocular lo desplaza hacia atrás; 150 g de
   contrapeso recuperan ~15 mm.
4. Verifica: con el tubo horizontal y los motores desenergizados, no debe caer
   en ninguno de los dos sentidos.

### 3.3 Centro de gravedad lateral

El conjunto Pi + bandeja + cámara pesa ~0.35 kg y va a un lado del tubo, a unos
45 mm del eje óptico:

```
desplazamiento lateral = 0.35 × 45 / (2.5 + 0.35) = 5.5 mm
```

5.5 mm de excentricidad lateral no genera par en altitud (está sobre el eje
óptico) pero **sí carga el rodamiento de azimut de forma asimétrica**. Es
tolerable; si se nota, gira la bandeja 180° y monta el Pi del lado opuesto al
ocular.

---

## 4. Rigidez estructural — aluminio sí, impresión 3D con cuidado

Viga en voladizo, `δ = F·L³/(3EI)`, con `F = 24.5 N`:

| Material | Sección | L | E | I | Flecha | Ángulo en la punta |
|---|---|---|---|---|---|---|
| Extrusión 2020 aluminio | 20×20×2 | 200 mm | 69 GPa | 7.87e-9 m⁴ | **0.12 mm** | **3.1 arcmin** |
| PETG impreso | 20×20 macizo | 200 mm | 2 GPa | 1.33e-8 m⁴ | 2.45 mm | **63 arcmin** |
| PETG impreso | 30×30 macizo | 50 mm | 2 GPa | 6.75e-8 m⁴ | 0.008 mm | 0.8 arcmin |
| Mejilla de horquilla PETG | 12×70, L=55 | 55 mm | 2 GPa | 3.43e-7 m⁴ | 0.002 mm | ~0.1 arcmin |

**Lo que dicen los números:**

- Una extrusión de aluminio de 200 mm se flexiona 0.12 mm, que son **3.1 arcmin
  de inclinación** — el 31 % del presupuesto de 10 arcmin, gastado en un solo
  elemento. Es aceptable pero no gratis: si añades un segundo voladizo, ya no
  cabe.
- Un soporte impreso de 200 mm es **inutilizable**: 63 arcmin, seis veces el
  objetivo. No porque el PETG sea malo, sino porque 2 GPa son 35 veces menos que
  el aluminio y la flecha va con `L³`.
- Impreso **corto y profundo** (30 mm de sección, 50 mm de vuelo) sí sirve:
  0.8 arcmin. Es la regla de diseño de las piezas de `hardware/*.scad`: las
  mejillas de la horquilla son cortas y de 70 mm de profundidad, y por eso
  aguantan.
- El **refuerzo en la base** de la escuadra del motor (`nema17_coupling.scad`,
  dos nervios triangulares) no es decorativo: sin él, la unión a 90° entre la
  placa del motor y el pie es una articulación, y el par de arranque la abre.

### 4.1 Torsión de la horquilla

Las dos mejillas trabajan a torsión cuando el tubo acelera en altitud. Con
separación de 144 mm y un par de 0.045 N·m, el giro relativo es del orden de
0.02° = 1.2 arcmin. Se mitiga con los pies atornillados al plato en dos puntos
por mejilla (2 × M6), que es lo que hace `alt_axis_assembly.scad`.

---

## 5. Velocidad y par a velocidad

El par de un stepper cae con la frecuencia de paso. A 5 °/s con 1/16:

```
f = 5 °/s ÷ 0.1125 °/paso = 44.4 micropasos/s = 2.78 pasos completos/s
```

2.78 pasos/s está en la zona plana de la curva par-velocidad: el motor entrega
esencialmente su par de retención. Un slew de 90° tarda 18 s, que es lento pero
correcto para un instrumento de apuntado. Con correa 5:1 la frecuencia sube a
13.9 pasos/s, todavía en la zona plana.

**No aumentes la velocidad sin volver a este cálculo**: a 50 °/s el motor está a
27.8 pasos/s y el par cae al 60–70 %, justo donde el margen de 6× empieza a
importar.

---

## 6. Resumen de veredictos

| Pregunta | Respuesta | Número |
|---|---|---|
| ¿El NEMA 17 mueve 2–3 kg con brazo de 20 cm? | **No** | déficit 12–17× |
| ¿Sirve el mismo motor para los dos ejes? | Sí: azimut sin gravedad, altitud equilibrada | 6.2× en cada uno |
| ¿Y con el tubo equilibrado? | **Sí, con margen** | 6.3× |
| ¿Cuánto desequilibrio tolera en directa? | Poco | **±8 mm** |
| ¿6.75 arcmin/step alcanza para 10 arcmin? | Marginal, no en la práctica | 67.5 % del presupuesto |
| ¿Qué lo arregla? | Correa 5:1 antes que microstepping | ±1.08 arcmin de exactitud |
| ¿Extrusión de aluminio aguanta? | Sí, con 3.1 arcmin de coste | 0.12 mm a 200 mm |
| ¿Impresión 3D aguanta? | Solo corta y profunda | 0.8 arcmin a 50 mm, 63 arcmin a 200 mm |
| ¿Dónde va el CG? | 265 mm desde el objetivo | 15 mm detrás del centro |

**Conclusión para el montaje:** equilibrar el tubo es obligatorio y es gratis;
la correa 5:1 es la siguiente compra si el apuntado no baja de 10 arcmin; y la
estructura que sostiene el tubo debe ser de aluminio, no impresa, en cualquier
voladizo de más de 100 mm.
