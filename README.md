# Paper A scientific engine

**Paper:** How Far Can a Structural Surrogate Be Trusted? Variable-Wise Extrapolation Profiles for Truss Response Models

Phase 1 implements a canonical 10-bar planar truss, an actual linear-elastic FEM oracle, and a reproducible 10,000-sample reference dataset.

Phase 2 consumes that frozen dataset, trains a 12→128→128→128→3 MLP, and builds variable-wise extrapolation profiles against the Phase 1 FEM oracle.

Phase 3 exposes the frozen engine through a versioned research API, an experiment/artifact registry, and a persistent job worker. Scientific artefacts remain the source of truth.

Phase 4 is a research observatory UI. It displays stored artefacts; it does not recompute FEM or MLP inference in the browser.

Phase 5 is the forensic audit and release-readiness gate. It does not introduce a new scientific protocol.

Frozen specification: `docs/research/paper-a-specification.md`.  
Reproduction: `docs/research/reproduction.md`.  
Final results index: `docs/research/final-results/README.md`.

Phase 3/5 assume deployment behind an authenticated or otherwise trusted network boundary. The API does not implement user accounts.

## Setup

```bash
make install
make frontend-install
```

## Commands

```bash
make lint
make typecheck
make test
make test-scientific
make test-integration
make verify-fea
make verify-reproducibility
make audit
make audit-phase2
make audit-phase3
make audit-phase5
make serve-api
make frontend-dev
make frontend-test
make frontend-build
make frontend-e2e
```

Do not regenerate `paper-a.phase1.v1-n10000-seed20260905` or `paper-a.phase2.v1` unless an integrity audit proves a scientifically material defect.

Authoritative experiment: `paper-a.phase2.v1`.  
Test/pilot jobs: `paper-a.phase3.tiny-*` and `paper-a.phase2.pilot-*`.
