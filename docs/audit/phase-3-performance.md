# Phase 3 performance

Measured 2026-09-05 on this machine with `TestClient` against the real `paper-a.phase2.v1` tree (n=20, after warmup implicit in the loop).

| Endpoint | p50 (ms) | max (ms) |
|----------|----------|----------|
| `GET /api/v1/health` | 0.68 | 8.51 |
| `GET /api/v1/experiments` | 81.54 | 119.03 |
| `GET /api/v1/experiments/paper-a.phase2.v1` | 140.46 | 140.94 |
| `GET /api/v1/research/summary` | 140.69 | 141.49 |
| `GET /api/v1/research/profiles` (variable=E, limit=20) | 1.91 | 23.18 |
| `GET /api/v1/research/thresholds` (limit=20) | 1.41 | 1.61 |
| `GET /api/v1/artifacts` | 70.33 | 70.61–71.61 |
| `GET /api/v1/artifacts/{id}` (manifest.json) | 70.24 | 70.84 |

## Interpretation

- Health does not touch FEM or training.
- Experiment detail / artifact listing hash files under 50 MB; that dominates ~70–140 ms.
- Profile/threshold reads use stored Parquet with filter + `slice`; they do not load the 132k/242k observation tables.
- Long jobs run on a background worker thread. HTTP handlers only enqueue or read state.

## Limits

Listing hashes every file on each detail request. Acceptable for the current tree; a metadata cache would be a later optimization, not a scientific change.
