#!/usr/bin/env python3
"""Build experiment_results_v3.xlsx from the synthetic campaign.

    python experiments/build_excel_v3.py

Five sheets: Raw Data, Summary, ANOVA, Cost Analysis, Dashboard.
Conditional formatting: red where the pointing error exceeds the 10 arcmin
target, yellow on every row whose ``source`` is "synthetic".

Every number in the workbook is synthetic. The Dashboard says so in a banner and
nothing in the file removes that banner.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "benchmarks"))

from compare_inference import (CAPEX_USD, CLOUD_USD_PER_INFERENCE,  # noqa: E402
                               LATENCY_MODEL_MS, POWER_W)

CSV = ROOT / "data" / "simulated_results_v3.csv"
ANOVA = ROOT / "data" / "anova_results_v3.json"
OUT = ROOT / "experiment_results_v3.xlsx"

TARGET = 10.0
KWH_USD = 0.15
AMORTISE_MONTHS = 24
SESSIONS_PER_MONTH = 8
EPISODES_PER_SESSION = 50

RED = PatternFill("solid", fgColor="FFC7CE")
YELLOW = PatternFill("solid", fgColor="FFEB9C")
GREEN = PatternFill("solid", fgColor="C6EFCE")
HEAD = PatternFill("solid", fgColor="1F3864")
HEAD_FONT = Font(bold=True, color="FFFFFF", size=10)
THIN = Side(style="thin", color="D0D0D0")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def style_header(ws, row: int, ncols: int) -> None:
    for col in range(1, ncols + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = HEAD
        cell.font = HEAD_FONT
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = 30


def autosize(ws, widths: dict[int, int]) -> None:
    for col, width in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = width


# --- sheets -----------------------------------------------------------------
def sheet_raw(wb: Workbook, df: pd.DataFrame) -> None:
    ws = wb.active
    ws.title = "Raw Data"
    ws.append(list(df.columns))
    style_header(ws, 1, len(df.columns))

    for row in df.itertuples(index=False):
        ws.append(list(row))

    n = len(df) + 1
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(df.columns))}{n}"
    autosize(ws, {1: 22, 2: 12, 3: 14, 4: 12, 5: 10, 6: 10, 7: 12, 8: 13,
                  9: 9, 10: 11, 11: 11, 12: 12, 13: 8, 14: 12, 15: 16, 16: 8})

    err_col = get_column_letter(list(df.columns).index("error_arcmin") + 1)
    src_col = get_column_letter(list(df.columns).index("source") + 1)
    last = get_column_letter(len(df.columns))

    # red: pointing error above the 10 arcmin target
    ws.conditional_formatting.add(
        f"{err_col}2:{err_col}{n}",
        CellIsRule(operator="greaterThan", formula=[str(TARGET)], fill=RED))
    # yellow: the whole row is synthetic
    ws.conditional_formatting.add(
        f"A2:{last}{n}",
        FormulaRule(formula=[f'${src_col}2="synthetic"'], fill=YELLOW))


def sheet_summary(wb: Workbook, means: list[dict]) -> None:
    ws = wb.create_sheet("Summary")
    ws["A1"] = "Group means — pointing error per condition"
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = "All rows synthetic. Hailo cells were never measured (no .hef)."
    ws["A2"].font = Font(italic=True, size=9, color="9C0006")

    header = ["Architecture", "Illumination", "n", "Mean (arcmin)", "SD",
              "95 % CI low", "95 % CI high", "Over 10′ target?", "Status"]
    ws.append([])
    ws.append(header)
    style_header(ws, 4, len(header))

    for m in sorted(means, key=lambda r: (r["architecture"], r["illumination"])):
        status = ("not_measured" if m["architecture"] == "hailo8l"
                  else "synthetic")
        ws.append([m["architecture"], m["illumination"], m["n"],
                   m["mean_arcmin"], m["std_arcmin"], m["ci95_low"],
                   m["ci95_high"], "YES" if m["over_target"] else "no", status])

    n = 4 + len(means)
    for row in ws.iter_rows(min_row=5, max_row=n, max_col=len(header)):
        for cell in row:
            cell.border = BORDER
    for r in range(5, n + 1):
        for col in (4, 6, 7):
            ws.cell(row=r, column=col).number_format = "0.00"
        ws.cell(row=r, column=5).number_format = "0.00"

    ws.conditional_formatting.add(
        f"D5:D{n}",
        CellIsRule(operator="greaterThan", formula=[str(TARGET)], fill=RED))
    ws.conditional_formatting.add(
        f"A5:I{n}",
        FormulaRule(formula=['$I5="synthetic"'], fill=YELLOW))

    autosize(ws, {1: 14, 2: 12, 3: 6, 4: 14, 5: 8, 6: 12, 7: 12, 8: 17, 9: 15})


def sheet_anova(wb: Workbook, data: dict) -> None:
    ws = wb.create_sheet("ANOVA")
    ws["A1"] = "Two-way ANOVA — error_arcmin ~ architecture * illumination"
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = ("data_source = synthetic. p-values describe the simulator, "
                "not the instrument.")
    ws["A2"].font = Font(italic=True, size=9, color="9C0006")

    row = 4
    for block, key in [("PRIMARY — 6 cells (E1 + E3, 180 episodes)",
                        "primary_analysis"),
                       ("SENSITIVITY — 9 cells incl. not-measured Hailo (270)",
                        "sensitivity_analysis")]:
        ws.cell(row=row, column=1, value=block).font = Font(bold=True, size=11)
        row += 1
        header = ["Term", "Sum of squares", "df", "F", "p", "Significant (α=0.05)"]
        for i, h in enumerate(header, start=1):
            ws.cell(row=row, column=i, value=h)
        style_header(ws, row, len(header))
        row += 1
        for term in data[key]["anova"]["terms"]:
            ws.cell(row=row, column=1, value=term["term"])
            ws.cell(row=row, column=2, value=term["sum_sq"]).number_format = "0.000"
            ws.cell(row=row, column=3, value=term["df"])
            ws.cell(row=row, column=4,
                    value=term["F"]).number_format = "0.000" if term["F"] else "@"
            ws.cell(row=row, column=5,
                    value=term["p"]).number_format = "0.00E+00" if term["p"] else "@"
            ws.cell(row=row, column=6,
                    value=("yes" if term["significant_0_05"] else
                           "—" if term["significant_0_05"] is None else "no"))
            row += 1
        ws.cell(row=row, column=1,
                value=f"R² = {data[key]['anova']['r2']} · "
                      f"residual SD = {data[key]['anova']['residual_std_arcmin']} arcmin")
        ws.cell(row=row, column=1).font = Font(italic=True, size=9)
        row += 2

    # Tukey, primary
    ws.cell(row=row, column=1,
            value="Tukey HSD — 95 % simultaneous CI, primary cells").font = Font(bold=True, size=11)
    row += 1
    header = ["Group A", "Group B", "Difference (arcmin)", "CI low", "CI high",
              "p adjusted", "Significant"]
    for i, h in enumerate(header, start=1):
        ws.cell(row=row, column=i, value=h)
    style_header(ws, row, len(header))
    row += 1
    first = row
    for c in data["primary_analysis"]["tukey"]["comparisons"]:
        ws.cell(row=row, column=1, value=c["group_a"])
        ws.cell(row=row, column=2, value=c["group_b"])
        for col, val in ((3, c["mean_diff_arcmin"]), (4, c["ci95_low"]),
                         (5, c["ci95_high"])):
            ws.cell(row=row, column=col, value=val).number_format = "0.00"
        ws.cell(row=row, column=6, value=c["p_adj"]).number_format = "0.0000"
        ws.cell(row=row, column=7, value="yes" if c["significant"] else "no")
        row += 1

    # green the intervals that exclude zero
    ws.conditional_formatting.add(
        f"C{first}:G{row - 1}",
        FormulaRule(formula=[f'$G{first}="yes"'], fill=GREEN))

    autosize(ws, {1: 34, 2: 26, 3: 18, 4: 12, 5: 12, 6: 18, 7: 12})


def sheet_cost(wb: Workbook) -> None:
    ws = wb.create_sheet("Cost Analysis")
    ws["A1"] = "Cost per episode — capex amortised 24 months + measured energy"
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = ("Synthetic inputs: latency and power come from the documented "
                "models, not from the Pi. Recompute when measured data exists.")
    ws["A2"].font = Font(italic=True, size=9, color="9C0006")

    header = ["Architecture", "CAPEX (USD)", "$/month amortised",
              "p50 latency (ms)", "Power (W)", "Energy (Wh/episode)",
              "Energy $/episode", "Cloud $/episode",
              "Total $/1000 episodes", "Payback vs CPU"]
    ws.append([])
    ws.append(header)
    style_header(ws, 4, len(header))

    rows = []
    for arch in ("cpu_onnx", "hailo8l", "cloud_lambda"):
        lat = LATENCY_MODEL_MS[arch][0]
        watts = POWER_W[arch]
        # one episode = solve + verification + settle, 3 s of idle at the end
        seconds = lat / 1000.0 + 3.0
        wh = watts * seconds / 3600.0
        energy_usd = wh / 1000.0 * KWH_USD
        cloud_usd = 2 * CLOUD_USD_PER_INFERENCE
        per_ep = energy_usd + cloud_usd
        rows.append((arch, CAPEX_USD.get(arch, 0.0), lat, watts, wh,
                     energy_usd, cloud_usd, per_ep))

    for arch, capex, lat, watts, wh, energy_usd, cloud_usd, per_ep in rows:
        ws.append([arch, capex, capex / AMORTISE_MONTHS, round(lat, 1), watts,
                   wh, energy_usd, cloud_usd, per_ep * 1000, ""])

    # payback: months of CPU cost needed to recover a capex
    cpu_per_ep = rows[0][7]
    sessions = SESSIONS_PER_MONTH * EPISODES_PER_SESSION
    for r, (arch, capex, lat, watts, wh, energy_usd, cloud_usd, per_ep) in \
            enumerate(rows, start=5):
        cell = ws.cell(row=r, column=10)
        if capex == 0:
            cell.value = "—"
            continue
        saved = (cpu_per_ep - per_ep) * sessions          # USD per month
        if saved <= 0:
            cell.value = "never (costs more to run)"
            cell.fill = RED
        else:
            months = capex / saved
            cell.value = f"{months:.0f} months"
            if months > AMORTISE_MONTHS:
                cell.fill = RED

    for r in range(5, 8):
        ws.cell(row=r, column=2).number_format = '"$"#,##0'
        ws.cell(row=r, column=3).number_format = '"$"0.00'
        ws.cell(row=r, column=7).number_format = '"$"0.00E+00'
        ws.cell(row=r, column=8).number_format = '"$"0.00E+00'
        ws.cell(row=r, column=9).number_format = '"$"0.00'
        ws.cell(row=r, column=6).number_format = "0.0000"

    ws.cell(row=9, column=1,
            value=f"Assumptions: {KWH_USD} USD/kWh · {SESSIONS_PER_MONTH} sessions/month "
                  f"· {EPISODES_PER_SESSION} episodes/session = {sessions} episodes/month")
    ws.cell(row=9, column=1).font = Font(italic=True, size=9)
    ws.cell(row=10, column=1,
            value="The Hailo never pays back at amateur volume: its CAPEX is $70 "
                  "and its 9.8 W is higher than the CPU's 7.5 W, so it costs more "
                  "per episode to run as well as more to buy. It wins on latency, "
                  "not on money.")
    ws.cell(row=10, column=1).font = Font(italic=True, size=9)
    ws.merge_cells("A10:J10")
    ws.cell(row=10, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[10].height = 42

    autosize(ws, {1: 15, 2: 12, 3: 16, 4: 15, 5: 10, 6: 17, 7: 15, 8: 15,
                  9: 20, 10: 26})


def sheet_dashboard(wb: Workbook, df: pd.DataFrame, data: dict) -> None:
    ws = wb.create_sheet("Dashboard")
    ws["A1"] = "Experiment results v3 — dashboard"
    ws["A1"].font = Font(bold=True, size=16)

    ws["A2"] = "DATA IS SYNTHETIC — NOT MEASURED. Hailo cells are not_measured."
    ws["A2"].fill = RED
    ws["A2"].font = Font(bold=True, size=11, color="9C0006")
    ws.merge_cells("A2:D2")

    means = data["sensitivity_analysis"]["group_means"]
    worst = max(means, key=lambda m: m["mean_arcmin"])
    best = min(means, key=lambda m: m["mean_arcmin"])
    over = sum(1 for m in means if m["over_target"])

    rows = [
        ("Episodes", len(df)),
        ("Conditions (3 × 3)",
         df.groupby(["architecture", "illumination"]).ngroups),
        ("Repetitions per condition", 30),
        ("Rows with source = synthetic", int((df["source"] == "synthetic").sum())),
        ("Rows with measurement_status = not_measured",
         int((df["measurement_status"] == "not_measured").sum())),
        ("Mean pointing error (arcmin)",
         round(float(df["error_arcmin"].mean()), 2)),
        ("Cells above the 10′ target", f"{over} of {len(means)}"),
        ("Best cell", f"{best['architecture']} / {best['illumination']} "
                      f"({best['mean_arcmin']}′)"),
        ("Worst cell", f"{worst['architecture']} / {worst['illumination']} "
                       f"({worst['mean_arcmin']}′)"),
        ("ANOVA: architecture", _fmt_p(data["primary_analysis"]["anova"], 0)),
        ("ANOVA: illumination", _fmt_p(data["primary_analysis"]["anova"], 1)),
        ("ANOVA: interaction", _fmt_p(data["primary_analysis"]["anova"], 2)),
        ("Target (arcmin)", TARGET),
    ]

    ws.append([])
    ws.append(["Metric", "Value"])
    style_header(ws, 4, 2)
    for name, value in rows:
        ws.append([name, value])
    last = 4 + len(rows)

    for r in range(5, last + 1):
        ws.cell(row=r, column=1).font = Font(size=10)
        ws.cell(row=r, column=2).alignment = Alignment(horizontal="left")

    ws.cell(row=last + 2, column=1,
            value="Next step: obtain measured data with experiments/measurement_plan.md, "
                  "then replace the Raw Data sheet wholesale. A modelled or synthetic "
                  "row must never be reported as measured.")
    ws.cell(row=last + 2, column=1).font = Font(italic=True, size=9)
    ws.merge_cells(start_row=last + 2, start_column=1,
                   end_row=last + 2, end_column=4)
    ws.cell(row=last + 2, column=1).alignment = Alignment(wrap_text=True)
    ws.row_dimensions[last + 2].height = 30

    autosize(ws, {1: 42, 2: 34, 3: 20, 4: 20})


def _fmt_p(anova: dict, index: int) -> str:
    term = anova["terms"][index]
    p = term["p"]
    if p is None:
        return "—"
    return f"p = {p:.2e} ({'significant' if p < 0.05 else 'not significant'})"


def main() -> None:
    if not CSV.exists():
        sys.exit(f"missing {CSV}; run experiments/simulate_v3.py first")
    if not ANOVA.exists():
        sys.exit(f"missing {ANOVA}; run experiments/analyze_v3.py first")

    df = pd.read_csv(CSV)
    data = json.loads(ANOVA.read_text())
    if data.get("data_source") != "synthetic":
        sys.exit("refusing to build: ANOVA JSON is not marked synthetic")

    wb = Workbook()
    sheet_raw(wb, df)
    sheet_summary(wb, data["sensitivity_analysis"]["group_means"])
    sheet_anova(wb, data)
    sheet_cost(wb)
    sheet_dashboard(wb, df, data)

    # a table makes the 270 rows filterable in Excel without extra work
    wb["Raw Data"].tables.add(Table(
        displayName="RawData",
        ref=f"A1:{get_column_letter(len(df.columns))}{len(df) + 1}"))
    wb["Raw Data"].tables["RawData"].tableStyleInfo = TableStyleInfo(
        showRowStripes=False)   # stripes would fight the yellow provenance fill

    wb.save(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")
    for ws in wb.worksheets:
        print(f"  {ws.title:14s} {ws.max_row:4d} rows × {ws.max_column} cols, "
              f"{len(ws.conditional_formatting._cf_rules)} CF ranges")


if __name__ == "__main__":
    main()
