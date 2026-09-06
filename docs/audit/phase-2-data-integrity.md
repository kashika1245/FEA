# Phase 2 Data Integrity

Generated from executed artefacts. Command: inspection of `data/experiments/paper-a.phase2.v1/` after `scripts/run_phase2.py --experiment-id paper-a.phase2.v1`.

| Check | Result | Source |
|-------|--------|--------|
| Phase 1 hash unchanged | `a78de261b1686363ed6d830cd370b763800da657bce0991047fe43fb9504e99e` | `sha256_file(dataset.parquet)` |
| Phase 1 hash matches freeze | yes | `docs/audit/dataset-quality-report.md` |
| Variable-wise rows | 132000 | `extrapolation/observations.parquet` |
| Expected variable-wise | 132000 | `manifest.json` |
| Combined rows | 242000 | `combined/observations.parquet` |
| Expected combined | 242000 | `manifest.json` |
| Duplicate variable-wise keys | 0 | `(seed, anchor_id, variable, direction, delta)` |
| Dataset hash on every observation | frozen Phase 1 hash | observations column |
| Distinct model hashes | 5 | observations column |
| Anchors | 100 | `anchors/anchors.parquet` |
| F at δ = 0.50 lower / upper | −3.5 / 14.5 kN | raw observations |
| Failures fabricated as zeros | none | `failures/` empty of silent fills |
| Normalization hash | `ff0c27f6faf4f812e49f8e165cb4584cd310d47b83c743c35280d75a97360327` | `normalization.json`, manifest |

Raw observation hash (`observations.parquet`): `ab32fafe57fa83d5b78c21be86c191d195fb317a2499be38cf91ddc3b1818886` from `scripts/audit_phase2.py`.
