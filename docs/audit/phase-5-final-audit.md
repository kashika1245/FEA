# Phase 5 final audit

**Verdict:** see `docs/audit/phase-5-release-readiness.md`.  
**Date of independent checks:** 2026-09-06.

This file is the index. Evidence classes:

| Label | Meaning |
| --- | --- |
| Verified | Executed or inspected in Phase 5 |
| Reported | Claimed by Phase 1–4 documents; not treated as proof |
| Assumed | Not independently established |

## Data-flow map (inspected)

```text
canonical.py + FEM solver
  → dataset generator (PCG64, seed 20260905)
  → data/datasets/paper-a.phase1.v1-n10000-seed20260905/dataset.parquet
  → train-only normalization + MLP training
  → interpolation JSON
  → interpolation_test anchors
  → variable-wise / combined FEM+MLP evaluation
  → profiles / thresholds / asymmetry Parquet
  → experiment manifest
  → AppServices + FastAPI /api/v1/research/*
  → frontend pages (read-only transforms)
  → researcher
```

## Phase 5 defects found and fixed

1. **Profiles 5% overview treated missing threshold cells as “Not reached”.** The page requested thresholds filtered by the selected variable *and* response, then painted a 12×3 matrix. Unmatched cells were labeled as scientific non-crossings. Fixed: fetch seed-scoped rows, distinguish `missing` vs `not_reached`.
2. **IQR band drawn on absolute/signed axes.** Stored q1/q3 are relative-error quartiles. The band is now shown only for the relative-error metric.
3. **Free-form seed inputs** could request a seed with no stored rows and look like an empty scientific result. Replaced with the frozen five-seed list.
4. **Unused `httpx2` dev dependency** (no imports). Removed.
5. **Root `.gitignore` omitted frontend build debris** (covered only by `frontend/.gitignore`). Root ignore updated.
6. **Methodology omitted several required limitations** (A3+F scope, negative F, non-generalization). Added.

`paper-a.phase2.v1` was **not** regenerated.

## Git

Verified: a `.git` directory exists and `git status` shows **no commits** (`No commits yet on master`; entire tree untracked). Git commit = `null`.

## Iterations actually performed

1. Repository map and git hygiene  
2. Independent Phase 1 parquet hash  
3. Independent Phase 2 counts and observation hash  
4. Split/schema integrity  
5. Leakage (train-only norm, interpolation_test anchors)  
6. Normalization refit vs stored hash  
7. Small-n dataset seed reproduction  
8. Checkpoint format (npz/JSON, no pickle)  
9. `verify_fea` numerical checks  
10. Combined/variable isolation sampling  
11. Profile `n_anchors` and finite metrics  
12. Threshold recomputation vs stored crossings  
13. Asymmetry threshold-row differences  
14. Combined vs isolated A3/F observation  
15. Manifest ↔ file hash consistency  
16. API CORS allow-list tests  
17. Artifact confinement / traversal tests  
18. Job idempotency, concurrency, stale restart tests  
19. Frontend threshold-matrix defect fix  
20. IQR-band metric guard  
21. Seed selectors + heading/label E2E  
22. Bundle-size measurement  
23. Playwright E2E (6) + live overview/profiles/interpolation  
24. Removal of unused `httpx2`  
25. Claim audit against runtime JSON  
26. Final-results package by hash reference  
27. Researcher copy on experiments vs `paper-a.phase2.v1`  
28. Documentation set under `docs/audit/phase-5-*.md`
