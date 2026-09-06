"""Structural parameters in internal units (mm², N/mm², N)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from app.scientific.exceptions import InvalidMaterialError, InvalidParameterError
from app.scientific.model import TrussModel
from app.scientific.units import (
    load_internal_to_kn,
    load_kn_to_internal,
    require_finite,
    youngs_modulus_gpa_to_internal,
    youngs_modulus_internal_to_gpa,
)


@dataclass(frozen=True, slots=True)
class StructuralParameters:
    """Member areas, Young's modulus, and load magnitude in internal units."""

    areas_mm2_by_member_id: Mapping[int, float]
    e_n_per_mm2: float
    f_n: float

    def __post_init__(self) -> None:
        areas = {
            int(member_id): require_finite(area, f"A[{member_id}]")
            for member_id, area in self.areas_mm2_by_member_id.items()
        }
        object.__setattr__(self, "areas_mm2_by_member_id", dict(sorted(areas.items())))
        object.__setattr__(self, "e_n_per_mm2", require_finite(self.e_n_per_mm2, "E"))
        object.__setattr__(self, "f_n", require_finite(self.f_n, "F"))
        if self.e_n_per_mm2 <= 0.0:
            raise InvalidMaterialError(
                f"Young's modulus must be positive, got {self.e_n_per_mm2} N/mm^2"
            )
        for member_id, area in self.areas_mm2_by_member_id.items():
            if area <= 0.0:
                raise InvalidMaterialError(
                    f"area of member {member_id} must be positive, got {area} mm^2"
                )

    @classmethod
    def from_paper_units(
        cls,
        areas_mm2_by_member_id: Mapping[int, float],
        e_gpa: float,
        f_kn: float,
    ) -> StructuralParameters:
        return cls(
            areas_mm2_by_member_id=areas_mm2_by_member_id,
            e_n_per_mm2=youngs_modulus_gpa_to_internal(e_gpa),
            f_n=load_kn_to_internal(f_kn),
        )

    def area_of(self, member_id: int) -> float:
        try:
            return self.areas_mm2_by_member_id[member_id]
        except KeyError as exc:
            raise InvalidParameterError(f"no area provided for member {member_id}") from exc

    def e_gpa(self) -> float:
        return youngs_modulus_internal_to_gpa(self.e_n_per_mm2)

    def f_kn(self) -> float:
        return load_internal_to_kn(self.f_n)

    def aligned_to(self, model: TrussModel) -> StructuralParameters:
        missing = [
            member_id
            for member_id in model.member_ids
            if member_id not in self.areas_mm2_by_member_id
        ]
        extra = [
            member_id
            for member_id in self.areas_mm2_by_member_id
            if member_id not in set(model.member_ids)
        ]
        if missing or extra:
            raise InvalidParameterError(
                f"area map does not match model members; missing={missing}, extra={extra}"
            )
        return self

    @classmethod
    def uniform(
        cls,
        model: TrussModel,
        area_mm2: float,
        e_gpa: float,
        f_kn: float,
    ) -> StructuralParameters:
        areas = {member_id: area_mm2 for member_id in model.member_ids}
        return cls.from_paper_units(areas, e_gpa, f_kn).aligned_to(model)
