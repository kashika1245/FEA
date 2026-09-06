# Phase 3 forensic audit

## Architecture

Dependency direction is API → application → (infrastructure | scientific). `scripts/audit_phase3.py` confirmed scientific packages do not import `fastapi`, `starlette`, `uvicorn`, `app.api`, `app.application`, or `app.infrastructure`.

## Security

See `docs/audit/phase-3-security.md`. Traversal, absolute path, symlink, malformed ID, oversized pagination, and configuration-injection tests passed. No arbitrary file reader. No pickle model loading. No `shell=True`.

## Reliability

| Topic | Behavior |
|-------|----------|
| queued | Survives restart; worker claims FIFO |
| running at crash | `failed` / `STALE_AFTER_RESTART` |
| cancel_requested at crash | `cancelled` |
| completed/failed | Unchanged |
| concurrency | One global runner + experiment lock; second run is 409 |
| idempotency | `X-Idempotency-Key` returns the same job |
| cancellation | Cooperative between runner stages; queued jobs cancel immediately |

Scientific work that is mid-stage (for example a training loop) finishes that stage before cancel is observed. That boundary is intentional.

## Data

SQLite schema version 1: `jobs`, `experiment_locks`. WAL, busy timeout, thread lock. Scientific Parquet is not duplicated into SQLite.

## Performance

See `docs/audit/phase-3-performance.md`. Health < 1 ms p50. Research profile/threshold reads ~1–2 ms p50. Job work is off the event loop.

## Code scan

No `TODO` / `FIXME` / `NotImplemented` in `app.api`, `app.application`, or `app.infrastructure`. No hardcoded scientific result tables in the API. `model.eval()` is PyTorch.

## Testing

106 tests passed including Phase 1/2 regression, security units, API integration, restart, failure, cancel, and a real tiny full pipeline.

## Findings

None blocking.

Non-blocking: mutating rate limit is a process-lifetime counter; experiment detail re-hashes artefacts on each call; profile Parquet is filtered in memory after a projected/full-file read of the small profile table (3960 rows), never the 132k observation file.
