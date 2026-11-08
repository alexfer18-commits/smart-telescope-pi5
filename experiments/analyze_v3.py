#!/usr/bin/env python3
"""Two-way ANOVA + Tukey HSD for protocol v3.

    python experiments/analyze_v3.py

Reads ``data/simulated_results_v3.csv`` and writes
``data/anova_results_v3.json`` and ``figures/anova_results_v3.pdf``.

The input is synthetic (``source == "synthetic"`` on every row). The root of the
JSON says so, the figure says so in its suptitle, and the Hailo level is
excluded from the primary model because it was never measured. This script is a
test of the statistics pipeline, not evidence about the instrument.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import statsmodels.api as sm  # noqa: E402
from statsmodels.stats.multicomp import pairwise_tukeyhsd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "simulated_results_v3.csv"
JSON_OUT = ROOT / "data" / "anova_results_v3.json"
FIG_OUT = ROOT / "figures" / "anova_results_v3.pdf"

TARGET_ARCMIN = 10.0
SESSION_ORDER = ["cpu_onnx", "hailo8l", "cloud_lambda"]
ILLUM_ORDER = ["dark", "suburban", "moonlight"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def anova_table(df: pd.DataFrame, formula: str) -> dict:
    model = sm.formula.ols(formula, data=df).fit()
    table = sm.stats.anova_lm(model, typ=2)
    return {
        "formula": formula,
        "n": int(model.nobs),
        "r2": round(float(model.rsquared), 4),
        "r2_adj": round(float(model.rsquared_adj), 4),
        "residual_std_arcmin": round(float(np.sqrt(model.mse_resid)), 4),
        "terms": [
            {
                "term": str(term),
                "sum_sq": round(float(row["sum_sq"]), 4),
                "df": int(row["df"]),
                "F": None if pd.isna(row["F"]) else round(float(row["F"]), 3),
                "p": None if pd.isna(row["PR(>F)"]) else float(row["PR(>F)"]),
                "significant_0_05": (None if pd.isna(row["PR(>F)"])
                                     else bool(row["PR(>F)"] < 0.05)),
            }
            for term, row in table.iterrows()
        ],
    }


def tukey(df: pd.DataFrame) -> dict:
    hsd = pairwise_tukeyhsd(df["error_arcmin"], df["cell"], alpha=0.05)
    table = hsd.summary().data
    header, body = table[0], table[1:]
    comparaciones = []
    for row in body:
        rec = dict(zip(header, row))
        comparaciones.append({
            "group_a": str(rec["group1"]),
            "group_b": str(rec["group2"]),
            "mean_diff_arcmin": round(float(rec["meandiff"]), 4),
            "ci95_low": round(float(rec["lower"]), 4),
            "ci95_high": round(float(rec["upper"]), 4),
            "p_adj": round(float(rec["p-adj"]), 6),
            "significant": bool(rec["reject"]),
        })
    comparaciones.sort(key=lambda r: abs(r["mean_diff_arcmin"]), reverse=True)
    return {"alpha": 0.05, "n_pairs": len(comparaciones),
            "comparisons": comparaciones, "_hsd": hsd}


def group_means(df: pd.DataFrame) -> list[dict]:
    out = []
    for (arch, illum), g in df.groupby(["architecture", "illumination"]):
        n = len(g)
        mean = float(g["error_arcmin"].mean())
        sem = float(g["error_arcmin"].std(ddof=1) / np.sqrt(n))
        half = 1.96 * sem
        out.append({
            "architecture": arch,
            "illumination": illum,
            "n": n,
            "mean_arcmin": round(mean, 4),
            "ci95_low": round(mean - half, 4),
            "ci95_high": round(mean + half, 4),
            "std_arcmin": round(float(g["error_arcmin"].std(ddof=1)), 4),
            "over_target": mean > TARGET_ARCMIN,
        })
    return out


def figure(df6: pd.DataFrame, means6: list[dict], hsd6, df9: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(18, 6.0))
    colors = {"cpu_onnx": "#1f77b4", "hailo8l": "#d62728",
              "cloud_lambda": "#2ca02c"}
    x = np.arange(len(ILLUM_ORDER))
    width = 0.28
    arches6 = ["cpu_onnx", "cloud_lambda"]

    # --- panel 1: group means with 95% CI --------------------------------
    ax = axes[0]
    for i, arch in enumerate(arches6):
        sel = [m for m in means6 if m["architecture"] == arch]
        sel = sorted(sel, key=lambda m: ILLUM_ORDER.index(m["illumination"]))
        m = [s["mean_arcmin"] for s in sel]
        err = [[s["mean_arcmin"] - s["ci95_low"] for s in sel],
               [s["ci95_high"] - s["mean_arcmin"] for s in sel]]
        ax.bar(x + (i - 0.5) * width, m, width, yerr=err, capsize=5,
               label=arch, color=colors[arch], alpha=0.85,
               error_kw={"elinewidth": 1.2})
    ax.axhline(TARGET_ARCMIN, color="k", ls="--", lw=1.2)
    ax.annotate("target 10′", xy=(2.0, TARGET_ARCMIN), xytext=(0, 6),
                textcoords="offset points", ha="right", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(ILLUM_ORDER, rotation=15, ha="right")
    ax.set_ylim(0, 12)
    ax.set_xlim(-0.6, 2.6)
    ax.set_ylabel("pointing error (arcmin)")
    ax.set_title("(a) Mean error per cell, 95 % CI\nmeasured-eligible cells only",
                 fontsize=10)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.tick_params(labelsize=9)

    # --- panel 2: Tukey simultaneous CIs ---------------------------------
    ax = axes[1]
    hsd6.plot_simultaneous(ax=ax, comparison_name=None)
    ax.set_xlim(3.2, 10.2)
    ax.set_xlabel("pointing error (arcmin)")
    ax.set_title("(b) Tukey HSD, 95 % simultaneous CI\nmean vs grand mean, 6 cells",
                 fontsize=10)
    ax.tick_params(labelsize=9)

    # --- panel 3: interaction --------------------------------------------
    ax = axes[2]
    for arch in SESSION_ORDER:
        sel = sorted([m for m in group_means(df9) if m["architecture"] == arch],
                     key=lambda m: ILLUM_ORDER.index(m["illumination"]))
        m = np.array([s["mean_arcmin"] for s in sel])
        lo = np.array([s["ci95_low"] for s in sel])
        hi = np.array([s["ci95_high"] for s in sel])
        ls = "-" if arch != "hailo8l" else "--"
        ax.plot(x, m, ls, marker="o", color=colors[arch], lw=1.6,
                label=arch + ("" if arch != "hailo8l" else " (not measured)"))
        ax.fill_between(x, lo, hi, color=colors[arch], alpha=0.13)
    ax.axhline(TARGET_ARCMIN, color="k", ls="--", lw=1.2)
    ax.annotate("target 10′", xy=(2.3, TARGET_ARCMIN), xytext=(0, 6),
                textcoords="offset points", ha="right", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(ILLUM_ORDER, rotation=15, ha="right")
    ax.set_ylim(2, 12)
    ax.set_xlim(-0.4, 2.4)
    ax.set_ylabel("pointing error (arcmin)")
    ax.set_title("(c) Interaction, 9 cells\nsynthetic only",
                 fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.tick_params(labelsize=9)

    fig.suptitle("ANOVA v3 — DATA IS SYNTHETIC, NOT MEASURED. "
                 "Hailo level not measured (no .hef).", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93), w_pad=3.0)
    FIG_OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_OUT)
    plt.close(fig)


def main() -> None:
    if not CSV.exists():
        sys.exit(f"missing {CSV}; run experiments/simulate_v3.py first")

    df = pd.read_csv(CSV)
    df["cell"] = df["architecture"] + " / " + df["illumination"]

    if set(df["source"]) != {"synthetic"}:
        sys.exit("refusing to analyse: input is not uniformly synthetic")

    # Primary model: the two architectures that can actually exist on the bench.
    df6 = df[df["architecture"] != "hailo8l"].copy()

    primary = anova_table(
        df6, "error_arcmin ~ C(architecture) * C(illumination)")
    covariate = anova_table(
        df6, "error_arcmin ~ C(architecture) * C(illumination) "
             "+ fwhm_arcsec + ambient_c")
    sensitivity = anova_table(
        df, "error_arcmin ~ C(architecture) * C(illumination)")

    tukey6 = tukey(df6)
    hsd6 = tukey6.pop("_hsd")
    tukey9 = tukey(df9 := df)
    tukey9.pop("_hsd")

    means6 = group_means(df6)
    means9 = group_means(df)

    payload = {
        # Root-level provenance: this file must never be citable as evidence.
        "data_source": "synthetic",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "input": {"path": str(CSV.relative_to(ROOT)),
                  "sha256": sha256(CSV), "rows": int(len(df)),
                  "cells": int(df["cell"].nunique())},
        "design": {
            "factors": {"architecture": SESSION_ORDER,
                        "illumination": ILLUM_ORDER},
            "repetitions_per_cell": 30,
            "response": "error_arcmin",
            "target_arcmin": TARGET_ARCMIN,
            "alpha": 0.05,
        },
        "primary_analysis": {
            "note": "E1 and E3 only: Hailo was never measured, so it is not "
                    "in the confirmatory model.",
            "n": int(len(df6)),
            "anova": primary,
            "tukey": tukey6,
            "group_means": means6,
        },
        "covariate_adjusted": {
            "note": "Same cells plus fwhm and ambient. fwhm is itself driven "
                    "by illumination, so it absorbs part of the effect; this is "
                    "a robustness check, not the primary result.",
            "anova": covariate,
        },
        "sensitivity_analysis": {
            "note": "All 9 cells including the not-measured Hailo level. "
                    "Exploratory only.",
            "n": int(len(df)),
            "anova": sensitivity,
            "tukey": tukey9,
            "group_means": means9,
        },
        "caveats": [
            "Every row is synthetic; no runtime, camera or mount produced any "
            "of these numbers.",
            "The 90 Hailo rows are additionally marked not_measured: no .hef "
            "exists until an x86 host compiles one.",
            "p-values describe the simulator's parameters, not the instrument.",
            "Replace this file entirely with measured data before submission; "
            "see experiments/experimental_protocol_v3.md §5.",
        ],
    }

    JSON_OUT.write_text(json.dumps(payload, indent=2))
    figure(df6, means6, hsd6, df)

    print(f"wrote {JSON_OUT.relative_to(ROOT)}")
    print(f"wrote {FIG_OUT.relative_to(ROOT)}")
    for term in primary["terms"]:
        p = "  n/a" if term["p"] is None else f"{term['p']:.3e}"
        print(f"  {term['term']:34s} F={term['F']}  p={p}")


if __name__ == "__main__":
    main()
