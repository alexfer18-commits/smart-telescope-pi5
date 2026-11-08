# Guía de ensamblaje — montura alt-azimut de bajo costo

Montura alt-azimut motorizada para un tubo de 60 mm, con Raspberry Pi 5 como
controlador. Todo lo que se imprime está en `hardware/*.scad`; todo lo que se
compra está en `hardware/SHOPPING_LIST.md`.

**Orden de lectura.** Esta guía se ejecuta de arriba abajo, y el orden importa:
los pasos 1–3 no necesitan el tubo, los 4–5 sí, y el 6 se hace con todo apagado.

---

## 1. Vista general

### 1.1 Vista lateral

```
                          tubo Ø60 × 500 mm (no incluido en el .scad)
                    ┌──────────────────────────────────┐
                    │        OTA / guidescope          │
        ╔═══════════╧══════════════════════════════════╧═══════════╗
        ║  soporte (saddle) 76 × 100 × 26, abrazadera Ø60          ║
        ╠═══════════════════════╤══════════════════════════════════╣
        ║                       │  eje de altitud (Ø8, horizontal)  ║
   ╔════╩════╗                  │                    ╔═════════════╩╗
   ║ mejilla ║                  │                    ║  mejilla     ║
   ║  −X     ║                  │                    ║  +X + motor  ║
   ╚════╤════╝                  │                    ╚═══════╤══════╝
        │              ┌────────┴────────┐                  │
        │              │  plato Ø150 × 8 │  ← eje de azimut │
        │              └────────┬────────┘                  │
        │        ┌──────────────┴──────────────┐             │
        │        │  anillo de empuje Ø150 × 6  │             │
        │        └──────────────┬──────────────┘             │
        │        ┌──────────────┴──────────────┐             │
        └────────┤  tapa / deck 150 × 150 × 6  ├─────────────┘
                 └──────────────┬──────────────┘
                 ┌──────────────┴──────────────┐
                 │  torre 130 × 130 × 79       │  ← motor AZ dentro
                 └──────────────┬──────────────┘
                 ┌──────────────┴──────────────┐
                 │  base 200 × 200 × 6         │  ← 4 × M6 al trípode
                 └─────────────────────────────┘

   alturas:  base 0–6 · torre 6–85 · deck 85–91 · postes 91–113
             anillo 113–119 · plato 119–127 · eje altitud a 105 sobre el plato
```

### 1.2 Vista superior

```
                         Y
                         ↑   tubo (eje óptico, sale de la página)
                         │
              ┌──────────┴──────────┐
              │      OTA Ø60        │
     ╔════════╪═════════════════════╪════════╗
     ║ mejilla║                     ║mejilla ║
     ║  −X    ║      saddle         ║  +X    ║  ← separación 144 mm
     ╚════╤═══╧═════════════════════╧═══╤════╝     (x = ±72)
          │                            │
          │      plato Ø150            │
          │   ┌────────────────────┐   │
          └───┤  torre 130 × 130   ├───┘
              └────────────────────┘
                   base 200 × 200
              ○                        ○
                         ○        ○
   ───────────────────────┼───────────────────────────→ X
                          │
                          ↓
                     trípode (M6)

   El centro de masa del tubo debe caer sobre el cruce de los dos ejes
   (origen). Ver docs/mechanical_analysis.md §4.
```

### 1.3 Qué se imprime

| Pieza | Archivo | Material | Boquilla / paredes / relleno |
|---|---|---|---|
| Abrazadera + bandeja Pi | `pi5_camera_mount.scad` (`part="collar"`, `"tray"`) | PETG la abrazadera, PLA la bandeja | 0.4 mm · 4 paredes · 40 % |
| Brazo y placa de cámara | `pi5_camera_mount.scad` (`"arm"`, `"plate"`) | PETG | 0.4 mm · 3 paredes · 25 % |
| Escuadra de motor + acople | `nema17_coupling.scad` | PETG | 0.4 mm · 4 paredes · 50 % |
| Eje azimut completo | `az_axis_assembly.scad` | PETG | 0.4 mm · 4 paredes · 40 % |
| Eje altitud completo | `alt_axis_assembly.scad` | PETG | 0.4 mm · 4 paredes · 40 % |

La abrazadera y la escuadra llevan esfuerzo sostenido: **no las imprimas en
PLA**. El PLA fluye bajo carga constante y a 40 °C al sol una abrazadera de PLA
pierde el apriete en una tarde.

---

## 2. Orden de ensamblaje (de lo simple a lo complejo)

### Paso 1 — Verificar el A4988 antes de tocar el motor

Esto se hace **con el motor desconectado**. Ver §4.1. Si el Vref viene de
fábrica en 1.5 V, conectar el motor lo sobrecalienta en minutos.

### Paso 2 — Eje azimutal (`az_axis_assembly.scad`)

1. Base 200 × 200 × 6 sobre la mesa, cara buena arriba.
2. Torre 130 × 130 × 79: 4 × M4 desde abajo, tuercas dentro de la torre.
3. Motor AZ dentro de la torre, brida hacia arriba, 4 × M3 en la cuadrícula
   31 × 31. El eje debe sobresalir por el agujero de Ø26 del deck.
4. Deck 150 × 150 × 6 sobre la torre, 4 × M4. Comprobar que el eje gira libre,
   sin rozar.
5. Acople rígido de 22 mm sobre el eje del motor. **No aprietes el prisionero
   todavía**: primero hay que meter el espárrago del cubo.
6. Tres postes Ø14 × 22 en el deck, a 60 mm del centro (90°, 210°, 330°).
7. Anillo de empuje Ø150 × 6 sobre los postes.
8. Cubo Ø70 × 6 dentro del anillo, con su espárrago de 5 mm hacia abajo dentro
   del acople. Ahora sí: dos prisioneros M3 a 0.8 N·m, sobre las caras planas
   limadas en ambos ejes.
9. Plato Ø150 × 8 sobre el cubo, 3 × M4.
10. Girar el plato a mano: debe dar una vuelta completa sin ruido y sin juego
    apreciable. Si roza, el cubo no está coaxial — afloja los postes y repite.

### Paso 3 — Eje de altitud (`alt_axis_assembly.scad`)

1. Dos pies 60 × 90 × 8 sobre el plato del azimut, 2 × M5 cada uno.
2. Mejillas a x = ±72, 2 × M6 por mejilla a los pies.
3. Rodamientos 608ZZ en los alojamientos de Ø22 de ambas mejillas. Entran a
   presión; si no entran, calienta la mejilla 10 s con secador, no la fuerces.
4. Eje Ø8 a través de ambos rodamientos. Debe girar con dos dedos.
5. Cubo del eje (70 × 100 × 34) centrado, prisionero M6 al eje. **Este es el
   prisionero que transmite todo el par de altitud**: 6 N·m, sobre cara plana.
6. Motor ALT en la cara exterior de la mejilla +X, brida contra la mejilla,
   4 × M3. Acople de 22 mm entre el eje del motor y el extremo del eje de 8 mm
   (con un adaptador 8→5 mm, o limando el eje a 5 mm en el tramo del acople).
7. Saddle 76 × 100 × 26 sobre el cubo, 2 × M6.
8. Abrazadera superior (strap) sobre el tubo, 2 × M5, **sin apretar**.
9. Tubo en el saddle, deslizado hasta que quede equilibrado (§4.3), y solo
   entonces aprieta el strap a 1.5 N·m.

### Paso 4 — Bandeja del Pi y cámara

1. Abrazadera de tubo abierta sobre el tubo, en el tercio trasero (el lado del
   ocular). 2 × M4 de apriete, 1.5 N·m. El tubo no debe marcar: si marca, pega
   una tira de fieltro de 1 mm dentro de la abrazadera.
2. Bandeja del Pi sobre los dos pads de la abrazadera, 2 × M4.
3. Pi 5 sobre la bandeja, 4 × M2.5 × 6. Los slots de ventilación quedan bajo el
   SoC.
4. Brazo de cámara bajo la bandeja, 2 × M3 × 10 desde abajo.
5. Placa de cámara en el extremo del brazo, 2 × M3. Los slots verticales dan
   ±9 mm de ajuste: súbela o bájala hasta que el objetivo de la Camera 3 quede
   centrado con el ocular.
6. Cable flexible de la cámara por el lado libre del brazo, nunca por debajo del
   tubo: en un slew el cable se engancha en el trípode.

### Paso 5 — Equilibrado (el paso que decide si el motor alcanza)

1. Con la montura sin motor conectado, pon el tubo horizontal.
2. Suéltalo. Si cae hacia el objetivo, el centro de masa está delante del eje:
   desliza el tubo hacia atrás en el saddle.
3. Repite hasta que quede quieto en cualquier ángulo. Ver §4.3 para el número.
4. Aprieta el strap y marca la posición con cinta.

### Paso 6 — Cableado (todo apagado)

§5. Conecta primero **GND**, después lógica, después VMOT. Nunca al revés y
nunca con la fuente encendida.

### Paso 7 — Primera energización

1. Fuente de 12 V desconectada de la red.
2. Buck ajustado a 5.1 V **en vacío**, medido con polímetro.
3. Conecta el buck a los pines 5 V (pin 2/4) y GND (pin 6) del Pi. Respeta la
   polaridad: invertirla mata el Pi, no hay protección.
4. Enciende la fuente. LED del Pi encendido, sin olor.
5. `python -c "import gpiozero"` y un movimiento de 10 pasos en cada eje.
6. Mide la temperatura del A4988 a los 5 minutos: si quema el dedo (> 70 °C),
   baja el Vref un 20 % o pon ventilador.

---

## 3. Advertencias de seguridad

### 3.1 Vref del A4988 — antes de conectar el motor

`Vref = I_fase × 8 × Rs`. Con Rs = 0.1 Ω (módulos verdes habituales):

| Corriente por fase | Vref | Cuándo |
|---|---|---|
| 1.20 A | **0.96 V** | ajuste recomendado, 5× de margen de par |
| 1.70 A | 1.36 V | corriente nominal del 17HS4401 — **no usar en A4988** |

Medición: fuente a 12 V en VMOT, lógica alimentada, **motor desconectado**.
Punta negra a GND, punta positiva al tornillo del potenciómetro. Gíralo con un
destornillador **plástico**; el de metal cortocircuita y mata el driver.

### 3.2 Orden de conexión

1. **Nunca** desconectes un motor con la alimentación puesta. El pico inductivo
   destruye el puente en H, y lo hace en el acto.
2. Conecta GND antes que nada, VMOT al final.
3. Un condensador electrolítico de **100 µF / 25 V** entre VMOT y GND, lo más
   cerca posible del driver. El A4988 sin él oscila y se recalienta.
4. Verifica el orden de las bobinas con un polímetro en ohmios: dos pares con
   ~2.4 Ω cada uno. Si mides continuidad entre los cuatro cables, el motor está
   mal y el driver se destruye al energizar.

### 3.3 Par de apriete

| Tornillo | Dónde | Par |
|---|---|---|
| M2.5 | Pi 5 a la bandeja | 0.35 N·m |
| M2 | Camera 3 | 0.20 N·m |
| M3 | motor al soporte | 0.60 N·m |
| M3 | inserto térmico en PETG | 0.50 N·m |
| M3 | prisionero del acople | 0.80 N·m |
| M4 | abrazadera al tubo | 1.50 N·m |
| M4 | tuerca en extrusión de aluminio | 2.50 N·m |
| M6 | cubo del eje de altitud | 6.0 N·m |

Más par en un inserto de PETG no sujeta más: arranca el inserto y deja la pieza
inservible. Si una rosca se pasa, taladra a Ø6 y pon un inserto mayor.

### 3.4 El tubo y el sol

Nunca apuntes al sol sin filtro delante del objetivo, ni siquiera para probar el
motor. La Camera 3 sin filtro se satura de forma permanente en menos de un
segundo, y el ocular concentra luz suficiente para dañar la vista.

---

## 4. Cableado: Pi 5 GPIO → A4988 → NEMA 17

### 4.1 Mapa de pines (BCM)

| Señal | GPIO (BCM) | Pin físico | Va a |
|---|---|---|---|
| AZ STEP | GPIO 17 | 11 | STEP del A4988 AZ |
| AZ DIR | GPIO 27 | 13 | DIR del A4988 AZ |
| AZ ENABLE | GPIO 22 | 15 | EN del A4988 AZ |
| ALT STEP | GPIO 23 | 16 | STEP del A4988 ALT |
| ALT DIR | GPIO 24 | 18 | DIR del A4988 ALT |
| ALT ENABLE | GPIO 25 | 22 | EN del A4988 ALT |
| Lógica 3V3 | — | 1 | VDD de ambos drivers + MS1/2/3 |
| GND | — | 6, 9, 14, 20 | GND de ambos drivers |
| 5 V del buck | — | 2, 4 | entrada del Pi |

`EN` es activo a nivel bajo en el A4988: GPIO 22 en alto **libera** el motor y
el tubo se cae por gravedad. El firmware debe arrancar con los dos ejes
energizados (`EN` en bajo) antes de mover nada.

### 4.2 Diagrama

```
  Raspberry Pi 5 (J8, 40 pines)          A4988 (AZ)              NEMA 17 (AZ)
  ─────────────────────────────          ──────────              ────────────
   pin  1  3V3 ───────┬────────────────→ VDD
   pin 11  GPIO17 ─────────────────────→ STEP
   pin 13  GPIO27 ─────────────────────→ DIR
   pin 15  GPIO22 ─────────────────────→ EN
   pin  6  GND ───────┼────────────────→ GND  (lógica)
                      ├────────────────→ MS1 ┐
                      ├────────────────→ MS2 ├─ 1/16 de paso
                      └────────────────→ MS3 ┘
                                        RESET ─┐
                                        SLEEP ─┴── puenteados entre sí
   12 V +  ────────────────────────────→ VMOT
   12 V −  ──┬─────────────────────────→ GND  (motor)
             └── 100 µF / 25 V ─────────┘
                                        1A ──→ negro   (bobina A+)
                                        1B ──→ verde   (bobina A−)
                                        2A ──→ rojo    (bobina B+)
                                        2B ──→ azul    (bobina B−)

  El A4988 (ALT) repite el bloque con GPIO 23/24/25.
  Los dos drivers comparten 3V3, GND y los 12 V; NO comparten STEP/DIR.
```

Colores de cable del 17HS4401: negro/verde = bobina A, rojo/azul = bobina B.
Verifícalo con el polímetro antes de conectar (§3.2.4); hay unidades con el
conector girado 180°.

### 4.3 Reparto de corriente

Dos NEMA 17 a 1.2 A por fase son 2.4 A de la fuente de 5 A, más 3 A del Pi por
el buck. La fuente de 12 V / 5 A queda justa: **no muevas los dos ejes a la vez
a máxima corriente**. El firmware debe intercalar los movimientos (un eje por
vez) o subir a una fuente de 12 V / 8 A. Es la razón por la que el BOM pide 5 A
y no 3 A.

---

## 5. Checklist de la primera noche

- [ ] Vref medido en ambos drivers, anotado en el cuaderno
- [ ] 100 µF presente en cada driver
- [ ] Bobinas identificadas con polímetro
- [ ] Buck a 5.1 V en vacío, polaridad verificada
- [ ] Los dos ejes giran 10 pasos en ambos sentidos desde el Pi
- [ ] `EN` en bajo al arrancar (ejes con par)
- [ ] Tubo equilibrado: se queda quieto en horizontal
- [ ] A4988 < 70 °C a los 5 minutos
- [ ] Límites software de altitud activos (`[-5°, 95°]`)
