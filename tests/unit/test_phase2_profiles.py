from __future__ import annotations

import pyarrow as pa

from app.scientific.extrapolation.profiles import aggregate_profiles
from app.scientific.extrapolation.thresholds import first_observed_crossing


def test_profile_quantiles_ordered() -> None:
    table = pa.table(
        {
            "model_id": ["m"] * 4,
            "seed": [1] * 4,
            "variable": ["A3"] * 4,
            "direction": ["upper"] * 4,
            "delta": [0.1] * 4,
            "relative_u_max_error": [1.0, 2.0, 3.0, 4.0],
            "relative_sigma_max_error": [1.0, 2.0, 3.0, 4.0],
            "relative_C_error": [1.0, 2.0, 3.0, 4.0],
            "absolute_u_max_error": [1.0, 2.0, 3.0, 4.0],
            "absolute_sigma_max_error": [1.0, 2.0, 3.0, 4.0],
            "absolute_C_error": [1.0, 2.0, 3.0, 4.0],
            "signed_u_max_error": [1.0, 2.0, 3.0, 4.0],
            "signed_sigma_max_error": [1.0, 2.0, 3.0, 4.0],
            "signed_C_error": [1.0, 2.0, 3.0, 4.0],
        }
    )
    profiles = aggregate_profiles(table).to_pylist()
    for row in profiles:
        assert (
            row["q1_relative_error_pct"]
            <= row["median_relative_error_pct"]
            <= row["q3_relative_error_pct"]
        )


def test_threshold_first_grid_later_and_never() -> None:
    assert first_observed_crossing([0.0, 0.1], [5.0, 6.0], 5.0) == "0.00"
    assert first_observed_crossing([0.0, 0.1, 0.2], [1.0, 4.0, 10.0], 5.0) == "0.20"
    assert first_observed_crossing([0.0, 0.5], [1.0, 4.9], 5.0) == "not reached"
    assert first_observed_crossing([0.0, 0.3], [4.9, 5.0], 5.0) == "0.30"
