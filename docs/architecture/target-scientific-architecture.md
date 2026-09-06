# Target Scientific Architecture — Paper A Phase 1

## Purpose

Phase 1 is a scientific engine, not an application shell. The architecture exists to make the following pipeline auditable:

```
scientific configuration
    → sample valid structural parameters
    → construct the canonical 10-bar truss
    → assemble stiffness
    → apply boundary conditions
    → solve
    → reactions, member forces, stresses, u_max, sigma_max, C
    → validate
    → persist row + provenance
    → hash
```

Nothing in that chain is mocked.

## Package layout

Python import root is `backend/`. The installable package is `app`.

```
backend/app/scientific/          public scientific engine
backend/app/scientific/fem/      direct-stiffness implementation
backend/app/scientific/dataset/  sampling, generation, storage, hashing
tests/unit|scientific|integration
tests/scientific/reference_solver.py   test-only independent FEM
scripts/                           operator entry points
configs/scientific.yaml            frozen operator-visible config
data/datasets/                     generated artefacts (not source)
docs/                              specification and audits
```

The FEM package is **general planar truss**. The 6-node / 10-member constraint is enforced by the canonical factory and by dataset generation, not by hard-coding 12×12 literals inside the solver. Tests may construct smaller trusses for analytical checks.

## Module responsibilities

| Layer | Responsibility | Must not do |
|-------|----------------|-------------|
| `config` + YAML | domains, seed, N, tolerances, versions | FEM arithmetic |
| `units` | named conversions and unit labels | silent conversion |
| `canonical` | the one 10-bar geometry/topology/supports/load | scatter coordinates |
| `model` | immutable validated truss aggregate | solve |
| `fem.element` | one element-stiffness implementation | assembly / BCs |
| `fem.assembly` | global `K`, `F`, DOF map | linear solve |
| `fem.boundary` | free/constrained partition | guess supports |
| `fem.solver` | reduced solve, reconstruct `u`, `analyze()` | invert `K` |
| `fem.reactions` | `R = Ku − F`, equilibrium checks | display-only reactions |
| `responses` | member `N`, `σ`, `u_max`, `sigma_max`, `C` | alternative physics |
| `dataset.*` | sampling, checkpoint, parquet, hashes, quality | change FEM math |

## Data flow

```
ScientificConfig
        │
        ├── CanonicalTruss (geometry_version)
        │         └── TrussModel (nodes, members, supports, loads)
        │
        └── StructuralParameters (A[10], E, F)   [internal N, mm, N/mm²]
                    │
                    ▼
              fem.analyze()
                    │
                    ▼
            StructuralResult (immutable)
                    │
                    ▼
              DatasetRow (paper units) → JSONL checkpoint → Parquet + metadata.json
```

## Solver strategy

- Dense symmetric positive-definite solve on the reduced free-free block.
- Size is 8×8 for the canonical model; dense methods are appropriate.
- Singularity and excessive condition number raise `SingularStructureError` / `NumericalStabilityError`.
- Geometry-only quantities (`L`, `c`, `s`, DOF indices) are computed once per model and scaled by `A E / L` per analysis. This does not change the mathematics.

## Independent verification

`tests/scientific/reference_solver.py` is deliberately not a copy of the production 4×4 formula:

- 1D axial spring `k = AE/L`
- 2×4 transformation matrix
- `numpy.linalg.lstsq` instead of `solve`
- member force via strain → stress → force

It is test-only. Production never imports it.

## Dataset engine

- Per-sample RNG via `SeedSequence.spawn`, so resume does not replay a global stream.
- Append-only JSONL + `fsync` checkpoint.
- Primary artefact: Parquet. No pickle. No database duplication in Phase 1.
- Failed FEM evaluations are written to `failures.jsonl` and are **not** rows in the primary dataset.
- For the in-domain 10-bar with two pins, valid draws are expected to be non-singular. Any failure fails the Phase 1 generation job rather than silently dropping a sample and drawing a replacement (replacement would change `N` relative to the seed schedule). If a theoretical in-domain singularity occurred, generation must stop and report it.

## Security posture (Phase 1)

- Configuration is YAML parsed into Pydantic models, not `eval` / `exec` / pickle.
- Dataset output paths must resolve under `data/`.
- Logging never emits full matrices at INFO.
- No secrets, no network calls in the scientific engine.

## Out of scope until Phase 2+

- MLP training and inference
- extrapolation grids and error profiles
- HTTP API / frontend
- PostgreSQL copies of the 10k-row table
