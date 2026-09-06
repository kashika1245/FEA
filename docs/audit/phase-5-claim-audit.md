# Phase 5 research-claim audit

Novelty framing that **must not** be upgraded:

> Extrapolation testing itself is not claimed as novel. Systematic variable-wise error-versus-distance profiles for this simple structural surrogate are **less explored**, not “never studied.”

Evidence is from `paper-a.phase2.v1` as independently read in Phase 5 (`docs/audit/phase-5-audit-runtime.json`). Seed cited below: `20260905` unless noted.

| Intended claim | Class | Evidence |
| --- | --- | --- |
| Extrapolation error depends on the variable being extrapolated | **SUPPORTED** | At δ = 0.50, median relative error (across directions/responses for that seed) ranges from ~0.60% (A5) to ~99% (F). A3 and A1 are the next largest area effects. |
| Extrapolation behaviour differs by response | **SUPPORTED** | At δ = 0.50 the same aggregation gives C ~1.24%, u_max ~0.77%, sigma_max ~0.70%. Differences are real but smaller than the F-versus-area contrast. |
| Lower and upper extrapolation can be asymmetric | **SUPPORTED** | 9 threshold rows for this seed have different lower vs upper 5% or 10% crossings. Asymmetry Parquet stores upper−lower median RE; it is not forced to zero. |
| Combined A3+F can differ from isolated extrapolation | **SUPPORTED** (bounded) | Upper `sigma_max` median RE: isolated A3 at δ_A3=0.50, δ_F=0.00 ≈ 0.93%; joint δ_A3=δ_F=0.50 ≈ 3.07%. This is one grid, one pair of variables. |
| 5%/10% values are universal safety limits | **NOT SUPPORTED** | They are first observed grid crossings or `not reached`. |
| Profiles define a full validity domain | **NOT SUPPORTED** | One-at-a-time δ plus one A3+F slice. |
| Results generalize to other structures/architectures | **NOT SUPPORTED** | Single linear truss, one MLP. |
| Interpolation R² implies extrapolation trust | **NOT SUPPORTED** | Interpolation R² ≥ 0.9998 while F at δ=0.50 is ~99% median RE. |

## Additional observation (not a general claim)

F is the most extrapolation-sensitive input on this grid. Negative F is load reversal. Do not convert that observation into “force is always untrustworthy for all surrogates.”
