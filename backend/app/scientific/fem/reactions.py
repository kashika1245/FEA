"""Reaction forces R = K u - F and global equilibrium checks."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from app.scientific.config import NumericalTolerances
from app.scientific.exceptions import NumericalStabilityError
from app.scientific.model import TrussModel


def reaction_vector(
    stiffness: npt.NDArray[np.float64],
    displacement: npt.NDArray[np.float64],
    load_vector: npt.NDArray[np.float64],
) -> npt.NDArray[np.float64]:
    """Return R = K u - F. At free DOFs this must be ~0; at supports it is the reaction."""

    reactions = stiffness @ displacement - load_vector
    if not np.all(np.isfinite(reactions)):
        raise NumericalStabilityError("reaction vector contains non-finite entries")
    return np.asarray(reactions, dtype=np.float64)


def nodal_forces(
    force_vector: npt.NDArray[np.float64],
    model: TrussModel,
) -> dict[int, tuple[float, float]]:
    return {
        node.node_id: (
            float(force_vector[model.global_dof_ux(node.node_id)]),
            float(force_vector[model.global_dof_uy(node.node_id)]),
        )
        for node in model.nodes
    }


def equilibrium_residuals(
    load_vector: npt.NDArray[np.float64],
    reactions: npt.NDArray[np.float64],
    model: TrussModel,
) -> tuple[float, float, float]:
    """Return (sum Fx, sum Fy, sum Mz about origin) of applied loads plus reactions."""

    total = load_vector + reactions
    sum_fx = 0.0
    sum_fy = 0.0
    sum_mz = 0.0
    for node in model.nodes:
        fx = float(total[model.global_dof_ux(node.node_id)])
        fy = float(total[model.global_dof_uy(node.node_id)])
        sum_fx += fx
        sum_fy += fy
        sum_mz += node.x_mm * fy - node.y_mm * fx
    return sum_fx, sum_fy, sum_mz


def assert_global_equilibrium(
    load_vector: npt.NDArray[np.float64],
    reactions: npt.NDArray[np.float64],
    model: TrussModel,
    tolerances: NumericalTolerances,
) -> None:
    sum_fx, sum_fy, sum_mz = equilibrium_residuals(load_vector, reactions, model)
    force_scale = max(float(np.linalg.norm(load_vector)), 1.0)
    moment_scale = max(force_scale * tolerances.length_reference_mm, 1.0)
    force_limit = tolerances.equilibrium_force_rtol * force_scale
    moment_limit = tolerances.equilibrium_moment_rtol * moment_scale
    if abs(sum_fx) > force_limit or abs(sum_fy) > force_limit:
        raise NumericalStabilityError(
            f"global force equilibrium failed: sumFx={sum_fx}, sumFy={sum_fy}, limit={force_limit}"
        )
    if abs(sum_mz) > moment_limit:
        raise NumericalStabilityError(
            f"global moment equilibrium failed: sumMz={sum_mz}, limit={moment_limit}"
        )
