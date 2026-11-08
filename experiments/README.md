# Experiments

One episode is one complete pointing task: slew, capture, solve, correct, verify.
The protocol below is the one the paper's statistics assume; deviating from it
invalidates the comparison.

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
