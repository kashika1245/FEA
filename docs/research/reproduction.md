# Paper A reproduction guide

This is the Phase 5 reproduction path. It does **not** require undocumented manual edits.

## Software

- Python ≥ 3.11 (repository type-checked as 3.12)
- Node.js 20+ for the observatory UI
- Frozen configs: `configs/scientific.yaml`, `configs/phase2.yaml`

## Commands

```bash
make install
make verify-fea
make verify-reproducibility
make audit
make frontend-install
make frontend-test
```

Authoritative artefacts already exist locally:

```text
data/datasets/paper-a.phase1.v1-n10000-seed20260905/
data/experiments/paper-a.phase2.v1/
```

Do **not** regenerate the 10,000-sample dataset or `paper-a.phase2.v1` unless an integrity audit proves corruption. Regeneration is a scientific incident.

If those directories are absent, the frozen commands are:

```bash
make generate-dataset
make train-surrogate
make run-phase2
make audit-phase2
```

Seeds:

```text
dataset seed = 20260905 (PCG64, SeedSequence children per sample; split uses SeedSequence([seed, 1]))
surrogate seeds = 20260905 … 20260909
anchor selection seed = 20260905, interpolation_test only
```

## Expected hashes (independently verified in Phase 5)

| Artefact | SHA-256 |
| --- | --- |
| Phase 1 `dataset.parquet` | `a78de261b1686363ed6d830cd370b763800da657bce0991047fe43fb9504e99e` |
| Train-only normalization bundle | `ff0c27f6faf4f812e49f8e165cb4584cd310d47b83c743c35280d75a97360327` |
| Phase 2 configuration (manifest) | `a6052f26a82850d96b485bbff88f434af5d68e76b0bd63dcfcf5510839b163f1` |
| Phase 1 configuration | `449e9b7cfd50bcce39c9293bb5f12b63724d49ae44cc0cd427290b3e998e4752` |

Expected counts:

```text
10,000 dataset rows (7000 / 1500 / 1500)
132,000 variable-wise observations
242,000 combined A3+F observations
3,960 profile rows
180 wide threshold rows
```

Independent check:

```bash
make audit-phase5
```

## Observatory

```bash
make serve-api
make frontend-dev
```

Open `http://127.0.0.1:5173`. Default experiment is `paper-a.phase2.v1`. Phase 3 `tiny-*` jobs are integration artefacts, not the paper experiment.

## What is reproduced

1. Dataset — `scripts/generate_dataset.py`
2. Surrogate — `scripts/train_surrogate.py`
3. Interpolation — stored `interpolation/seed-*.json`
4. Extrapolation — `extrapolation/observations.parquet`
5. Profiles / thresholds / asymmetry — `profiles/*.parquet`
6. Combined A3+F — `combined/observations.parquet`
7. Figures / tables — `reports/` and `profiles` plot writers
8. API + UI — read stored artefacts only
