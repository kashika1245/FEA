"""Internal unit system and explicit conversions.

Internal FEM arithmetic uses millimetres, newtons, and N/mm² exclusively.
Paper-facing parameters E (GPa) and F (kN) are converted only at the boundary.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.scientific.exceptions import InvalidParameterError

# 1 GPa = 1e9 N/m² and 1 N/mm² = 1 MPa = 1e6 N/m², so 1 GPa = 1000 N/mm².
GPA_TO_N_PER_MM2: float = 1000.0
# 1 kN = 1000 N.
KN_TO_N: float = 1000.0


@dataclass(frozen=True, slots=True)
class UnitSystem:
    """Labels for the internal unit system. Values are documentation, not conversion factors."""

    length: str = "mm"
    force: str = "N"
    area: str = "mm^2"
    youngs_modulus: str = "N/mm^2"
    stress: str = "N/mm^2"
    displacement: str = "mm"
    compliance: str = "N*mm"
    paper_youngs_modulus: str = "GPa"
    paper_load: str = "kN"


INTERNAL_UNITS = UnitSystem()


def require_finite(value: float, name: str) -> float:
    """Return value if it is a finite float; otherwise raise."""

    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise InvalidParameterError(f"{name} must be a real number, got {type(value)!r}")
    as_float = float(value)
    if as_float != as_float or as_float in (float("inf"), float("-inf")):
        raise InvalidParameterError(f"{name} must be finite, got {value!r}")
    return as_float


def youngs_modulus_gpa_to_internal(e_gpa: float) -> float:
    """Convert Young's modulus from GPa to N/mm²."""

    return require_finite(e_gpa, "E") * GPA_TO_N_PER_MM2


def youngs_modulus_internal_to_gpa(e_n_per_mm2: float) -> float:
    """Convert Young's modulus from N/mm² to GPa."""

    return require_finite(e_n_per_mm2, "E_internal") / GPA_TO_N_PER_MM2


def load_kn_to_internal(f_kn: float) -> float:
    """Convert load magnitude from kN to N."""

    return require_finite(f_kn, "F") * KN_TO_N


def load_internal_to_kn(f_n: float) -> float:
    """Convert load magnitude from N to kN."""

    return require_finite(f_n, "F_internal") / KN_TO_N
