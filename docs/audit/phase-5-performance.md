# Phase 5 performance

Measured in this environment (not a dedicated benchmark lab).

## Backend

| Check | Observation |
| --- | --- |
| `GET /api/v1/health` | Integration client returns 200; no dedicated latency harness re-run in Phase 5 |
| Research profile page | Slice + filter of 3960-row Parquet |
| Combined grid | Reads the 242k-row file, filters in memory, returns ≤ 121 cells | 
| Artifact download | `FileResponse` of the confined file |

The combined endpoint does **not** send 242,000 rows to the browser. It is still the heaviest research read because it opens the full observations file per request.

## Frontend

| Check | Observation |
| --- | --- |
| Production JS | 308.59 kB (95.95 kB gzip) after Phase 5 build |
| CSS | 4.54 kB (1.82 kB gzip) |
| Polling | Jobs only, 2 s, while non-terminal |

## Rate limit / jobs

One global running scientific job. Mutation limiter is a process-lifetime counter (30).
