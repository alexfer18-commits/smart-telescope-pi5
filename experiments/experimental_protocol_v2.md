# Experimental protocol v2

One episode is one complete pointing task: slew, capture, solve, correct,
verify. The protocol below is the one the paper's statistics assume; deviating
from it invalidates the comparison.

## The 90 episodes

| Factor | Levels | Notes |
|---|---|---|
| Inference substrate | E1 CPU, E2 Hailo-8L, E3 Cloud | the independent variable |
| Repetition | 30 per substrate | 90 total |
| Target | 30 objects, drawn without replacement | fixed across substrates |
| Controller | PID, MPC | reduced design: 10 episodes each, then the winner takes 30 |

Randomise substrate order within each block. Precede every block with a
15-minute thermal soak. Record ambient temperature and the verification solve's
FWHM as blocking covariates — do not randomise them, they are not controllable
and pretending otherwise hides the confound.

## Per-episode procedure

1. Park, then slew to the target using the mount model's prediction.
2. Capture 2 s at gain 0, save the raw frame.
3. Solve with the substrate under test; log `latency_ms`, `n_stars`,
   `error_arcmin`, `source`.
4. Apply the residual through the controller; settle 3 s.
5. Capture and solve with the *verification* solver (never the experimental one).
6. Log the angular separation between commanded and verified position.
7. Power: integrate the INA219 samples across the episode, in Wh.

## Log schema

`experiments/episode_schema.json` is the contract. One JSON file per episode,
plus a session index. Files are append-only; a re-run gets a new `episode_id`,
never an edit.

## What makes a run invalid

- Verification solver == experimental solver (a biased model hides itself).
- Fewer than 6 detected stars in the verification frame.
- Seeing worse than 4 arcsec FWHM (the solve becomes noise-dominated).
- Network loss during an E3 episode that is not logged as such. Log it, keep it,
  and analyse it separately: degraded mode is a result, not an accident.

## Data Provenance

This section exists because the repository currently contains two kinds of
numbers that look alike and must never be confused.

**What is synthetic today.** Every number in `data/benchmark_results.json` — the
latency percentiles, throughput, energy, and cost for all four backends — comes
from a documented latency model (`LATENCY_MODEL_MS` in
`benchmarks/compare_inference.py`), not from a measurement. No inference runtime
was installed on the machine that produced them. Each row carries
`"source": "synthetic"` and `"energy_source": "modelled"`, and
`figures/benchmark_comparison.pdf` prints a red warning when any row is
synthetic. These numbers exist to exercise the harness and to size the
experiment; they are not evidence.

**What replaces them.** `benchmarks/run_real_measurements.py` runs on the
Raspberry Pi 5 with a real quantized model and, when the INA219 shunt is fitted,
real power. It writes `data/real_measurements.json` with
`"source": "measured"`, the model's SHA-256, and the host. It has no synthetic
fallback: if a runtime, a model, or the shunt is missing it reports the row as
skipped or `null` and never estimates. The procedure, the install commands, the
acceptance thresholds, and the x86 HEF compilation steps are in
`experiments/measurement_plan.md`.

**The rule for the manuscript.** Every table and every figure states its
provenance. `measured` values come only from `data/real_measurements.json`;
`modelled` values are labelled as such in the caption, never in a footnote. A
row may not mix the two. The paper must be updated with the real numbers —
replacing the synthetic table in its entirety — before submission; if the E2
hardware is still unavailable at that point, the paper reports E1 and E3 as
measured and E2 as **not measured**, with the constraint stated in the
Experimental Design section. Reporting a modelled E2 row as if it were measured
is the one failure this section exists to prevent.

**Traceability.** Every run records the DFC version, the HailoRT version, the
model hash, the host, and the three repetitions. A number without those five
fields is not reproducible, and an irreproducible number does not go in the
paper.
