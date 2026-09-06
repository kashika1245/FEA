# Scientific Audit — Phase 1

Performed after the 10,000-sample dataset existed. Items are marked PASS only if executed or inspected in this phase.

## Structure

| Item | Result | Evidence |
|------|--------|----------|
| Geometry | PASS | `canonical.py` bay 9144 mm; tests `test_geometry.py` |
| Topology | PASS | frozen 10 members; `test_topology.py` |
| Supports | PASS | nodes 5 and 6 pinned; constrained DOFs (8,9,10,11) |
| Load convention | PASS | node 2, direction (0, −1); `test_assembly.py` load vector |

## Mathematics

| Item | Result | Evidence |
|------|--------|----------|
| Element stiffness | PASS | rank-1 form vs expanded 4×4 in `test_element.py` |
| Assembly | PASS | 12×12, symmetry residual 0.0 on verify_fea case |
| Boundary conditions | PASS | elimination, not row-zeroing; `test_boundary.py` |
| Solve | PASS | `numpy.linalg.solve`; no explicit inverse |
| Reactions | PASS | `R = Ku − F`; global ∑F+∑R tested |
| Axial force / stress | PASS | single-bar N=F, σ=F/A; 10-bar vs reference |
| u_max | PASS | magnitude; single-bar node 2; 10-bar loaded tip |
| Compliance | PASS | C=F·u; load scaling C(2F)=4C(F) |

## Numerical

| Item | Result | Evidence |
|------|--------|----------|
| Symmetry | PASS | `\|\|K-K^T\|\|_F = 0` on canonical verify case |
| Equilibrium | PASS | reduced residual 8.64e-12; ∑Fy 1.82e-11 N |
| Scaling | PASS | load, area, modulus tests |
| Singularity | PASS | unconstrained bar raises `SingularStructureError` |
| Independent reference | PASS | production vs transform+lstsq+strain path |
| Invalid inputs | PASS | zero/negative/NaN/Inf area, E, F |

## Data

| Item | Result | Evidence |
|------|--------|----------|
| Sampling bounds | PASS | quality report; all Ai, E, F in domain |
| Seed | PASS | 20260905 |
| N=10000 | PASS | metadata sample_count 10000 |
| NaN/Inf/missing | PASS | all zero |
| Duplicates | PASS | 0 duplicate IDs and 0 duplicate input vectors |
| Failed FEA | PASS | 0 |
| Dataset hash | PASS | SHA-256 of Parquet bytes, recomputed match |
| Configuration hash | PASS | `449e9b7cfd50bcce39c9293bb5f12b63724d49ae44cc0cd427290b3e998e4752` |
| Reproducibility | PASS | N=20 twice identical; different seed differs |

## Independent reference comparison (executed)

Single-bar analytical: u=0.05 mm, σ=10 N/mm², C=50 N·mm, matched by production and reference.

Canonical heterogeneous 10-bar: production displacement, member forces, stresses, u_max, sigma_max, and C matched the reference solver within `reference_rtol=1e-8`.
