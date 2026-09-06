# Phase 5 data integrity

Independently counted from Parquet metadata / tables:

| Artefact | Rows | Expected |
| --- | ---: | ---: |
| Variable-wise observations | 132000 | 132000 |
| Combined observations | 242000 | 242000 |
| Profiles | 3960 | 3960 |
| Wide thresholds | 180 | 5×12×3 |
| Asymmetry | 1980 | 5×12×3×11 |

Profile relative/absolute columns used by the paper are finite. `n_anchors` is uniformly 100.

Manifest hashes match the files they name (dataset, normalization). Variable-wise observations hash from `audit_phase2`:

```text
ab32fafe57fa83d5b78c21be86c191d195fb317a2499be38cf91ddc3b1818886
```

## Classification of other experiment directories

| Path | Class |
| --- | --- |
| `paper-a.phase2.v1` | Keep — production research artefact |
| `paper-a.phase2.pilot-*` | Archive — pilot, not the paper |
| `paper-a.phase3.tiny-*` | Ignore/test — API/UI integration |
| `data/app/phase3.sqlite` | Ignore — runtime job DB |
| `data/app/phase3-perf.sqlite` | Ignore — performance probe DB |
| `data/validation/repro-*` | Ignore — reproducibility scratch |

Phase 3/4 experiments must not be cited as Paper A results.

## Missing data

Threshold string `not reached` is stored and distinct from numeric δ. UI now also distinguishes **no stored row** (filter/pagination miss) from `not reached`.
