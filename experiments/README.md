# Experiments

| File | What it is |
|---|---|
| `experimental_protocol_v2.md` | the 90-episode protocol, invalid-run rules, and **Data Provenance** |
| `measurement_plan.md` | hardware checklist, runtime install, real measurement run, x86 HEF compile |
| `episode_schema.json` | JSON Schema every episode log must satisfy |

Read the protocol before the plan: the plan explains how to measure, the
protocol explains what counts as a valid measurement.

Two numbers in this repository look alike and are not:

- `data/benchmark_results.json` — **synthetic**, a latency model. Exercises the
  harness. Never cited as a result.
- `data/real_measurements.json` — **measured** on the Pi 5 by
  `benchmarks/run_real_measurements.py`. This is the one the paper reports.
