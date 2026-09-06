# Phase 5 data-leakage audit

Fresh check, not a copy of Phase 2’s PASS.

| Control | Result |
| --- | --- |
| Split IDs disjoint | Verified: no train/val/test `sample_id` overlap |
| Normalization train-only | Verified: refit on 7000 train rows; hash matches stored bundle; input means are not the interpolation_test means |
| Model selection | Verified in source: ranking uses validation MSE only; all five seeds retained |
| Anchors | Verified: 100 unique `source_sample_id` values, subset of interpolation_test, no train overlap |
| Extrapolation points | Verified: built from those anchors; one or two coordinates move |
| FEM reference | Verified: `analyze()` on the actual extrapolated coordinates; not a surrogate-as-oracle loop |
| Profile aggregation | Verified: grouped by model/seed/variable/direction/delta/response |
| Combined aggregation (API) | Verified: median over stored relative errors at (δ_A3, δ_F) after seed/direction filters |

No test statistics enter the scaler. The interpolation competence gate uses interpolation_test metrics **after** training; it can reject a run but does not retune weights on that split.
