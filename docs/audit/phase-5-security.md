# Phase 5 security

## Findings fixed

- CORS `*` is dropped in `cors_origins_from_env` (verified by unit test).
- Unused `httpx2` removed.

## Verified controls

- Artifact IDs are opaque Base64 tokens; clients never pass filesystem paths.
- Relative paths reject `..`, absolute paths, and backslashes.
- Symlinked artefacts are not served.
- Experiment IDs must match a token regex; new writes must use `paper-a.phase3.*`.
- Frozen `paper-a.phase2.*` cannot be overwritten by jobs.
- Unhandled exceptions return a generic 500 body (no traceback).
- Validation errors do not echo raw payload dumps.
- Worker runs on a daemon thread, not the asyncio loop.
- Models are `.npz` + JSON, not pickle.
- No `eval`/`exec`/`os.system`/`shell=True` in application code. `model.eval()` is PyTorch eval mode.
- No `.env` or credential files present.

## Rate limiting

`RateLimiter` is a **process-lifetime counter**, not a sliding window. That is acceptable only on a trusted research host. Do not describe it as a sliding-window limiter.

## Authentication boundary

The API is an authenticated-network / trusted-host service. There are no user accounts, sessions, or per-researcher ACLs. Deploy behind a reverse proxy or equivalent access control. Phase 5 did not add a login system.

## Remaining assumptions

- Anyone who can reach the API can read artefacts and launch `paper-a.phase3.*` jobs.
- SQLite files under `data/app/` are local runtime state, not a multi-tenant store.
- CORS default is local Vite origins only.
