# Phase 2 Scientific Audit

## What was asked

How prediction error grows as a 12→128→128→128→3 MLP, trained only inside the Phase 1 box, is driven beyond that box one variable at a time (and once for A3+F together).

## What was actually executed

`scripts/run_phase2.py --experiment-id paper-a.phase2.v1` completed with status `completed` (`manifest.json`).

## Interpolation competence

All five seeds passed the predetermined gate. Seed `20260905` interpolation_test metrics from `interpolation/seed-20260905.json`:

| Response | R² | median RE % | MAE |
|----------|---:|------------:|----:|
| u_max | 0.999923 | 0.301 | 0.0949 mm |
| sigma_max | 0.999889 | 0.371 | 0.499 N/mm² |
| C | 0.999908 | 0.555 | 1006 N·mm |

Maximum interpolation relative error for C on that seed was 29.9%. That is below the catastrophic gate of 100% and is reported, not hidden.

## Variable-wise behaviour (seed 20260905, stored thresholds)

Generated table: `data/experiments/paper-a.phase2.v1/reports/threshold_table.md`.

Observed pattern, not a narrative:

- **E:** no 5% or 10% median-RE crossing on [0, 0.50] in either direction for any response.
- **Most areas other than A1/A3:** no crossing in this range.
- **A1 and A3, lower direction:** first observed 5% crossings appear at δ ∈ {0.30, 0.40, 0.45, 0.50} depending on response. Upper A1/A3 5% crossings were **not reached**.
- **F, lower direction:** C already has median RE ≥ 5% and ≥ 10% at δ = 0.00 (the lower training boundary). u_max and sigma_max cross 5% at δ = 0.05. This is a boundary observation, not “average interpolation.”
- **F, upper direction:** C crosses 5% at δ = 0.25 and 10% at δ = 0.45; u_max and sigma_max 5%/10% were **not reached** by δ = 0.50.

Lower versus upper is not symmetric. At δ = 0.50, seed `20260905`, `upper − lower` median relative error for F is about −187% (u_max), −183% (sigma_max), −193% (C): lower-F error is much larger. Source: `profiles/asymmetry.parquet`.

Profiles were not forced to be monotonic.

## Combined A3 + F (seed 20260905)

Median relative error across 100 anchors, from `combined/observations.parquet`:

| Corner | u_max | sigma_max | C |
|--------|------:|----------:|--:|
| δA3=0, δF=0, both upper | 0.170% | 0.308% | 0.485% |
| δA3=0.50, δF=0.50, both upper | 3.16% | 3.07% | 10.3% |
| δA3=0.50, δF=0.50, both lower | 159% | 135% | 173% |

Isolated-variable profiles do not describe this lower-lower corner. That is the purpose of the case study, not a claim about the full 12-D exterior.

## Novelty language

Documentation uses only the agreed framing. No “universal validity boundary” language appears in the generated threshold table.
