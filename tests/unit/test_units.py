from __future__ import annotations

import pytest

from app.scientific.config import load_default_scientific_config
from app.scientific.exceptions import InvalidParameterError
from app.scientific.units import (
    GPA_TO_N_PER_MM2,
    KN_TO_N,
    load_internal_to_kn,
    load_kn_to_internal,
    youngs_modulus_gpa_to_internal,
    youngs_modulus_internal_to_gpa,
)


def test_named_conversion_factors() -> None:
    assert GPA_TO_N_PER_MM2 == 1000.0
    assert KN_TO_N == 1000.0


def test_youngs_modulus_domain_edges() -> None:
    config = load_default_scientific_config()
    low = youngs_modulus_gpa_to_internal(config.parameter_domain.youngs_modulus_gpa.min)
    high = youngs_modulus_gpa_to_internal(config.parameter_domain.youngs_modulus_gpa.max)
    assert low == 180_000.0
    assert high == 220_000.0
    assert youngs_modulus_internal_to_gpa(low) == 180.0


def test_load_domain_edges() -> None:
    config = load_default_scientific_config()
    assert load_kn_to_internal(config.parameter_domain.load_kn.min) == 1000.0
    assert load_kn_to_internal(config.parameter_domain.load_kn.max) == 10_000.0
    assert load_internal_to_kn(10_000.0) == 10.0


def test_nan_rejected() -> None:
    with pytest.raises(InvalidParameterError):
        youngs_modulus_gpa_to_internal(float("nan"))
    with pytest.raises(InvalidParameterError):
        load_kn_to_internal(float("inf"))
