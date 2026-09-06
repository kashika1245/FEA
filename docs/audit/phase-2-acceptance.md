# Phase 2 Acceptance

Checked items were executed or inspected. Sources are named.

## Scientific

- [x] Phase 1 dataset validated (`load_and_validate_phase1_dataset`)
- [x] Phase 1 dataset hash unchanged (`a78de261…e99e`)
- [x] no data leakage (scientific leakage tests)
- [x] train-only normalization (7000-row fit; hash `ff0c27f6…0327`)
- [x] exact MLP 12-128-128-128-3 (`assert_architecture`)
- [x] five seeds trained and retained
- [x] interpolation evaluated on `interpolation_test`
- [x] interpolation gate passed for all five seeds
- [x] 100 anchors
- [x] 12 variables, lower and upper, δ = 0.00…0.50
- [x] actual FEM (`analyze`) and actual MLP
- [x] 132000 raw variable-wise observations
- [x] median/IQR profiles (3960 profile rows)
- [x] lower/upper comparison (`asymmetry.parquet`)
- [x] 5% and 10% first-observed crossings, including `not reached`
- [x] A3+F combined 242000 observations
- [x] no forced monotonicity
- [x] no fabricated scientific numbers

## Engineering

- [x] typed Phase 2 configuration (`configs/phase2.yaml`)
- [x] deterministic CPU training
- [x] resumable chunks (integration resume test)
- [x] batched MLP, FEM cache, chunk Parquet
- [x] structured JSON logs
- [x] NumPy weight archives, not pickle models
- [x] writes confined under `data/`

## Testing (executed)

- [x] `pytest` 77 collected tests passed (unit + scientific + integration)
- [x] `ruff check` passed
- [x] `mypy backend/app` passed
- [x] `scripts/audit_phase2.py` findings empty
- [x] Phase 1 hash regression passed

## Documentation

- [x] `docs/research/phase-2-method.md`
- [x] `docs/research/extrapolation-protocol.md`
- [x] experiment `manifest.json`
- [x] integrity, reproducibility, performance, scientific, and acceptance reports
