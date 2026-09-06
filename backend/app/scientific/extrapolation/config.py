"""Extrapolation protocol helpers derived from Phase 1 domains and Phase 2 config."""

from __future__ import annotations

from app.scientific.config import ParameterDomain
from app.scientific.surrogate.config import INPUT_NAMES, VariableName

DOMAIN_BOUNDS: dict[str, tuple[str, str]] = {
    **{f"A{index}": ("area_mm2", "area_mm2") for index in range(1, 11)},
    "E": ("youngs_modulus_gpa", "youngs_modulus_gpa"),
    "F": ("load_kn", "load_kn"),
}


def variable_bounds(domain: ParameterDomain, variable: VariableName | str) -> tuple[float, float]:
    if variable in {f"A{index}" for index in range(1, 11)}:
        return domain.area_mm2.min, domain.area_mm2.max
    if variable == "E":
        return domain.youngs_modulus_gpa.min, domain.youngs_modulus_gpa.max
    if variable == "F":
        return domain.load_kn.min, domain.load_kn.max
    raise ValueError(f"unknown variable {variable}")


def input_index(variable: str) -> int:
    return INPUT_NAMES.index(variable)
