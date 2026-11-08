# Paper paragraph — provenance (v3)

The following paragraph belongs in the Results section, immediately before the
first table of pointing errors. It is written to be quoted verbatim; the word
count is 98.

---

> All results in this section are synthetic. They were produced by
> `experiments/simulate_v3.py`, which draws pointing error, latency, and star
> counts from documented constants rather than from the instrument: every row of
> `data/simulated_results_v3.csv` carries `source = "synthetic"`, and the 90
> Hailo-8L rows carry `measurement_status = "not_measured"` because no compiled
> `.hef` exists without an x86 host. The accompanying analysis is therefore a
> rehearsal of the statistical pipeline — two-way ANOVA with Tukey HSD — and not
> evidence about the mount. The procedure that will replace it is specified in
> `experiments/measurement_plan.md`.

---

## When to delete it

Delete this paragraph only when *all* of the following are true:

1. `data/simulated_results_v3.csv` has been replaced by episode logs written by
   the real harness, and no row retains `source = "synthetic"`.
2. The ANOVA was re-run with `experiments/analyze_v3.py` on those logs, so
   `data/anova_results_v3.json` reports the same numbers as the paper.
3. `experiment_results_v3.xlsx` was rebuilt from the measured CSV.

If E2 is still unmeasured at that point, this paragraph is replaced by a
restriction sentence in the experimental-design section — E1 and E3 reported as
measured, E2 as not measured — not by silence.
