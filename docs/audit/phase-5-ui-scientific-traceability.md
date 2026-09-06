# Phase 5 UI scientific traceability

Every scientific number in the UI must come from a stored artefact. Phase 5 traced the live implementation.

| UI | Frontend transform | API | Artefact | Scientific meaning |
| --- | --- | --- | --- | --- |
| Overview hashes / row counts | `formatHash`, `formatNumber` | `GET /api/v1/research/summary` | `manifest.json` + Parquet row counts | Provenance, not a recomputed metric |
| Profile median / IQR | `seriesFor` sorts by δ; no smoothing | `GET /api/v1/research/profiles` | `profiles/profiles.parquet` | Anchor-wise median and quartiles of relative (or selected) error at each δ |
| 5% upper overview | `crossingOverview` / `crossingLabel` | `GET /api/v1/research/thresholds` (seed, limit 200) | `profiles/thresholds.parquet` | First observed 5% upper crossing; missing ≠ not reached |
| Threshold table | display only | `GET /api/v1/research/thresholds` | same | 5%/10% lower/upper strings or `not reached` |
| Asymmetry chart/table | maps stored lower/upper fields | `GET /api/v1/research/asymmetry` | `profiles/asymmetry.parquet` | Independent lower vs upper median RE; difference upper−lower |
| Combined heatmap | color scale on current max | `GET /api/v1/research/combined` | `combined/observations.parquet` | Median stored relative error at (δ_A3, δ_F) |
| Interpolation table | `formatNumber` / `formatPercent` | `GET /api/v1/research/interpolation` | `interpolation/seed-*.json` | Interpolation-test MAE/RMSE/RE/R² and gate |
| Artifacts list / download | opaque ID URL | `GET /api/v1/artifacts`, `/download` | files under the experiment dir | Bytes on disk |
| Job status | `StatusBadge` | `GET /api/v1/jobs` | SQLite `jobs` | Runtime, not Paper A evidence |

Hardcoded Paper A numeric results were not found in `frontend/src` production files. Frozen lists (`VARIABLES`, `RESPONSES`, `FROZEN_SEEDS`, default experiment id) are protocol identifiers, not measured errors.
