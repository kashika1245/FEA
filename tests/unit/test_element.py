from __future__ import annotations

import numpy as np
import pytest

from app.scientific.exceptions import InvalidGeometryError, InvalidMaterialError
from app.scientific.fem.element import axial_stiffness, element_stiffness


def test_element_stiffness_matches_expanded_formula() -> None:
    cosine, sine, axial = 0.6, 0.8, 12.5
    computed = element_stiffness(cosine, sine, axial)
    c, s, k = cosine, sine, axial
    expected = k * np.array(
        [
            [c * c, c * s, -c * c, -c * s],
            [c * s, s * s, -c * s, -s * s],
            [-c * c, -c * s, c * c, c * s],
            [-c * s, -s * s, c * s, s * s],
        ],
        dtype=np.float64,
    )
    np.testing.assert_allclose(computed, expected, rtol=0.0, atol=1e-15)


def test_element_stiffness_is_symmetric() -> None:
    matrix = element_stiffness(0.6, 0.8, 10.0)
    np.testing.assert_allclose(matrix, matrix.T, rtol=0.0, atol=1e-15)


def test_axial_stiffness_formula() -> None:
    assert axial_stiffness(100.0, 200_000.0, 1000.0) == 20_000.0


def test_zero_length_rejected() -> None:
    with pytest.raises(InvalidGeometryError):
        axial_stiffness(50.0, 200_000.0, 0.0)


def test_non_positive_area_and_modulus_rejected() -> None:
    with pytest.raises(InvalidMaterialError):
        axial_stiffness(0.0, 200_000.0, 1000.0)
    with pytest.raises(InvalidMaterialError):
        axial_stiffness(50.0, -1.0, 1000.0)
