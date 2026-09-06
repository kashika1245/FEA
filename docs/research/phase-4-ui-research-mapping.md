# Phase 4 UI → API mapping

| View | Endpoint | Fields shown |
|------|----------|----------------|
| Overview | `GET /research/summary` | hashes, row counts, manifest seeds/geometry |
| Experiments | `GET /experiments` | id, status, hashes, artifact_count, immutable |
| Experiment detail | `GET /experiments/{id}`, `GET /jobs?experiment_id=` | manifest, counts, real job launch/cancel |
| Profiles | `GET /research/profiles` | stored median/IQR vs δ; optional direction overlay |
| Threshold heatmap/table | `GET /research/thresholds` | `lower_5` / `upper_5` / `lower_10` / `upper_10` strings |
| Asymmetry | `GET /research/asymmetry` | stored lower/upper medians and difference |
| Combined | `GET /research/combined` | median RE of stored A3+F observations per grid node |
| Interpolation | `GET /research/interpolation` | seed metrics and competence gate |
| Artifacts | `GET /artifacts`, download by opaque id | relative_path, media_type, size, sha256 |
| Jobs | `GET /jobs`, `POST /experiments`, `POST …/run`, cancel | SQLite job state |

Threshold “not reached” is displayed as text. It is never coerced to 0 or 0.50.
