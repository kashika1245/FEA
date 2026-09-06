"""Global stiffness assembly and load-vector construction."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from app.scientific.config import NumericalTolerances
from app.scientific.exceptions import InvalidLoadError, NumericalStabilityError
from app.scientific.fem.element import axial_stiffness, element_stiffness
from app.scientific.model import TrussModel
from app.scientific.parameters import StructuralParameters


def assemble_global_stiffness(
    model: TrussModel,
    parameters: StructuralParameters,
) -> npt.NDArray[np.float64]:
    """Assemble the global stiffness matrix K (n_dof by n_dof)."""

    parameters.aligned_to(model)
    stiffness = np.zeros((model.n_dof, model.n_dof), dtype=np.float64)
    for geometry in model.member_geometry():
        area = parameters.area_of(geometry.member_id)
        axial = axial_stiffness(area, parameters.e_n_per_mm2, geometry.length_mm)
        local = element_stiffness(geometry.cosine, geometry.sine, axial)
        dofs = geometry.dof_indices
        stiffness[np.ix_(dofs, dofs)] += local
    if not np.all(np.isfinite(stiffness)):
        raise NumericalStabilityError("global stiffness contains non-finite entries")
    return stiffness


def assemble_load_vector(model: TrussModel, force_n: float) -> npt.NDArray[np.float64]:
    """Assemble F_global from canonical load directions and magnitude F."""

    if not np.isfinite(force_n):
        raise InvalidLoadError(f"load magnitude must be finite, got {force_n}")
    load_vector = np.zeros(model.n_dof, dtype=np.float64)
    for spec in model.loads:
        load_vector[model.global_dof_ux(spec.node_id)] += force_n * spec.direction_x
        load_vector[model.global_dof_uy(spec.node_id)] += force_n * spec.direction_y
    if not np.all(np.isfinite(load_vector)):
        raise NumericalStabilityError("load vector contains non-finite entries")
    return load_vector


def symmetry_residual(stiffness: npt.NDArray[np.float64]) -> float:
    """Return Frobenius norm of K minus K transpose."""

    delta = stiffness - stiffness.T
    return float(np.linalg.norm(delta, ord="fro"))


def assert_symmetric(
    stiffness: npt.NDArray[np.float64],
    tolerances: NumericalTolerances,
) -> None:
    residual = symmetry_residual(stiffness)
    scale = float(np.linalg.norm(stiffness, ord="fro"))
    limit = max(tolerances.symmetry_atol, tolerances.symmetry_rtol * scale)
    if residual > limit:
        raise NumericalStabilityError(
            f"stiffness matrix is not symmetric: ||K-K^T||_F={residual} exceeds {limit}"
        )
