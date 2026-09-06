"""Authoritative 2D truss element stiffness. This is the only production implementation."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from app.scientific.exceptions import (
    InvalidGeometryError,
    InvalidMaterialError,
    NumericalStabilityError,
)


def axial_stiffness(area_mm2: float, e_n_per_mm2: float, length_mm: float) -> float:
    """Return AE/L in N/mm."""

    if not np.isfinite(area_mm2) or area_mm2 <= 0.0:
        raise InvalidMaterialError(f"element area must be finite and positive, got {area_mm2}")
    if not np.isfinite(e_n_per_mm2) or e_n_per_mm2 <= 0.0:
        raise InvalidMaterialError(f"element E must be finite and positive, got {e_n_per_mm2}")
    if not np.isfinite(length_mm) or length_mm <= 0.0:
        raise InvalidGeometryError(f"element length must be finite and positive, got {length_mm}")
    value = (area_mm2 * e_n_per_mm2) / length_mm
    if not np.isfinite(value):
        raise NumericalStabilityError(f"non-finite axial stiffness AE/L={value}")
    return float(value)


def element_stiffness(
    cosine: float,
    sine: float,
    axial: float,
) -> npt.NDArray[np.float64]:
    """Return the 4x4 global-axis element stiffness.

    Mathematically equivalent to the standard expansion

        (AE/L) * [[c², cs, -c², -cs],
                  [cs, s², -cs, -s²],
                  [-c², -cs, c², cs],
                  [-cs, -s², cs, s²]]

    Implemented as ``axial * a aᵀ`` with ``a = [c, s, -c, -s]``, which is a single
    rank-1 formula, automatically symmetric, and not duplicated elsewhere.
    """

    if not np.isfinite(cosine) or not np.isfinite(sine):
        raise InvalidGeometryError(f"direction cosines must be finite, got c={cosine}, s={sine}")
    if not np.isfinite(axial) or axial <= 0.0:
        raise InvalidMaterialError(f"axial stiffness must be finite and positive, got {axial}")
    direction = np.array([cosine, sine, -cosine, -sine], dtype=np.float64)
    stiffness = axial * np.outer(direction, direction)
    if not np.all(np.isfinite(stiffness)):
        raise NumericalStabilityError("element stiffness contains non-finite entries")
    return stiffness
