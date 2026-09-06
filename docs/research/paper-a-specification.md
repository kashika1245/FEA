# Paper A — Frozen Phase 1 Scientific Specification

**Paper:** Paper A — Structural Surrogate Extrapolation Profiling  
**Frozen title:** How Far Can a Structural Surrogate Be Trusted? Variable-Wise Extrapolation Profiles for Truss Response Models  
**Phase:** 1 — scientific foundation (specification, canonical structure, FEM oracle, dataset)  
**Status:** FROZEN for Phase 1  
**Freeze date:** 2026-09-05

This document is the Phase 1 source of truth. Downstream code, tests, datasets, and later phases must consume these definitions. Changing a frozen value requires an explicit specification revision, a geometry/solver version bump, and regeneration of affected artefacts.

Phase 1 does **not** implement the MLP surrogate, the extrapolation engine, the frontend, or a full production HTTP API.

---

## 1. Research question (context only)

How does prediction error evolve as a structural surrogate moves progressively beyond its training domain, and does that behaviour depend on:

1. which physical input variable is extrapolated,
2. which structural response is predicted,
3. whether extrapolation occurs below or above the training boundary,
4. whether multiple variables simultaneously leave the training domain?

Phase 1 produces the FEM reference dataset on which those questions will later be asked. It does not answer them.

---

## 2. Structural system

**System:** 10-bar planar truss  
**Nodes:** 6  
**Members:** 10  
**Kinematics:** 2D truss (axial members only; no bending stiffness)  
**Analysis:** linear-elastic static finite-element analysis, direct stiffness method

### 2.1 Geometry freeze decision

No numerical geometry existed in the repository at audit time.

The canonical geometry is therefore frozen here as the **literature-standard cantilever 10-bar planar truss** used throughout the structural-optimization literature (Venkayya / Haftka topology): two square bays, left-hand pinned support pair, free tip on the right.

Classic imperial bay length is 360 inches. The internal unit system is millimetres. The conversion is exact:

```
360 in × 25.4 mm/in = 9144 mm
```

Two bays therefore span `2 × 9144 = 18288 mm`. Height is one bay: `9144 mm`.

This is a documented unit conversion of a standard topology, not an invented alternative truss.

**Geometry version:** `tenbar.cantilever.v1`

### 2.2 Canonical nodes

Coordinates are in millimetres. Origin is the lower-left support. +x is right. +y is up.

| node_id | x (mm) | y (mm) | role |
|--------:|-------:|-------:|------|
| 1 | 18288.0 | 9144.0 | free (upper tip) |
| 2 | 18288.0 | 0.0 | free (lower tip; loaded) |
| 3 | 9144.0 | 9144.0 | free |
| 4 | 9144.0 | 0.0 | free |
| 5 | 0.0 | 9144.0 | pinned support |
| 6 | 0.0 | 0.0 | pinned support |

ASCII schematic (not to scale):

```
  y
  ^
  |  (5) paletted ---- (3) ---- (1)
  |   |  \          / |  \      / |
  |   |   \        /  |   \    /  |
  |   |    \      /   |    \  /   |
  |   |     \    /    |     \/    |
  |   |      \  /     |     /\    |
  |   |       \/      |    /  \   |
  |  (6) ----- (4) -------- (2)   F ↓
  +------------------------------> x
      pinned           free tip
```

### 2.3 Canonical members

Member `node_i`–`node_j` ordering is deterministic: `node_i < node_j` is **not** forced; the frozen connectivity below is the literature numbering and is used as written.

| member_id | node_i | node_j | description |
|----------:|-------:|-------:|-------------|
| 1 | 5 | 3 | top chord, left bay |
| 2 | 3 | 1 | top chord, right bay |
| 3 | 6 | 4 | bottom chord, left bay |
| 4 | 4 | 2 | bottom chord, right bay |
| 5 | 3 | 4 | vertical, middle |
| 6 | 1 | 2 | vertical, right |
| 7 | 5 | 4 | diagonal, left bay |
| 8 | 6 | 3 | diagonal, left bay |
| 9 | 3 | 2 | diagonal, right bay |
| 10 | 4 | 1 | diagonal, right bay |

Member lengths implied by the coordinates:

- chords and verticals: `9144 mm`
- diagonals: `9144 × √2 mm`

### 2.4 Supports

| support_id | node_id | restrain_ux | restrain_uy | prescribed displacement |
|-----------:|--------:|:-----------:|:-----------:|-------------------------|
| 1 | 5 | yes | yes | 0 |
| 2 | 6 | yes | yes | 0 |

Both supports are pinned. No prescribed non-zero displacement exists in Phase 1.

### 2.5 Load convention

The operator brief specifies a **single** applied-load parameter `F`.

**Frozen convention:**

- load location: node 2 (lower free tip)
- load direction: `(0, −1)` in the model coordinate frame (downward, parallel to −y)
- `F` is the **magnitude** of that concentrated force
- research-domain `F` is positive; the force vector contributed to the global load vector is `F * direction`
- there is no second concentrated load

This is a deliberate Phase 1 choice: the classic two-load 10-bar benchmark applies equal downward loads at nodes 2 and 4. Paper A’s input vector contains one scalar `F`, and the specification language is singular (“the applied load”, “load location”, “load direction”). A single tip load matches that input structure without introducing an undocumented second force.

**Load convention version:** `single-tip-downward.v1` (part of `tenbar.cantilever.v1`)

---

## 3. Unit system (internal, frozen)

One internally consistent system is used for all FEM arithmetic.

| Quantity | Internal unit | Symbol |
|----------|---------------|--------|
| length / coordinate / displacement | millimetre | mm |
| force / reaction / member axial force | newton | N |
| area | square millimetre | mm² |
| Young’s modulus | newton per square millimetre | N/mm² |
| stress | newton per square millimetre | N/mm² |
| compliance | newton-millimetre | N·mm |

**Named conversions (explicit, never implicit):**

```
1 GPa  = 1000 N/mm²     because 1 GPa = 1e9 N/m² and 1 N/mm² = 1 MPa = 1e6 N/m²
                    therefore 180 GPa = 180_000 N/mm²
1 kN   = 1000 N         therefore 1 kN = 1000 N and 10 kN = 10_000 N
```

**Storage convention for the published dataset artefact:**

| Column | Unit in artefact | Converted to internal |
|--------|------------------|------------------------|
| `A1`…`A10` | mm² | mm² (identity) |
| `E` | GPa | `E_gpa * 1000` → N/mm² |
| `F` | kN | `F_kn * 1000` → N |
| `u_max` | mm | mm (identity) |
| `sigma_max` | N/mm² | N/mm² (identity) |
| `C` | N·mm | N·mm (identity) |

The solver never stores `E` as GPa internally. Conversion happens at the parameter-ingestion boundary.

---

## 4. Input vector

```
x = [A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, E, F]
```

| Symbol | Meaning | Training domain | Domain unit |
|--------|---------|-----------------|-------------|
| `A_i` | cross-sectional area of member `i` | `[50, 100]` | mm² |
| `E` | Young’s modulus (uniform for all members) | `[180, 220]` | GPa |
| `F` | applied-load magnitude | `[1, 10]` | kN |

Areas may differ by member. `E` is a single scalar applied to every member. `F` is a single scalar.

---

## 5. Primary outputs

| Symbol | Definition | Unit |
|--------|------------|------|
| `u_max` | `max_i sqrt(u_x,i² + u_y,i²)` over all six nodes | mm |
| `sigma_max` | `max_e |σ_e|` over all ten members | N/mm² |
| `C` | `F_globalᵀ u` (global load vector times global displacement vector) | N·mm |

Signed member stress is retained at member level. The scalar `sigma_max` is the maximum **absolute** member stress. Absolute value is applied per member, then the maximum is taken. It is not the absolute value of the mean, nor max of signed stress.

`u_max` is a displacement **magnitude**. It is not max `|u_x|` and not max `|u_y|`.

---

## 6. Dataset (Phase 1 artefact)

| Item | Frozen value |
|------|----------------|
| Sample count `N` | 10_000 |
| Sampling | independent continuous uniform on each input, within the training domain |
| RNG | `numpy.random.Generator` with `PCG64`, master seed below, per-sample `SeedSequence.spawn` |
| Master random seed | `20260905` |
| Split (recorded now, unused by an MLP in Phase 1) | 70% train / 15% validation / 15% interpolation test |
| Split counts at `N = 10000` | 7000 / 1500 / 1500 |

Split assignment is a deterministic shuffle of sample IDs driven by a child seed independent of the per-sample parameter draws. It does not re-run FEM.

### 6.1 Row schema

| Column | Type | Unit |
|--------|------|------|
| `sample_id` | integer, `1 … N` | — |
| `split` | `{train, validation, interpolation_test}` | — |
| `A1`…`A10` | float64 | mm² |
| `E` | float64 | GPa |
| `F` | float64 | kN |
| `u_max` | float64 | mm |
| `sigma_max` | float64 | N/mm² |
| `C` | float64 | N·mm |

### 6.2 Uniform sampling interval

`numpy.random.Generator.uniform(low, high)` draws from `[low, high)`. For a continuous parameter and `N = 10000` the probability of landing on an endpoint is not scientifically meaningful. Dataset validation still requires `low ≤ x ≤ high`. This half-open convention is frozen and must not be “fixed” by rejection sampling that would change the seed stream.

---

## 7. Later-phase information (recorded, not implemented)

These values are frozen so Phase 2 does not invent them. Phase 1 **must not** implement the extrapolation engine.

| Item | Frozen value |
|------|----------------|
| Anchor configurations | 100 |
| Extrapolated variables | 12 (`A1`…`A10`, `E`, `F`) |
| Directions | lower and upper |
| Distance grid | `δ ∈ {0.00, 0.05, …, 0.50}` |

---

## 8. FEM formulation (normative)

**Solver version:** `planar-truss-direct-stiffness.v1`

### 8.1 Degrees of freedom

Two displacement DOFs per node: `u_x`, then `u_y`. Global DOF index for node `n` (1-based node IDs):

```
dof_ux(n) = 2 * (n - 1)
dof_uy(n) = 2 * (n - 1) + 1
```

Canonical model: 12 global DOFs, indices `0 … 11`. Constrained DOFs: node 5 and node 6, both directions → DOFs `8, 9, 10, 11`. Free DOFs: `0 … 7`.

### 8.2 Element stiffness

For member `e` connecting nodes `i` and `j`:

```
dx = x_j - x_i
dy = y_j - y_i
L  = sqrt(dx² + dy²)
c  = dx / L
s  = dy / L
k_e = (A_e E / L) *
      [[ c²,  c s, -c², -c s],
       [ c s,  s², -c s, -s²],
       [-c², -c s,  c²,  c s],
       [-c s, -s²,  c s,  s²]]
```

There is exactly one production implementation of this formula.

### 8.3 Assembly, boundary conditions, solve

- Assemble `K = Σ_e scatter(k_e)` into the 12×12 global matrix.
- Assemble `F_global` from the canonical load specification and magnitude `F`.
- Partition free (`f`) and constrained (`c`) DOFs. Constrained displacements are identically 0.
- Solve `K_ff u_f = F_f` with a dense linear solver (`numpy.linalg.solve`). Do not form `K⁻¹` explicitly.
- Reconstruct `u` with `u_c = 0`.

### 8.4 Reactions, member resultants, responses

```
R = K u - F_global
```

Global force equilibrium (applied loads plus reactions) must hold within tolerance, including the unconstrained moment equilibrium about the origin.

Axial extension of member `e`:

```
n_hat = (c, s)
u_i, u_j = nodal displacement vectors
δ_e = (u_j - u_i) · n_hat
N_e = (A_e E / L_e) * δ_e
σ_e = N_e / A_e
```

Tension is positive when the member elongates.

```
C = F_global · u
```

### 8.5 Failure policy

Invalid scientific inputs are rejected. They are not repaired. Non-finite values, non-positive areas, non-positive Young’s modulus, non-finite load, singular or near-singular `K_ff`, and invalid topology raise typed exceptions. Dataset generation records structured failures and does not write NaN/zero/fake responses into the primary dataset.

---

## 9. Numerical tolerances (frozen)

Tolerances are relative to double-precision direct stiffness on a 12-DOF system whose element stiffness scale is `A E / L ~ 10³ N/mm`. They are not loosened to make tests pass.

| Name | Value | Justification |
|------|------:|---------------|
| `symmetry_atol` | `1e-12` | `K` is assembled from analytically symmetric rank-1 updates; residual should be roundoff only. Compared as `‖K−Kᵀ‖_F ≤ max(symmetry_atol, symmetry_rtol * ‖K‖_F)`. |
| `symmetry_rtol` | `1e-14` | relative roundoff floor for a well-scaled dense matrix |
| `equilibrium_rtol` | `1e-8` | `‖K u − F_applied_and_reactions‖` is identically ~0 after `R = Ku−F`; the useful check is `‖K_ff u_f − F_f‖ / ‖F_f‖` and global `∑F + ∑R` |
| `equilibrium_force_rtol` | `1e-8` | relative to `‖F_global‖_2` |
| `equilibrium_moment_rtol` | `1e-8` | relative to `‖F_global‖_2 * L_ref` with `L_ref = 9144 mm` |
| `scaling_rtol` | `1e-8` | linear theory; discrepancy is solver roundoff, not modelling error |
| `reference_rtol` | `1e-8` | production vs independent reference on the same well-conditioned system |
| `reference_atol` | `1e-10` | absolute floor for near-zero entries |
| `condition_number_limit` | `1e12` | above this, the reduced system is treated as numerically singular for this application |
| `min_length_mm` | `1e-9` | lengths below this are zero-length members in double precision for this millimetre model |

---

## 10. Reproducibility

- Master seed `20260905`.
- Bit generator `PCG64`.
- Sample `i` (1-based) is drawn from `SeedSequence(master_seed).spawn(N)[i-1]`.
- Geometry, solver, and software versions are stored in dataset metadata.
- `configuration_hash` hashes the canonical JSON of scientific configuration plus geometry/topology/load convention (no timestamps).
- `dataset_hash` is SHA-256 of the final Parquet bytes.
- Git commit is recorded when a commit exists; the Phase 1 freeze began from an empty repository.

---

## 11. Storage

The scientific dataset artefact is **Apache Parquet** (`dataset.parquet`) plus a sidecar `metadata.json`.

Reasons:

- columnar, typed, efficient for later ML
- language-portable
- content-addressable by hashing file bytes
- no pickle / no arbitrary code execution

Checkpointing uses append-only `samples.jsonl` with `fsync`, not the final Parquet file, so a crash cannot leave a truncated Parquet footer.

---

## 12. Software versions (Phase 1)

| Identifier | Value |
|------------|--------|
| `software_version` | `0.1.0` |
| `geometry_version` | `tenbar.cantilever.v1` |
| `solver_version` | `planar-truss-direct-stiffness.v1` |
| `dataset_version` | `paper-a.phase1.v1` |
