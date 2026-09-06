# Phase 5 testing

Counts below were produced by commands executed in Phase 5. They are not copied from Phase 4.

## Executed

```text
make lint                 PASS (ruff)
make typecheck            PASS (mypy, 78 files)
make test (unit)          67 passed
make test-scientific      25 passed
make test-integration     15 passed
make verify-fea           validated: true
make verify-reproducibility  passed: true
make audit                wrote dataset-quality-report.md
make audit-phase2         phase1 hash match; observations hash recorded
make audit-phase3         no forbidden execution
make audit-phase5         passed: true
frontend lint             PASS
frontend typecheck        PASS
frontend unit/component   8 passed (5 files)
frontend build            PASS
frontend e2e              6 passed
```

## Warning filters

`pyproject.toml` uses `filterwarnings = ["error"]` plus two third-party ignores:

- `DeprecationWarning`: anyio `BlockingPortal` alias
- `StarletteDeprecationWarning`: httpx TestClient

These are TestClient/anyio deprecations, not scientific warnings. No project `warnings.filterwarnings` calls were found.

## Test quality

No `assert True` production tests. Phase 3 API tests hit the real FastAPI app and, for the tiny pipeline, the real engine. Frontend tests cover formatting, profile series order, and the threshold missing-vs-not-reached distinction. E2E talks to the real API and preview server (no mocked science).

## Weaknesses (non-blocking)

- Frontend has few component tests relative to page count.
- Combined isolation in `audit_phase5.py` samples every 2420th row, not every row.
- MLP retraining is not part of the default Phase 5 command set.
