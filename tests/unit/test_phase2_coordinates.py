from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from app.scientific.extrapolation.coordinates import distance_from_value, extrapolated_value


def test_delta_zero_hits_boundaries() -> None:
    assert extrapolated_value(50.0, 100.0, "upper", 0.0) == 100.0
    assert extrapolated_value(50.0, 100.0, "lower", 0.0) == 50.0


def test_published_extremes() -> None:
    assert extrapolated_value(50.0, 100.0, "upper", 0.5) == 125.0
    assert extrapolated_value(50.0, 100.0, "lower", 0.5) == 25.0
    assert extrapolated_value(180.0, 220.0, "upper", 0.5) == 240.0
    assert extrapolated_value(180.0, 220.0, "lower", 0.5) == 160.0
    assert extrapolated_value(1.0, 10.0, "upper", 0.5) == 14.5
    assert extrapolated_value(1.0, 10.0, "lower", 0.5) == -3.5


@given(st.floats(0.0, 0.5, allow_nan=False, allow_infinity=False, width=32))
def test_distance_is_non_negative_and_inverts(delta: float) -> None:
    upper = extrapolated_value(50.0, 100.0, "upper", delta)
    lower = extrapolated_value(50.0, 100.0, "lower", delta)
    recovered_upper = distance_from_value(50.0, 100.0, "upper", upper)
    recovered_lower = distance_from_value(50.0, 100.0, "lower", lower)
    assert recovered_upper >= -1e-12
    assert recovered_lower >= -1e-12
    if delta > 1e-12:
        assert upper > 100.0
        assert lower < 50.0
    assert abs(recovered_upper - delta) < 1e-6
