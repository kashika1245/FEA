# Phase 3 Current State (pre-implementation audit)

Audited before any Phase 3 code was written. Phase 1 and Phase 2 remain frozen.

## Current architecture

The repository is a scientific package (`paper-a-scientific`) with:

- `backend/app/scientific/` — FEM oracle, dataset engine, MLP, extrapolation, reporting
- `configs/scientific.yaml` — frozen Phase 1 configuration
- `configs/phase2.yaml` — frozen Phase 2 configuration
- `scripts/` — CLI entry points that construct `Phase2Runner`
- `data/datasets/` — frozen Phase 1 Parquet
- `data/experiments/` — Phase 2 experiment trees
- `tests/` — unit / scientific / integration tests (77 passing at Phase 2 close)

There is **no** HTTP API, job queue, process registry, or application database.

## Reusable components (do not rewrite)

| Component | Location | Phase 3 use |
|-----------|----------|-------------|
| `Phase2Runner` | `experiments/runner.py` | Job execution target |
| `ExperimentManifest` | `experiments/manifest.py` | Authoritative completed-experiment metadata |
| `confine_under_data_root` | `dataset/storage.py` | Filesystem confinement primitive |
| `sha256_file` / `canonical_json_bytes` | `reproducibility.py` | Artifact integrity |
| Typed scientific errors | `exceptions.py`, `phase2_errors.py` | API error mapping |
| `load_and_validate_phase1_dataset` | `surrogate/dataset.py` | Readiness / integrity |
| Train-only normalization | `surrogate/normalization.py` | Unchanged |
| Safe model weights (`npz` + JSON) | `surrogate/checkpoints.py` | Artifact type, never pickle |
| Structured scientific logs | `surrogate/logging_util.py` | Complementary to app logs |

## Frozen artefacts (read-only)

| Item | Value / path |
|------|----------------|
| Phase 1 dataset hash | `a78de261b1686363ed6d830cd370b763800da657bce0991047fe43fb9504e99e` |
| Phase 2 experiment | `data/experiments/paper-a.phase2.v1/` |
| Normalization hash | `ff0c27f6faf4f812e49f8e165cb4584cd310d47b83c743c35280d75a97360327` |
| Observation counts | 132000 variable-wise, 242000 combined |
| Profile rows | 3960 |

`paper-a.phase2.v1`, `paper-a.phase2.pilot-tiny`, and `paper-a.phase2.pilot-10a` must not be overwritten by API-launched jobs.

## Infrastructure gaps

- No versioned HTTP API
- No experiment/job registry independent of the filesystem
- No asynchronous job execution or cancellation
- No restart-safe application state
- No request correlation or API error envelope
- No secure artifact download ID (clients must not pass filesystem paths)
- No pagination or resource limits
- Scientific CLI is the only execution path

## Proposed Phase 3 architecture

```
HTTP /api/v1
    → app.api (FastAPI, schemas, exception handlers)
        → app.application (experiment, artifact, job, research services)
            → app.scientific (unchanged)
            → app.infrastructure (SQLite, locks, worker, path security)
```

Scientific modules must not import FastAPI, SQLite, or HTTP types.

## Dependency justification

| Dependency | Why | Why not stdlib |
|------------|-----|----------------|
| FastAPI | Typed HTTP, OpenAPI, validation | stdlib `http.server` has no OpenAPI or Pydantic integration |
| Uvicorn | ASGI server for the FastAPI app | Required to run FastAPI |
| httpx (dev) | FastAPI/Starlette `TestClient` | Needed for API integration tests |
| SQLite (stdlib) | Job/registry persistence, WAL, transactions | No extra runtime dependency |

Rejected: PostgreSQL, Redis, Celery, Kafka. A single-process research backend with one expensive job at a time does not need them.

## Scientific / non-scientific boundary

- **Scientific source of truth:** Parquet, JSON manifests, `npz` weights, generated figures under `data/experiments/` and `data/datasets/`.
- **Application state:** job rows, lock rows, and registry bookkeeping in SQLite under `data/app/`.
- The API **reads** completed artefacts; it does **not** recompute 374k observations to serve GET requests.
- Mutating jobs may create **new** experiment IDs only. Frozen Phase 2 trees are immutable.
- Clients cannot override geometry, solver, architecture, δ grid, or dataset hash.
