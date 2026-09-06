# Phase 3 Architecture

## Layers

1. **`app.scientific`** — frozen FEM, dataset, MLP, extrapolation. No web imports.
2. **`app.infrastructure`** — SQLite, filesystem security, job worker thread, structured logs.
3. **`app.application`** — experiment registry, artifact catalog, job orchestration, research reads.
4. **`app.api`** — FastAPI `/api/v1`, typed schemas, error envelope, request IDs.

Dependency direction is strictly downward: API → application → (scientific | infrastructure). Scientific never depends on API.

## Persistence

SQLite at `data/app/phase3.sqlite` (overridable in tests):

- WAL mode
- schema version table
- transactional job transitions
- one global running-job slot (`max_running_jobs = 1`)
- experiment write lock

Scientific Parquet is **not** copied into SQLite.

## Execution

A background worker thread polls `queued` jobs and runs `Phase2Runner` **stage by stage** on a thread (not on the asyncio event loop). Progress is stage + optional unit counts. Cancellation is cooperative between stages.

## Immutability

IDs matching `paper-a.phase2.*` that already have a completed manifest are immutable. API jobs create `paper-a.phase3.*` trees.

## Authorization

Phase 3 assumes deployment behind a trusted network boundary. No user-account theater. Mutating routes are the same process as reads; the contract is documented so auth can be added later.

## Retention

Authoritative Phase 1/2 artefacts are never auto-deleted. Incomplete Phase 3 job trees may remain for audit; cleanup is operator-driven only.
