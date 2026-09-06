# Phase 4 integration

The UI never talks to Parquet or scientific modules. It uses `/api/v1`.

CORS is optional and explicit (`PAPER_A_CORS_ORIGINS`). Local development prefers the Vite/preview proxy so the browser stays same-origin.

Integration-only backend changes (no scientific edits):

- CORS allow-list
- research list `limit` up to 2000 (a single variable/response/seed series is 110 rows)
- threshold/asymmetry filters
- `GET /api/v1/research/combined` aggregates stored combined observations with column projection
- job list returns `JobDetail` including stage progress

Frozen Phase 2 trees remain immutable.
