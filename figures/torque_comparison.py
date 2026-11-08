#!/usr/bin/env python3
"""Torque envelope of the altitude axis.

    python figures/torque_comparison.py

Draws ``figures/torque_comparison.pdf``. The numbers are the ones worked in
``docs/mechanical_analysis.md`` §1: 2.5 kg tube, gravity, and the 0.28 N·m the
17HS4401 can hold at the 1.2 A the A4988 accepts. The bar chart is logarithmic
because the useful case and the failure case span two orders of magnitude; on a
linear axis the balanced bar would be invisible, which is the point.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "figures" / "torque_comparison.pdf"

INK = "#1a1a1a"
GREY = "#8a8a8a"
ACCENT = "#1f4e79"
BAD = "#b03a2e"

AVAILABLE = 0.28   # N·m, 40 N·cm x (1.2 A / 1.7 A)
UNBALANCED = 4.91  # N·m, 2.5 kg x 9.81 x 0.20 m
BALANCED = 0.045   # N·m, bearing friction + inertia, centroid on the axis

assert abs(AVAILABLE / BALANCED - 6.2) < 0.05   # 6.2x margin
assert abs(AVAILABLE / UNBALANCED - 0.06) < 0.005  # 0.06x, cannot move


def main() -> None:
    labels = ["Unbalanced altitude\n(20 cm lever)", "Balanced altitude\n(centroid on axis)",
              "NEMA 17 available\n(1.2 A through the A4988)"]
    values = [UNBALANCED, BALANCED, AVAILABLE]
    colors = [BAD, ACCENT, GREY]

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    bars = ax.bar(labels, values, width=0.55, color=colors, edgecolor=INK,
                  linewidth=0.8, zorder=3)

    ax.set_yscale("log")
    ax.set_ylim(0.03, 9)
    ax.set_ylabel("Torque at the axis (N·m, log scale)", fontsize=10)
    ax.set_title("Altitude axis: required vs available torque", fontsize=12,
                 pad=14)

    limit = ax.axhline(AVAILABLE, color=INK, linestyle="--", linewidth=1.1, zorder=4)

    for bar, value in zip(bars, values):
        label = f"{value:.3f}".rstrip("0").rstrip(".")
        ax.annotate(f"{label} N·m", xy=(bar.get_x() + bar.get_width() / 2, value),
                    xytext=(0, 4), textcoords="offset points", ha="center",
                    va="bottom", fontsize=9.5, color=INK)

    ax.annotate("0.06× — motor cannot move the tube", xy=(0.29, UNBALANCED),
                xytext=(0.38, UNBALANCED), va="center", ha="left",
                fontsize=9, color=BAD, fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=BAD, lw=0.9))
    ax.annotate("6.2× margin", xy=(1, 0.10), ha="center", fontsize=9,
                color=ACCENT, fontweight="bold")

    ax.grid(axis="y", color="#e4eaf0", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    ax.legend(handles=[limit], labels=["NEMA 17 limit at 1.2 A"],
              loc="upper right", fontsize=8.5, frameon=False)

    fig.text(0.5, 0.015,
             "Balanced = tube centroid on the altitude axis; a ~150 g counterweight "
             "recovers ~15 mm of offset.",
             ha="center", fontsize=7.5, color=GREY)
    fig.subplots_adjust(left=0.10, right=0.98, top=0.88, bottom=0.20)

    fig.savefig(OUT, facecolor="white")
    plt.close(fig)
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} kB)")


if __name__ == "__main__":
    main()
