# Phase 5 scientific integrity

## FEM — Verified

`make verify-fea` passed. Reported values include stiffness symmetry residual 0, reduced residual ~8.6e-12, condition number ~74.6. Equilibrium force/moment residuals are at numerical noise. Tolerances were not loosened.

Canonical geometry matches the frozen contract (6 nodes, 10 members, load on node 2, direction (0,−1)).

## Dataset — Verified

`load_and_validate_phase1_dataset` plus independent `sha256_file`:

```text
a78de261b1686363ed6d830cd370b763800da657bce0991047fe43fb9504e99e
```

10,000 rows; 7000 / 1500 / 1500; no split ID overlap.

## Surrogate — Verified (artefacts, not retrained)

Architecture, train-only z-score, five retained seeds, validation-only ranking rule are stored in config + manifest. Normalization independently refit on the train split only; hash:

```text
ff0c27f6faf4f812e49f8e165cb4584cd310d47b83c743c35280d75a97360327
```

Interpolation competence gate: all five seeds `passed_gate: true` (stored JSON). Interpolation R² on the 1500-point test split is ≥ 0.9998 for all responses/seeds. That is interpolation competence, not extrapolation trust.

## Extrapolation protocol — Verified

`extrapolated_value` is the Phase 2 definition: upper = xmax + δ·width, lower = xmin − δ·width. Sweeps change exactly one coordinate. Combined A3+F changes those two only. Sampled combined rows match expected A3/F and leave other inputs at the anchor.

## Profiles / IQR — Verified

Profiles group `(model_id, seed, variable, direction, delta, response)` and take quantiles **across anchors** (`n_anchors = 100` for every stored row). This is **anchor variability**, not seed variability. Seed-to-seed variation is a separate table (`reports/seed_variability_table.md`).

No monotonicity is imposed. Charts connect stored δ points only.

## Thresholds — Verified

`first_observed_crossing` walks δ ascending and returns the first grid median ≥ 5% or 10%, else `not reached`. Phase 5 recomputed every stored wide-threshold cell from `profiles.parquet`: **0 mismatches**.

## Combined — Verified

242,000 rows. API heatmap is median relative error of stored observations at each (δ_A3, δ_F) for one seed/direction pair. It is one two-variable probe, not a multidimensional validity domain.

## Units — Verified

`1 GPa = 1000 N/mm²`, `1 kN = 1000 N`. UI labels: u_max mm, sigma_max N/mm², C N·mm, A mm², E GPa, F kN.

## Failures — Verified

FEM/MLP evaluation exceptions are recorded then **re-raised**. Non-finite responses raise `ExperimentError`. Failures are not written as 0. The authoritative experiment `failures/` directory has no recorded failure files.
