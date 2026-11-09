# Plan de trabajo de 6 meses — Alumna

**Proyecto:** smart-telescope-pi5 — Edge-AI on low-cost embedded hardware for autonomous celestial object pointing
**Inicio:** 1 de diciembre de 2026 · **Fin:** 31 de mayo de 2027
**Dedicación:** media jornada (20 h/semana), con acceso a cielo oscuro al menos dos noches al mes.

Este plan es el operativo de la alumna. La Sección V del paper agrupa los hitos de otra forma; para la ejecución manda esta tabla.

## Resumen por mes

| Mes | Fechas | Objetivo | Entregable | Hito de aceptación |
|:--|:--|:--|:--|:--|
| 1 | 1–31 dic 2026 | Compra de hardware y verificación de la Pi 5 | BOM con precios reales; Pi 5 con Raspberry Pi OS 64-bit; primera captura | La cámara entrega un frame 2304×1296 y los dos motores giran por GPIO |
| 2 | 1–31 ene 2027 | Montaje mecánico y verificación | Montura armada, contrapeso calibrado, holgura medida | Centro de masa a ±8 mm del eje de altitud; backlash < 0.5° |
| 3 | 1–28 feb 2027 | astrometry.net y primer plate solving | Solve ciego reproducible sobre 50 frames | ≥ 80 % de frames resueltos; tiempo de solve registrado |
| 4 | 1–31 mar 2027 | Cierre de lazo con PID | Lazo cerrado apuntando a 30 objetivos | Error de apuntado ≤ 10 arcmin RMS (objetivo ambicioso: ≤ 5) |
| 5 | 1–30 abr 2027 | Benchmark de las 3 arquitecturas | Dataset de 90 episodios + logs crudos + ANOVA | Las tres condiciones medidas; HEF compilado en host x86 |
| 6 | 1–31 may 2027 | Redacción del paper final | Manuscrito IEEE TIM + dataset público | PDF enviado y dataset con identificador persistente |

## Detalle y entregables

### Mes 1 — Compra y puesta en marcha de la Pi 5 (diciembre 2026)

- Cerrar la compra del material pendiente: Pi Camera Module 3, 2 × A4988, kit de extrusión 2020, fuente 12 V/5 A, guías 50 mm, INA219. El Hailo-8L es opcional y se decide en el mes 4.
- Grabar Raspberry Pi OS 64-bit (kernel 6.12) y fijar las versiones del manifiesto: picamera2 0.3.39, ONNX Runtime 1.31.1, astropy 8.0.2, gpiozero 2.0.1.post3.
- Probar la cámara con `create_still_configuration()` y `capture_array()`; guardar un frame de referencia.
- Probar los dos NEMA 17 con los A4988: pulso, dirección y micropaso; verificar que no se pierde paso a 5 °/s.
- **Entregable:** `docs/hardware_inventory.md` actualizado con precios reales, frame de primera luz y registro de la prueba de motores.
- **Hito:** la Pi 5 captura y mueve ambos ejes sin intervención manual.

### Mes 2 — Montaje mecánico y verificación (enero 2027)

- Armar la estructura de extrusión 2020 (base, torre, deck, horquilla) y las piezas impresas cortas.
- Montar el tubo, buscar el centro de masa real con el método del tarugo y añadir el contrapeso de ~150 g si el ocular lo desplaza.
- Medir la holgura y el backlash por aproximación direccional; ajustar la corriente de los A4988 a 1.2 A (Vref 0.96 V).
- Verificar la flecha del voladizo de 200 mm y que el tubo no cae con los motores desenergizados.
- **Entregable:** montura armada, fotos de montaje, registro de equilibrio y backlash.
- **Hito:** centro de masa a ±8 mm del eje de altitud y backlash < 0.5°.

### Mes 3 — astrometry.net y primer plate solving (febrero 2027)

- Instalar astrometry.net y los índices adecuados al campo (guías 200 mm + Camera Module 3).
- Resolver primero frames diurnos/brillantes y luego 50 frames nocturnos; registrar éxito, tiempo y residual.
- Implementar el solver geométrico base (detección de centroides + matching) como referencia del modelo aprendido.
- **Entregable:** script de solve reproducible, log de 50 frames y primer WCS guardado.
- **Hito:** ≥ 80 % de frames resueltos y tiempo de solve medido en la Pi 5.

### Mes 4 — Cierre de lazo con PID (marzo 2027)

- Implementar el lazo lento: captura → solve → residual → corrección; y el lazo rápido a 200 Hz.
- Sintonizar el PID por relay autotuning; limitar anti-windup y filtrar la derivada.
- Correr 30 episodios de apuntado con objetivos fijos y medir el error con un solve independiente.
- **Entregable:** lazo cerrado funcionando y log de 30 episodios con error por objetivo.
- **Hito:** error de apuntado ≤ 10 arcmin RMS; si no se alcanza, documentar la causa (resolución de paso, flexión o centroidado).

### Mes 5 — Benchmark de las 3 arquitecturas (abril 2027)

- Compilar el HEF del modelo en un host x86 (el Dataflow Compiler no corre en arm64); auditar la cobertura de operadores.
- Medir E1 (CPU), E2 (Hailo-8L) y E3 (AWS Lambda) con la misma óptica, mecánica y pesos.
- Correr los 90 episodios (3 × 30) con orden aleatorizado y baño térmico de 15 min por bloque.
- Registrar latencia p50/p95, energía por sesión con INA219 y coste por 1000 inferencias.
- **Entregable:** dataset de 90 episodios, logs crudos y tabla ANOVA/Tukey.
- **Hito:** las tres condiciones medidas; si E2 no se puede compilar, se reporta como *not measured*, nunca modelada.

### Mes 6 — Redacción del paper final (mayo 2027)

- Analizar los resultados y cerrar las figuras (torque, ANOVA, comparativa de latencia/energía/coste).
- Redactar el manuscrito para *IEEE Transactions on Instrumentation and Measurement*; el segundo paper (IoT Journal) queda como extensión.
- Publicar el dataset con identificador persistente y licencia permisiva; congelar el repositorio con tag `v3.0`.
- **Entregable:** `Propuesta_Final_v3.pdf` actualizado con resultados reales, manuscrito enviado y dataset publicado.
- **Hito:** PDF enviado y dataset accesible.

## Riesgos y contingencias

- **Clima:** solo dos noches al mes de cielo oscuro. Se aplica un colchón del 20 % a los meses 3 y 4; si se pierden dos noches seguidas, se prioriza el mes 5.
- **Hailo-8L:** depende de un host x86 para compilar el HEF. Si no aparece, E1 y E3 se miden y E2 se reporta como no medido.
- **Precisión:** si el error de paso de ±5.4 arcmin impide bajar de 10 arcmin, se añade la correa 5:1 (±1.08 arcmin) antes que el TMC2209; el TMC2209 mejora resolución y ruido, no el error de paso.
- **Presupuesto:** el material pendiente son \$168; con Hailo-8L, \$238. Cualquier desviación se anota en el BOM el mismo día.
