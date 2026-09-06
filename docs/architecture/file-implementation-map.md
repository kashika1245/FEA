# File Implementation Map — Paper A Phase 1

This map lists every **production** file intended for Phase 1. Test-only files are listed at the end. If a file is not listed, it should not exist in the scientific engine.

---

## Root / tooling

### `pyproject.toml`

- **Purpose:** package metadata, dependencies, tool configuration.
- **Responsibilities:** define `app` package under `backend/`; pin scientific and QA dependencies; configure ruff, mypy, pytest, coverage.
- **Dependencies:** none (manifest).
- **Public interfaces:** PEP 621 project table; `[project.optional-dependencies] dev`.
- **Algorithm:** none.
- **Invariants:** no secrets; no wildcard dependency pins that hide solver-relevant ABI changes for numpy/pyarrow.
- **Failure conditions:** install failure is an environment failure, not a scientific result.
- **Tests:** installation exercised by CI/local `pip install -e ".[dev]"`.
- **Performance:** irrelevant.
- **Security:** no URL dependencies; no post-install scripts.

### `Makefile`

- **Purpose:** stable operator commands (`format`, `lint`, `typecheck`, `test`, …).
- **Responsibilities:** wrap ruff/mypy/pytest/scripts with `PYTHONPATH=backend`.
- **Dependencies:** `.venv`.
- **Security:** no interpolation of untrusted paths into the shell beyond Make variables set in the file.

### `configs/scientific.yaml`

- **Purpose:** operator-visible frozen configuration.
- **Responsibilities:** seed, N, domains, tolerances, versions.
- **Invariants:** must match `docs/research/paper-a-specification.md`.
- **Security:** parsed as YAML → Pydantic; rejected if unknown fields or invalid ranges.

---

## `backend/app/scientific/`

### `exceptions.py`

- **Purpose:** typed scientific failures.
- **Public interfaces:** `ScientificError` and subclasses (`InvalidGeometryError`, `InvalidMaterialError`, `InvalidLoadError`, `InvalidTopologyError`, `InvalidParameterError`, `FEASolverError`, `SingularStructureError`, `NumericalStabilityError`, `DatasetError`, `CheckpointError`, `StorageSecurityError`).
- **Invariants:** never used to swallow errors; messages contain diagnostic numbers, not secrets.
- **Tests:** `tests/unit/` invalid-input tests.

### `units.py`

- **Purpose:** unit labels and explicit conversions.
- **Public interfaces:** `UnitSystem`, `GPA_TO_N_PER_MM2`, `KN_TO_N`, `youngs_modulus_gpa_to_internal`, `load_kn_to_internal`, and inverse helpers for dataset export.
- **Algorithm:** multiply by frozen named factors.
- **Invariants:** `180 GPa → 180000 N/mm²`; `1 kN → 1000 N`.
- **Tests:** `tests/unit/test_units.py`.

### `config.py`

- **Purpose:** strongly typed scientific configuration.
- **Public interfaces:** `ScientificConfig`, `load_scientific_config(path)`.
- **Dependencies:** pydantic, yaml, `units`, `exceptions`.
- **Invariants:** domain bounds, split fractions sum to 1, positive N, documented tolerances.
- **Failure conditions:** missing file, extra YAML keys, invalid bounds.
- **Security:** path must be a regular file; YAML loaded with `safe_load`.

### `geometry.py`

- **Purpose:** `Node` and coordinate validation.
- **Public interfaces:** `Node`.
- **Invariants:** finite coordinates, positive integer `node_id`.

### `topology.py`

- **Purpose:** `Member`, `Support`, `LoadSpec`.
- **Invariants:** member endpoints distinct; support/load node IDs are identifiers only (existence checked in the model).

### `model.py`

- **Purpose:** immutable `TrussModel` aggregate and validation.
- **Public interfaces:** `TrussModel`, `dof_ux`, `dof_uy`, `geometry_quantities`.
- **Algorithm:** validate uniqueness, references, lengths; deterministic sort by IDs; precompute `L, c, s` and DOF maps.
- **Failure conditions:** invalid topology/geometry as listed in the specification.
- **Tests:** `tests/unit/test_geometry.py`, `test_topology.py`.

### `canonical.py`

- **Purpose:** the single canonical 10-bar factory.
- **Public interfaces:** `canonical_ten_bar_truss()`, `GEOMETRY_VERSION`.
- **Invariants:** exactly 6 nodes, 10 members, pinned nodes 5 and 6, load at node 2 direction `(0, −1)`, coordinates as frozen.
- **Tests:** `tests/unit/test_geometry.py`, `test_topology.py`.

### `parameters.py`

- **Purpose:** `StructuralParameters` in internal units, with validation.
- **Public interfaces:** `StructuralParameters.from_paper_units(...)`.
- **Failure conditions:** non-finite, non-positive area/E; non-finite F; wrong member count.

### `responses.py`

- **Purpose:** member resultants and scalar paper outputs; `StructuralResult`.
- **Algorithm:** axial extension dot product; `N = (AE/L) δ`; `σ = N/A`; `u_max`; `sigma_max`; `C = F·u`.
- **Invariants:** `sigma_max = max |σ_e|`; `u_max` is magnitude.

### `reproducibility.py`

- **Purpose:** hashing, git commit discovery, canonical JSON.
- **Public interfaces:** `sha256_bytes`, `sha256_file`, `canonical_json_bytes`, `configuration_hash`, `git_commit_or_none`.
- **Algorithm:** SHA-256; JSON with sorted keys and no NaN.
- **Security:** git invocation is fixed argv, never user-interpolated; failure → `None`.

---

## `backend/app/scientific/fem/`

### `element.py`

- **Purpose:** sole production element stiffness.
- **Public interfaces:** `element_stiffness(c, s, axial_stiffness) → (4,4) ndarray`.
- **Algorithm:** `k = (AE/L) * outer-structure of [c,s,-c,-s]`.
- **Invariants:** symmetry; finite entries.

### `assembly.py`

- **Purpose:** global `K` and `F`.
- **Public interfaces:** `assemble_global_stiffness`, `assemble_load_vector`.
- **Invariants:** `K` symmetric within tolerance; load only at configured DOFs.

### `boundary.py`

- **Purpose:** free/constrained partition.
- **Public interfaces:** `partition_system(K, F, model) → ReducedSystem`.
- **Algorithm:** Boolean masks from supports; slice `K_ff`, `F_f`.
- **Failure conditions:** no free DOFs; constrained DOF not in range.

### `solver.py`

- **Purpose:** `solve_displacements`, public `analyze()`.
- **Algorithm:** condition-number guard; `numpy.linalg.solve`; reconstruct full `u`.
- **Failure conditions:** `LinAlgError`, non-finite, `cond > limit`.
- **Performance:** reuse precomputed geometry quantities from the model.

### `reactions.py`

- **Purpose:** `R = K u − F`; equilibrium tests.
- **Invariants:** sum of applied forces and reactions ≈ 0 in x and y; moment about origin ≈ 0.

### `validation.py`

- **Purpose:** post-solve numerical validation used by `analyze()` and tests.
- **Public interfaces:** `validate_solved_system(...)`.

---

## `backend/app/scientific/dataset/`

### `sampling.py`

- **Purpose:** deterministic uniform draws in paper units.
- **Public interfaces:** `draw_parameters(sample_id, n_samples, seed, domain)`.
- **Algorithm:** `PCG64(SeedSequence(seed).spawn(n)[sample_id-1])`.
- **Invariants:** each component inside the closed domain for validation (`uniform` is half-open at draw time).

### `schema.py`

- **Purpose:** `DatasetRow` and column order.
- **Invariants:** 10 area columns; units documented on the model.

### `checkpoint.py`

- **Purpose:** resumable JSONL writes.
- **Public interfaces:** `CheckpointStore`.
- **Algorithm:** append line, flush, fsync; recover by reading complete lines only.
- **Failure conditions:** corrupt last line discarded only if incomplete (no newline); complete rows never rewritten.
- **Security:** directory confined under `data/`.

### `storage.py`

- **Purpose:** Parquet write/read; path confinement.
- **Security:** `StorageSecurityError` if resolved path escapes the data root.

### `metadata.py`

- **Purpose:** `DatasetMetadata` schema and hash linkage.

### `validation.py`

- **Purpose:** dataset quality checks and report dataclass.

### `generator.py`

- **Purpose:** `generate_dataset(config, output_dir, ...)`.
- **Algorithm:** resume-aware loop; FEM; validate; persist; finalize parquet + hashes.
- **Logging:** dataset id, stage, completed/total, elapsed, failure count — no arrays.
- **Failure conditions:** in-domain FEM failure aborts the primary 10k generation.

---

## Scripts

| File | Purpose |
|------|---------|
| `scripts/verify_fea.py` | run canonical analysis + invariant checks |
| `scripts/generate_dataset.py` | generate or resume a dataset |
| `scripts/verify_reproducibility.py` | twice-generate small N and compare |
| `scripts/audit_dataset.py` | write `docs/audit/dataset-quality-report.md` from artefacts |

---

## Tests (not production physics)

| File | Purpose |
|------|---------|
| `tests/unit/test_*.py` | geometry, units, element, assembly, BCs, sampling, responses |
| `tests/scientific/reference_solver.py` | independent FEM |
| `tests/scientific/test_fea_reference.py` | production vs reference vs analytics |
| `tests/scientific/test_equilibrium.py` | `Ku` and reaction equilibrium |
| `tests/scientific/test_scaling.py` | load / area / modulus scaling |
| `tests/scientific/test_numerical_stability.py` | singularity and edge bounds |
| `tests/scientific/test_dataset_integrity.py` | hashes, bounds, schema |
| `tests/integration/test_dataset_generation.py` | N=10/50, checkpoint recovery |
| `tests/scientific/test_properties.py` | hypothesis properties |

---

## Documentation

| File | Purpose |
|------|---------|
| `docs/research/paper-a-specification.md` | frozen science |
| `docs/research/numerical-method.md` | FEM derivation as implemented |
| `docs/research/dataset-generation.md` | sampling, checkpoint, hash |
| `docs/architecture/current-state-audit.md` | empty-repo audit |
| `docs/architecture/target-scientific-architecture.md` | this architecture |
| `docs/audit/*` | generated quality / phase-1 reports |
