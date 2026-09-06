"""Independent test-only planar truss solver.

This is not used by production analysis. It uses a 1D spring + transformation
matrix and an SVD least-squares solve, then recovers member force from strain.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from app.scientific.exceptions import NumericalStabilityError, SingularStructureError
from app.scientific.model import TrussModel
from app.scientific.parameters import StructuralParameters


@dataclass(frozen=True, slots=True)
class ReferenceResult:
    displacement: npt.NDArray[np.float64]
    axial_forces: dict[int, float]
    stresses: dict[int, float]
    u_max: float
    sigma_max: float
    compliance: float


def _local_axial_stiffness(axial: float) -> npt.NDArray[np.float64]:
    return axial * np.array([[1.0, -1.0], [-1.0, 1.0]], dtype=np.float64)


def _transform(cosine: float, sine: float) -> npt.NDArray[np.float64]:
    return np.array(
        [[cosine, sine, 0.0, 0.0], [0.0, 0.0, cosine, sine]],
        dtype=np.float64,
    )


def reference_analyze(model: TrussModel, parameters: StructuralParameters) -> ReferenceResult:
    parameters.aligned_to(model)
    n_dof = model.n_dof
    stiffness = np.zeros((n_dof, n_dof), dtype=np.float64)
    load = np.zeros(n_dof, dtype=np.float64)
    for spec in model.loads:
        load[model.global_dof_ux(spec.node_id)] += parameters.f_n * spec.direction_x
        load[model.global_dof_uy(spec.node_id)] += parameters.f_n * spec.direction_y
    for geometry in model.member_geometry():
        area = parameters.area_of(geometry.member_id)
        axial = (area * parameters.e_n_per_mm2) / geometry.length_mm
        transformed = (
            _transform(geometry.cosine, geometry.sine).T
            @ _local_axial_stiffness(axial)
            @ _transform(geometry.cosine, geometry.sine)
        )
        i, j, k, ell = geometry.dof_indices
        index = (i, j, k, ell)
        for row, global_row in enumerate(index):
            for col, global_col in enumerate(index):
                stiffness[global_row, global_col] += transformed[row, col]
    free = list(model.free_dofs())
    k_ff = np.zeros((len(free), len(free)), dtype=np.float64)
    f_f = np.zeros(len(free), dtype=np.float64)
    for a, dof_a in enumerate(free):
        f_f[a] = load[dof_a]
        for b, dof_b in enumerate(free):
            k_ff[a, b] = stiffness[dof_a, dof_b]
    solution, _residuals, rank, _singular = np.linalg.lstsq(k_ff, f_f, rcond=None)
    if rank < len(free):
        raise SingularStructureError(
            f"reference solver: rank-deficient K_ff rank={rank} < {len(free)}"
        )
    if not np.all(np.isfinite(solution)):
        raise NumericalStabilityError("reference solver produced non-finite displacements")
    displacement = np.zeros(n_dof, dtype=np.float64)
    for local, dof in enumerate(free):
        displacement[dof] = float(solution[local])
    forces: dict[int, float] = {}
    stresses: dict[int, float] = {}
    for geometry in model.member_geometry():
        area = parameters.area_of(geometry.member_id)
        ux_i = displacement[geometry.dof_indices[0]]
        uy_i = displacement[geometry.dof_indices[1]]
        ux_j = displacement[geometry.dof_indices[2]]
        uy_j = displacement[geometry.dof_indices[3]]
        extension = (ux_j - ux_i) * geometry.cosine + (uy_j - uy_i) * geometry.sine
        strain = extension / geometry.length_mm
        stress = parameters.e_n_per_mm2 * strain
        force = stress * area
        forces[geometry.member_id] = float(force)
        stresses[geometry.member_id] = float(stress)
    magnitudes = []
    for node in model.nodes:
        ux = displacement[model.global_dof_ux(node.node_id)]
        uy = displacement[model.global_dof_uy(node.node_id)]
        magnitudes.append(float(np.hypot(ux, uy)))
    compliance = float(load @ displacement)
    return ReferenceResult(
        displacement=displacement,
        axial_forces=forces,
        stresses=stresses,
        u_max=max(magnitudes),
        sigma_max=max(abs(value) for value in stresses.values()),
        compliance=compliance,
    )
