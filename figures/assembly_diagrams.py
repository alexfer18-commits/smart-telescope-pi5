#!/usr/bin/env python3
"""Two assembly plates for the hardware guide.

    python figures/assembly_diagrams.py

Draws ``figures/assembly_exploded.png`` and ``figures/assembly_side_view.png``
from the same dimensions as ``hardware/*.scad``, so the drawings cannot drift
from the model. These replace the AI renders: a labelled line drawing is what
an assembly guide actually needs, and it is reproducible.

Dimensions in millimetres; the axes are equal-aspect and unlabelled on purpose
(the labels carry the reading, not the axes).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DPI = 200
INK = "#1a1a1a"
GREY = "#8a8a8a"
ACCENT = "#1f4e79"
FILL = "#f4f6f8"
FILL2 = "#e4eaf0"


def box(ax, x, y, w, h, label=None, side="right", dx=18, color=INK, fill=FILL,
        hatch=None, italic=False, fontsize=8.5, dashed=False):
    rect = mpatches.Rectangle(
        (x, y), w, h, linewidth=1.1, edgecolor=color, facecolor=fill,
        hatch=hatch, linestyle="--" if dashed else "-", zorder=2)
    ax.add_patch(rect)
    if label:
        if side == "right":
            tx, ty = x + w + dx, y + h / 2
            ha, a = "left", 0
            ax.plot([x + w, tx - 4], [y + h / 2, ty], color=GREY, lw=0.7,
                    zorder=1)
        else:
            tx, ty = x - dx, y + h / 2
            ha, a = "right", 0
            ax.plot([x, tx + 4], [y + h / 2, ty], color=GREY, lw=0.7, zorder=1)
        ax.text(tx, ty, label, ha=ha, va="center", fontsize=fontsize,
                color=INK, style="italic" if italic else "normal", zorder=3)
    return rect


def dim(ax, x0, x1, y, text, fontsize=7.5):
    ax.annotate("", xy=(x0, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="<->", color=GREY, lw=0.7))
    ax.text((x0 + x1) / 2, y + 1.5, text, ha="center", va="bottom",
            fontsize=fontsize, color=GREY)


# --- plate 1: exploded -------------------------------------------------------
def exploded() -> None:
    fig, ax = plt.subplots(figsize=(10.0, 9.2))

    cx = 0.0
    y = 0.0

    def part(w, h, label, fill=FILL, hatch=None, gap=16, dashed=False):
        nonlocal y
        box(ax, cx - w / 2, y, w, h, label, fill=fill, hatch=hatch,
            dashed=dashed)
        y += h + gap

    part(200, 6, "1 · Base 200×200×6\n4 × M6 al trípode", fill=FILL2)
    part(130, 79, "2 · Torre 130×130×79\n(aloja el motor AZ)", gap=18)
    part(150, 6, "3 · Deck 150×150×6")
    part(42, 40, "4 · NEMA 17 azimut\n17HS4401, 1.8°/paso", fill=FILL2, gap=14)
    part(22, 22, "5 · Acople rígido Ø16×22\nprisioneros M3", gap=14)
    part(150, 6, "6 · Anillo de empuje Ø150", gap=14)
    part(70, 6, "7 · Cubo Ø70 + espárrago 5 mm", gap=14)
    part(150, 8, "8 · Plato Ø150×8\n3 × M5 a la horquilla", fill=FILL2, gap=20)
    part(70, 120, "9 · Horquilla: 2 mejillas\n120 mm, separación 144", gap=18)
    part(60, 96, "10 · Saddle 76×100×26\n+ abrazadera Ø60", gap=14)

    # tube as a long horizontal bar, drawn last so it sits above the fork
    tube_y = y
    ax.add_patch(mpatches.Rectangle((-250, tube_y), 500, 60, linewidth=1.2,
                                    edgecolor=INK, facecolor=FILL2, zorder=2))
    ax.plot([-250, 250], [tube_y + 30, tube_y + 30], color=GREY, lw=0.6,
            ls=(0, (12, 4)), zorder=3)
    ax.text(0, tube_y + 30, "11 · Tubo Ø60 × 500", ha="center", va="center",
            fontsize=9, color=INK, zorder=4,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none"))
    ax.plot([250, 285], [tube_y + 55, tube_y + 62], color=GREY, lw=0.7)
    ax.text(290, tube_y + 62, "eje óptico (Y)", ha="left", va="center",
            fontsize=8.5, color=INK)
    y = tube_y + 60 + 20

    part(93, 3, "12 · Bandeja Pi 5 ventilada\n+ 4 × M2.5", gap=14)
    part(34, 60, "13 · Brazo de cámara\najuste vertical ±9 mm", gap=12)
    part(34, 34, "14 · Placa Camera 3\nslot vertical", gap=20)

    for label, yy in [("AZ", 95), ("ALT", 400)]:
        ax.annotate("", xy=(-95, yy + 40), xytext=(-95, yy),
                    arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.4))
        ax.text(-106, yy + 20, f"eje {label}", fontsize=9, color=ACCENT,
                fontweight="bold", ha="right", va="center")

    ax.set_xlim(-330, 470)
    ax.set_ylim(-14, y + 10)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Vista explosionada — montura alt-azimut, Pi 5\n"
                 "cotas en mm · 14 piezas, 4 de ellas impresas",
                 fontsize=12, pad=14)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.93, bottom=0.01)
    fig.savefig(ROOT / "figures" / "assembly_exploded.png", dpi=DPI,
                facecolor="white")
    plt.close(fig)


# --- plate 2: side elevation -------------------------------------------------
def side_view() -> None:
    fig, ax = plt.subplots(figsize=(14, 6.4))

    # All heights come from the SCAD assemblies. Horizontal axis = vertical
    # stack (X on the drawing), so the tube runs left-right at altitude level.
    box(ax, -100, 0, 200, 6, None, fill=FILL2)                   # base
    box(ax, -65, 6, 130, 79, None)                               # tower
    box(ax, -75, 85, 150, 6, None)                               # deck
    box(ax, -75, 91, 150, 22, None, hatch="////", fill="white")  # posts
    box(ax, -75, 113, 150, 6, None, fill=FILL2)                  # bearing ring
    box(ax, -35, 113, 70, 6, None)                               # hub
    box(ax, -75, 119, 150, 8, None, fill=FILL2)                  # platter
    box(ax, -35, 127, 70, 120, None, hatch="\\\\", fill="white")  # fork cheek

    alt = 232
    # tube: 500 mm, centred on the altitude axis
    ax.add_patch(mpatches.Rectangle((-250, alt - 30), 500, 60, linewidth=1.4,
                                    edgecolor=INK, facecolor=FILL, zorder=3))
    ax.plot([-250, 250], [alt, alt], color=GREY, lw=0.7, ls=(0, (14, 5)),
            zorder=4)
    # saddle
    ax.add_patch(mpatches.Rectangle((-50, alt - 30), 100, 22, linewidth=1.1,
                                    edgecolor=INK, facecolor=FILL2, zorder=4))
    # collar + Pi tray at the rear third
    cx = -120
    box(ax, cx + 19, alt - 34, 12, 8, None, fill=FILL2, dashed=True)
    box(ax, cx + 19, alt + 26, 12, 8, None, fill=FILL2, dashed=True)
    box(ax, cx - 46, alt + 33, 93, 3, None, fill=FILL2)
    box(ax, cx - 27, alt + 36, 56, 16, None, hatch="....", fill="white")
    ax.text(cx, alt + 44, "Pi 5", ha="center", va="center", fontsize=8,
            zorder=5)
    # camera arm: down from the tray, back past the eyepiece
    ax.add_patch(mpatches.Rectangle((cx - 52, alt - 30), 6, 63,
                                    linewidth=1.1, edgecolor=INK,
                                    facecolor=FILL, zorder=3))
    ax.add_patch(mpatches.Rectangle((-262, alt - 30), 96, 5,
                                    linewidth=1.1, edgecolor=INK,
                                    facecolor=FILL, zorder=3))
    box(ax, -266, alt - 9, 4, 34, None, fill=FILL2)

    def note(xy, text, tx, ty, ha="right"):
        ax.annotate(text, xy=xy, xytext=(tx, ty), ha=ha, va="center",
                    fontsize=8.5, color=INK, zorder=6,
                    arrowprops=dict(arrowstyle="-", color=GREY, lw=0.7,
                                    shrinkA=2, shrinkB=2))

    # left column
    note((-250, 252), "tubo Ø60 × 500", -290, 258)
    note((-100, 281), "bandeja Pi 5\n+ HAT opcional", -290, 292)
    note((-263, 240), "Camera 3\najuste ±9 mm", -300, 218)
    note((-50, 206), "saddle + abrazadera\ncentro de masas AQUÍ", -290, 178)
    note((-35, 152), "mejilla 120 mm\nPETG, 4 paredes", -290, 148)
    note((-75, 123), "plato Ø150 × 8", -290, 118)
    note((-75, 88), "deck 150 × 150 × 6", -290, 88)
    note((-65, 45), "torre 130 × 130 × 79\nmotor AZ dentro", -290, 45)

    # right column
    note((75, 116), "anillo de empuje Ø150\n+ 3 postes", 290, 132, ha="left")
    note((100, 3), "base 200 × 200 × 6\n4 × M6 al trípode", 290, 8, ha="left")

    # azimuth axis (vertical, no gravitational torque)
    ax.plot([0, 0], [-8, 330], color=ACCENT, lw=0.9, ls=(0, (6, 4)), zorder=1)
    ax.text(-14, 326, "eje de azimut\n(vertical, sin par\ngravitatorio)",
            ha="right", va="top", fontsize=9, color=ACCENT, fontweight="bold")

    # altitude axis leaves the page: mark it at the tube centre
    ax.plot([0], [alt], marker="o", ms=13, mfc="white", mec=ACCENT, mew=1.2,
            zorder=7)
    ax.plot([-4.5, 4.5], [alt - 4.5, alt + 4.5], color=ACCENT, lw=1.0, zorder=8)
    ax.plot([-4.5, 4.5], [alt + 4.5, alt - 4.5], color=ACCENT, lw=1.0, zorder=8)
    note((0, alt + 30), "eje de altitud\n(sale del papel)", 110, 300, ha="left")

    dim(ax, -100, 100, -16, "200 mm")

    ax.set_xlim(-400, 400)
    ax.set_ylim(-30, 342)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Vista lateral — montura ensamblada con tubo Ø60\n"
                 "el centro de masas del tubo debe caer sobre el cruce de ambos ejes",
                 fontsize=12, pad=12)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.90, bottom=0.01)
    fig.savefig(ROOT / "figures" / "assembly_side_view.png", dpi=DPI,
                facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    exploded()
    side_view()
    for name in ("assembly_exploded.png", "assembly_side_view.png"):
        p = ROOT / "figures" / name
        print(f"wrote {p.relative_to(ROOT)} ({p.stat().st_size // 1024} kB)")
