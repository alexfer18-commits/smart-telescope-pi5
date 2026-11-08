# Experiments

| File | What it is |
|---|---|
| `experimental_protocol_v3.md` | **current**: 3 × 3 design, MQTT topics, `source` column, primary vs sensitivity analysis |
| `experimental_protocol_v2.md` | previous single-architecture protocol; still the reference for the 90-episode design |
| `measurement_plan.md` | hardware checklist, runtime install, real measurement run, x86 HEF compile |
| `episode_schema.json` | JSON Schema every episode log must satisfy |
| `simulate_v3.py` | writes `data/simulated_results_v3.csv` — 270 rows, all `source = "synthetic"` |
| `analyze_v3.py` | two-way ANOVA + Tukey → `data/anova_results_v3.json`, `figures/anova_results_v3.pdf` |
| `build_excel_v3.py` | five-sheet workbook `experiment_results_v3.xlsx` |
| `paper_paragraph_v3.md` | the 98-word provenance paragraph, with the conditions for deleting it |

Read the protocol before the plan: the plan explains how to measure, the
protocol explains what counts as a valid measurement.

Pipeline, in order (`data/*.json` is git-ignored, the CSV and the xlsx are not):

```bash
.venv/bin/python experiments/simulate_v3.py       # 270 synthetic episodes
.venv/bin/python experiments/analyze_v3.py        # ANOVA + Tukey + figure
.venv/bin/python experiments/build_excel_v3.py    # workbook
```

Two numbers in this repository look alike and are not:

- `data/simulated_results_v3.csv` and `data/benchmark_results.json` —
  **synthetic**, from a documented model. They exercise the pipeline. Never
  cited as results.
- `data/real_measurements.json` — **measured** on the Pi 5 by
  `benchmarks/run_real_measurements.py`. This is the one the paper reports.
