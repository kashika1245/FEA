from __future__ import annotations

from app.scientific.surrogate.config import load_default_phase2_config


def test_expected_counts_are_derived_from_configuration() -> None:
    config = load_default_phase2_config()
    variable_wise = config.expected_variable_wise_count(5, 100)
    assert variable_wise == (
        100
        * len(config.extrapolation.variables)
        * len(config.extrapolation.directions)
        * len(config.extrapolation.deltas)
        * 5
    )
    assert variable_wise == 132000
    combined = config.expected_combined_count(5, 100)
    assert combined == (
        100
        * len(config.combined.deltas_a3)
        * len(config.combined.deltas_f)
        * len(config.combined.directions_a3)
        * len(config.combined.directions_f)
        * 5
    )
