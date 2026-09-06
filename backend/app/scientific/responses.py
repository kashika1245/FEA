"""Member resultants, scalar paper responses, and the immutable analysis result."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import numpy as np
import numpy.typing as npt

from app.scientific.exceptions import NumericalStabilityError
from app.scientific.fem.element import axial_stiffness
from app.scientific.model import TrussModel
from app.scientific.parameters import StructuralParameters
from app.scientific.units import INTERNAL_UNITS, UnitSystem


@dataclass(frozen=True, slots=True)
class MemberResult:
    member_id: int
    axial_force_n: float
    stress_n_per_mm2: float
    axial_extension_mm: float
    length_mm: float


@dataclass(frozen=True, slots=True)
class NodalDisplacement:
    node_id: int
    ux_mm: float
    uy_mm: float

    @property
    def magnitude_mm(self) -> float:
        return float(np.hypot(self.ux_mm, self.uy_mm))


@dataclass(frozen=True, slots=True)
class SolverDiagnostics:
    n_free_dofs: int
    n_constrained_dofs: int
    condition_number: float
    reduced_residual_norm: float
    stiffness_symmetry_residual: float
    equilibrium_sum_fx_n: float
    equilibrium_sum_fy_n: float
    equilibrium_sum_mz_nmm: float


@dataclass(frozen=True, slots=True)
class StructuralResult:
    displacement_vector: npt.NDArray[np.float64]
    nodal_displacements: tuple[NodalDisplacement, ...]
    member_results: tuple[MemberResult, ...]
    reactions: npt.NDArray[np.float64]
    load_vector: npt.NDArray[np.float64]
    u_max_mm: float
    u_max_node_id: int
    sigma_max_n_per_mm2: float
    sigma_max_member_id: int
    compliance_nmm: float
    diagnostics: SolverDiagnostics
    validated: bool
    geometry_version: str
    solver_version: str
    software_version: str
    analyzed_at_utc: str
    units: UnitSystem = INTERNAL_UNITS

    def __post_init__(self) -> None:
        displacement = np.array(self.displacement_vector, dtype=np.float64, copy=True)
        reactions = np.array(self.reactions, dtype=np.float64, copy=True)
        load_vector = np.array(self.load_vector, dtype=np.float64, copy=True)
        displacement.setflags(write=False)
        reactions.setflags(write=False)
        load_vector.setflags(write=False)
        object.__setattr__(self, "displacement_vector", displacement)
        object.__setattr__(self, "reactions", reactions)
        object.__setattr__(self, "load_vector", load_vector)


def nodal_displacements_from_vector(
    model: TrussModel,
    displacement: npt.NDArray[np.float64],
) -> tuple[NodalDisplacement, ...]:
    items: list[NodalDisplacement] = []
    for node in model.nodes:
        ux = float(displacement[model.global_dof_ux(node.node_id)])
        uy = float(displacement[model.global_dof_uy(node.node_id)])
        items.append(NodalDisplacement(node.node_id, ux, uy))
    return tuple(items)


def maximum_displacement_magnitude(
    nodal: tuple[NodalDisplacement, ...],
) -> tuple[float, int]:
    if not nodal:
        raise NumericalStabilityError("no nodal displacements")
    best = max(nodal, key=lambda item: item.magnitude_mm)
    return best.magnitude_mm, best.node_id


def member_resultants(
    model: TrussModel,
    parameters: StructuralParameters,
    displacement: npt.NDArray[np.float64],
) -> tuple[MemberResult, ...]:
    results: list[MemberResult] = []
    for geometry in model.member_geometry():
        area = parameters.area_of(geometry.member_id)
        ux_i = float(displacement[geometry.dof_indices[0]])
        uy_i = float(displacement[geometry.dof_indices[1]])
        ux_j = float(displacement[geometry.dof_indices[2]])
        uy_j = float(displacement[geometry.dof_indices[3]])
        extension = (ux_j - ux_i) * geometry.cosine + (uy_j - uy_i) * geometry.sine
        axial = axial_stiffness(area, parameters.e_n_per_mm2, geometry.length_mm)
        force = axial * extension
        stress = force / area
        if not np.isfinite(force) or not np.isfinite(stress):
            raise NumericalStabilityError(
                f"non-finite member resultant on member {geometry.member_id}"
            )
        results.append(
            MemberResult(
                member_id=geometry.member_id,
                axial_force_n=float(force),
                stress_n_per_mm2=float(stress),
                axial_extension_mm=float(extension),
                length_mm=geometry.length_mm,
            )
        )
    return tuple(results)


def maximum_absolute_stress(members: tuple[MemberResult, ...]) -> tuple[float, int]:
    if not members:
        raise NumericalStabilityError("no member results")
    best = max(members, key=lambda item: abs(item.stress_n_per_mm2))
    return abs(best.stress_n_per_mm2), best.member_id


def compliance(
    load_vector: npt.NDArray[np.float64], displacement: npt.NDArray[np.float64]
) -> float:
    value = float(load_vector @ displacement)
    if not np.isfinite(value):
        raise NumericalStabilityError(f"non-finite compliance {value}")
    return value


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()
