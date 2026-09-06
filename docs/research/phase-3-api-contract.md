# Phase 3 API contract

Base path: `/api/v1`. OpenAPI: `GET /openapi.json`.

Phase 3 assumes deployment behind an authenticated or otherwise trusted network boundary. There are no user accounts.

## Error envelope

```json
{"error": {"code": "EXPERIMENT_NOT_FOUND", "message": "Experiment does not exist.", "request_id": "..."}}
```

`X-Request-ID` is accepted when it matches `[A-Za-z0-9._-]{1,128}`; otherwise a hex token is generated. The same value is returned on every response.

No stack traces, filesystem roots, or Python exception reprs are returned to clients.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Process liveness |
| GET | `/ready` | Data root, SQLite, Phase 1 Parquet present |
| GET | `/experiments` | Paginated experiment list |
| POST | `/experiments` | Create `paper-a.phase3.*` directory |
| GET | `/experiments/{experiment_id}` | Manifest-backed detail |
| POST | `/experiments/{experiment_id}/run` | Queue a job |
| POST | `/experiments/{experiment_id}/cancel` | Cancel the active job |
| GET | `/jobs` | Paginated jobs |
| GET | `/jobs/{job_id}` | Job detail and stage progress |
| POST | `/jobs/{job_id}/cancel` | Cooperative cancel |
| GET | `/artifacts?experiment_id=` | Paginated artifact inventory |
| GET | `/artifacts/{artifact_id}` | Metadata |
| GET | `/artifacts/{artifact_id}/download` | Byte stream |
| GET | `/research/summary` | Stored experiment detail |
| GET | `/research/profiles` | Sliced `profiles/profiles.parquet` |
| GET | `/research/thresholds` | Sliced `profiles/thresholds.parquet` |
| GET | `/research/asymmetry` | Sliced `profiles/asymmetry.parquet` |
| GET | `/research/interpolation` | Stored `interpolation/seed-*.json` |

## Job types

`TRAIN_SURROGATE`, `INTERPOLATION_EVALUATION`, `EXTRAPOLATION`, `COMBINED_EXTRAPOLATION`, `PROFILE_BUILD`, `REPORT_BUILD`, `FULL_PHASE2_PIPELINE`.

Clients cannot override geometry, solver, architecture, grid, anchors, or dataset hash.

## Idempotency

`X-Idempotency-Key` returns the existing job if the key was already used. A second run on an experiment that already has a queued/running/cancel_requested job returns `409 JOB_ALREADY_RUNNING`. A completed job of the same type is returned instead of starting a destructive rerun. Frozen `paper-a.phase2.*` trees return `403 EXPERIMENT_IMMUTABLE`.

## Pagination

`offset` ≥ 0, `limit` 1–100 (research reads default 50). Ordering is deterministic (experiment id / created_at+job_id / artifact relative path).

## Artifact IDs

Opaque urlsafe-base64 tokens encoding `experiment_id:relative/posix/path`. Clients never supply filesystem paths.
