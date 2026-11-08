# Protocolo experimental v3

Diseño factorial 3 × 3. Una condición es una celda; un episodio es un
apuntado completo. Este documento sustituye a `experimental_protocol_v2.md`
para la fase 4; el v2 sigue siendo válido para el diseño de 90 episodios de una
sola arquitectura.

> **Estado actual: todos los números de este protocolo son sintéticos.** Ver §5.
> El diseño está listo; los datos, no. `experiments/measurement_plan.md` describe
> cómo obtener los reales.

---

## 1. Variables

### 1.1 Factor A — arquitectura de inferencia (3 niveles)

| Nivel | Etiqueta | Sustrato | Qué resuelve |
|---|---|---|---|
| E1 | `cpu_onnx` | ONNX Runtime en la CPU del Pi 5 | línea base, sin acelerador |
| E2 | `hailo8l` | Hailo-8L por HailoRT, sobre un `.hef` | acelerador NPU |
| E3 | `cloud_lambda` | AWS Lambda por HTTPS | cómputo externo |

**Nota obligatoria sobre E2:** *Hailo condition marked as not_measured until x86
host is available.* El Hailo-8L ejecuta un HEF producido por el Dataflow
Compiler, que solo existe para x86_64 Linux. Sin un host x86 no hay `.hef`, y sin
`.hef` no hay condición E2. Hasta que exista, las 90 filas de E2 llevan
`measurement_status = "not_measured"` y **no se citan como resultado**.

### 1.2 Factor B — iluminación del cielo (3 niveles)

| Nivel | Etiqueta | Brillo del cielo | Luna | Estrellas detectables (típ.) |
|---|---|---|---|---|
| L1 | `dark` | 21.5 mag/arcsec² | ninguna | 40–120 |
| L2 | `suburban` | 18.5 mag/arcsec² | cuarto creciente | 15–40 |
| L3 | `moonlight` | 16.5 mag/arcsec² | llena, a > 40° | 6–15 |

Se mide el brillo con un SQM en el cenit al inicio y al final de cada bloque. Si
cambia más de 0.5 mag/arcsec², el bloque se repite: la iluminación es un factor,
no una covariable que se pueda dejar derivar.

### 1.3 Unidad experimental

**Un episodio** = un apuntado completo a un objeto, con corrección y
verificación. 30 repeticiones por celda × 9 celdas = **270 episodios**.

| | L1 dark | L2 suburban | L3 moonlight | Total |
|---|---|---|---|---|
| E1 cpu_onnx | 30 | 30 | 30 | 90 |
| E2 hailo8l | 30 | 30 | 30 | 90 |
| E3 cloud_lambda | 30 | 30 | 30 | 90 |
| **Total** | **90** | **90** | **90** | **270** |

Los 30 objetos se sortean sin reemplazo de un catálogo de 60 y se reutilizan en
las 9 celdas: el objeto es un bloque, no una fuente de variación.

### 1.4 Variables de respuesta y covariables

| Variable | Unidad | Tipo |
|---|---|---|
| `error_arcmin` | arcmin | respuesta primaria |
| `latency_ms` | ms | respuesta secundaria |
| `n_stars` | — | covariable |
| `fwhm_arcsec` | arcsec | covariable (seeing) |
| `ambient_c` | °C | covariable |
| `energy_wh` | Wh | respuesta secundaria (solo con INA219) |

---

## 2. Tópicos MQTT

La fase 4 usa los tópicos del broker con ACL (ver `docker/mosquitto/acl_file`).
Los nombres cambiaron respecto a la v2; cualquier cliente antiguo hay que
reapuntarlo.

| Tópico | Publica | Lee | Contenido |
|---|---|---|---|
| `telescope/status/state` | `pi` | `phone`, harness | estado del montaje, 1 Hz, retenido |
| `telescope/commands/cmd` | `phone` | `pi` | orden validada |
| `telescope/pi/rejected` | `pi` | `phone`, harness | por qué se rechazó una orden |

Payload de estado (mínimo que consume el harness):

```json
{"ts": "2026-11-08T21:04:11Z", "ra_deg": 210.4, "dec_deg": 54.1,
 "alt_deg": 47.2, "az_deg": 131.8, "tracking": true, "error_arcmin": 4.7}
```

Payload de comando:

```json
{"cmd": "move", "axis": "az", "deg": 1.5}
```

Reglas que el harness **no** puede relajar:

- El harness se suscribe a `telescope/status/#`; nunca publica en
  `telescope/commands/#`, porque el ACL de `pi` no se lo permite y un
  experimento no debe poder mover el instrumento por su cuenta.
- Un episodio empieza cuando se publica el comando y termina cuando llega el
  estado con `tracking: true` y el error de verificación. Si no llega en 30 s,
  el episodio se marca `timeout` y **se conserva**.
- Los mensajes son ≤ 512 bytes y sin retención en el camino de comandos: un
  comando retenido se reproduce al reconectar y mueve el tubo solo.

---

## 3. Procedimiento por episodio

1. **Park** y comprobar límites: altitud en `[-5°, 95°]`, azimut en una vuelta.
2. **Slew** al objeto con el modelo de la montura. Máximo 5 °/s.
3. **Asentar** 3 s (el tubo oscila; medir antes de asentar mide la oscilación).
4. **Capturar** 2 s a ganancia 0 y guardar el frame crudo.
5. **Resolver** con el sustrato bajo prueba; registrar `latency_ms`, `n_stars`,
   `error_arcmin`, `source`.
6. **Corregir** el residual con el PID.
7. **Asentar** 3 s.
8. **Verificar** con el solver de verificación — **nunca** el mismo del paso 5.
9. Registrar la separación angular entre posición comandada y verificada.
10. Integrar la potencia del INA219 sobre el episodio (solo si está conectado).

### 3.1 Orden y aleatorización

- Un bloque = una noche. Antes de cada bloque, **15 min de reposo térmico**.
- Dentro del bloque se aleatoriza el orden de las 9 celdas.
- El orden de las arquitecturas no se aleatoriza *entre* noches sin registrar la
  noche: la deriva térmica y la transparencia se llevan en `night_id`.
- Nunca dos celdas de iluminación distinta en la misma hora sin volver a medir
  el SQM.

---

## 4. Registro

`experiments/episode_schema.json` es el contrato. Un JSON por episodio, más un
índice de sesión. Los ficheros son **append-only**: un reintento recibe un
`episode_id` nuevo, nunca una edición.

### 4.1 Esquema de la tabla (CSV y Excel)

| Columna | Tipo | Valores |
|---|---|---|
| `episode_id` | str | `E1-L2-014` |
| `night_id` | str | `2026-11-14` |
| `architecture` | enum | `cpu_onnx` · `hailo8l` · `cloud_lambda` |
| `illumination` | enum | `dark` · `suburban` · `moonlight` |
| `repetition` | int | 1–30 |
| `object_id` | str | `M31`, `M42`, … |
| `latency_ms` | float | — |
| `error_arcmin` | float | respuesta primaria |
| `n_stars` | int | — |
| `fwhm_arcsec` | float | — |
| `ambient_c` | float | — |
| `energy_wh` | float \| null | null sin INA219 |
| **`source`** | **enum** | **`measured` · `modelled` · `synthetic`** |
| `measurement_status` | enum | `measured` · `not_measured` |

**La columna `source` es obligatoria y no admite nulos.** Es la primera columna
que se valida al cargar el CSV; una fila sin `source` aborta el análisis.

---

## 5. Data Provenance

### 5.1 Qué es qué

| Valor de `source` | Significado | Puede ir al paper |
|---|---|---|
| `measured` | producido por un instrumento físico, con hash del modelo y host | sí, como resultado |
| `modelled` | derivado de un modelo analítico declarado (p. ej. `LATENCY_MODEL_MS`) | sí, etiquetado como modelo, nunca como medición |
| `synthetic` | generado por un simulador con parámetros elegidos a mano para ejercitar el pipeline | **no** |

### 5.2 Lo que hay hoy

`data/simulated_results_v3.csv` contiene **270 filas, todas con
`source = "synthetic"`**. Ninguna es una medición. Las 90 filas de E2 llevan
además `measurement_status = "not_measured"`, porque ni siquiera el simulador
puede pretender que esa condición existe: no hay `.hef`.

El análisis de `figures/anova_results_v3.pdf` es un **ensayo del pipeline
estadístico**, no un resultado sobre el instrumento. Su JSON lleva
`"data_source": "synthetic"` en la raíz precisamente para que no se pueda citar
fuera de contexto.

### 5.3 Lo que las reemplaza

`benchmarks/run_real_measurements.py` para latencia y energía, y el harness de
episodios para el error de apuntado. Ambos escriben `source = "measured"` y
**no tienen fallback sintético**: si falta un runtime, un modelo o el shunt,
la fila se marca `null` o se omite, nunca se estima.

### 5.4 La regla del manuscrito

- Toda tabla y toda figura declara su procedencia en el pie, no en una nota al
  final.
- Una fila no mezcla `measured` con `modelled`.
- Antes del envío, la tabla sintética se sustituye **entera**. Si E2 sigue sin
  host x86, el paper reporta E1 y E3 como medidos y E2 como **not measured**,
  con la restricción en la sección de diseño experimental.
- Reportar una fila `synthetic` como si fuera medida es el único fallo que esta
  sección existe para impedir.

---

## 6. Análisis estadístico

### 6.1 Modelo

```
error_arcmin ~ C(architecture) * C(illumination) + fwhm_arcsec + ambient_c
```

ANOVA de dos vías con interacción, tipo II (los factores están balanceados;
tipo II coincide con tipo III en un diseño balanceado y no depende del orden).
Nivel de significancia α = 0.05.

### 6.2 Post-hoc

Tukey HSD sobre las 9 celdas, con intervalos de confianza simultáneos al 95 %.
Se reporta el tamaño de efecto (diferencia de medias en arcmin) y su IC, no solo
el p-valor.

### 6.3 Qué se analiza y qué no

| Análisis | Celdas | Estado |
|---|---|---|
| Principal | E1 y E3 × 3 iluminaciones (6 celdas, 180 filas) | defendible: las dos arquitecturas existen |
| Sensibilidad | las 9 celdas (270 filas) | exploratorio: incluye E2, que no está medido |

El análisis de 9 celdas se reporta como sensibilidad y **no** como resultado
principal. Un ANOVA que incluye una condición que no se puede medir produce un
p-valor sobre datos sintéticos, y eso no es evidencia.

### 6.4 Potencia

Con n = 30 por celda y sd residual ≈ 1.2 arcmin, el diseño detecta una
diferencia de medias de 0.5 arcmin entre dos celdas con potencia ≈ 0.80 a
α = 0.05. Una diferencia menor que eso no se distingue del ruido de centrado y
no merece una noche de observación.

### 6.5 Criterios de invalidez

- Solver de verificación == solver experimental.
- Menos de 6 estrellas en el frame de verificación.
- FWHM > 4 arcsec.
- Corte de red en un episodio E3 no registrado como tal (se registra y se
  analiza aparte: el modo degradado es un resultado).
- Cambio de SQM > 0.5 mag/arcsec² dentro del bloque.

Un episodio inválido no se borra: se marca `valid = false` y se excluye del
ANOVA, con el recuento de exclusiones reportado.
