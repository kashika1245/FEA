# Phase 2 Method

**Paper:** How Far Can a Structural Surrogate Be Trusted? Variable-Wise Extrapolation Profiles for Truss Response Models  
**Phase:** 2 — MLP surrogate and extrapolation research engine  
**Version:** `paper-a.phase2.v1`  
**Software version:** `0.2.0`

This document describes the method that was implemented and executed. It does not claim that extrapolation testing itself is novel. The study develops a variable-wise extrapolation profiling procedure for a parametric truss surrogate and quantifies response-specific degradation relative to finite-element reference solutions.

## Phase 1 consumption

Phase 2 consumes the frozen Phase 1 artefact and does not modify geometry, topology, supports, loads, FEM formulation, sampling, splits, or response definitions.

| Item | Frozen value | Evidence |
|------|--------------|----------|
| Dataset | `paper-a.phase1.v1-n10000-seed20260905` | `data/datasets/.../metadata.json` |
| Dataset hash | `a78de261b1686363ed6d830cd370b763800da657bce0991047fe43fb9504e99e` | Phase 2 gate + `manifest.json` |
| Geometry | `tenbar.cantilever.v1` | Phase 1 specification |
| Solver | `planar-truss-direct-stiffness.v1` | `analyze()` |
| Splits | 7000 / 1500 / 1500 | integrity gate |

The Parquet file was absent from the working tree (gitignored) and was reconstructed from the completed Phase 1 `samples.jsonl` using the Phase 1 writer. The reconstructed hash matched the frozen hash exactly.

## Surrogate

Architecture (frozen): `12 → Dense(128) → ReLU → Dense(128) → ReLU → Dense(128) → ReLU → Dense(3)`.

- Loss: MSE on z-scored outputs
- Optimizer: Adam, learning rate `0.001`
- Batch size: 128
- Max epochs: 300
- Early stopping: validation MSE, patience 25
- Input normalization: train-only z-score
- Output scaling: train-only z-score, inverted before all reported errors
- Seeds: `20260905, 20260906, 20260907, 20260908, 20260909`
- Device: CPU, deterministic algorithms, one thread

Training uses the train split only. Early stopping and ranking use the validation split only.

## Model selection rule (predetermined)

**Retain all five seeds.** Extrapolation is reported for every seed.

A validation-only ranking (`lowest_validation_mse_only`) is stored for display order. Interpolation-test and extrapolation numbers are never used to select or discard a seed.

## Error definitions

Signed error: `prediction − FEA`  
Absolute error: `|prediction − FEA|`  
Relative error (%): `|prediction − FEA| / (|FEA| + ε) × 100`  
**ε = 1e-12** for every response and every experiment.

All reported metrics are in physical units: `u_max` mm, `sigma_max` N/mm², `C` N·mm.

## Interpolation competence gate (predetermined)

The gate is an in-domain competence check so that later degradation is interpretable. It is **not** an engineering safety limit.

A seed passes if and only if:

- all interpolation-test predictions are finite
- R² ≥ 0.90 for each response
- median relative error ≤ 10% for each response
- maximum relative error ≤ 100% for each response

All five seeds must pass before scientific extrapolation claims are written.

## Anchors

100 interpolation_test rows, selected by PCG64 without replacement, selection seed `20260905`, independent of model error. Stored in `anchors/anchors.parquet`.

## Variable-wise protocol

12 inputs × {lower, upper} × δ ∈ {0.00, 0.05, …, 0.50}.  
Exactly one coordinate changes; the others remain the anchor values.  
δ = 0 is the corresponding training boundary, not mean interpolation performance.  
Lower F at δ = 0.50 is −3.5 kN (load reversal). It is not clamped to zero.

Every point is evaluated with the Phase 1 `analyze()` oracle and the trained MLP.

## Profiles and thresholds

Primary profile: median relative error versus δ, with Q1–Q3 across the 100 anchors, per seed.  
No monotonicity is forced. No curve is fitted through the grid.

5% and 10% crossings are the **first observed empirical threshold crossing** on the tested δ grid (`error ≥ threshold`). If none occurs in [0, 0.50], the result is `not reached`. These percentages are analysis conventions, not universal validity boundaries.

## Combined A3 + F

One controlled two-variable case: both A3 and F are moved on the same δ grid and both direction pairs. It does not characterize the full multidimensional extrapolation domain.

## Limitations

- one linear-static 10-bar benchmark
- synthetic FEM data
- one MLP architecture
- finite δ range
- empirical thresholds
- one-variable profiles do not define a multidimensional validity domain
- A3+F is one case study
- no universal surrogate validity boundary
