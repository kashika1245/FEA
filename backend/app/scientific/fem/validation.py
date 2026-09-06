"""Post-solve numerical validation of the reconstructed FEM system."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from app.scientific.config import NumericalTolerances
from app.scientific.exceptions import NumericalStabilityError
from app.scientific.fem.assembly import assert_symmetric
from app.scientific.fem.boundary import ReducedSystem
from app.scientific.fem.reactions import assert_global_equilibrium
from app.scientific.model import TrussModel


def assert_reduced_equilibrium(
    reduced: ReducedSystem,
    u_free: npt.NDArray[np.float64],
    tolerances: NumericalTolerances,
) -> None:
    residual = reduced.stiffness_ff @ u_free - reduced.load_f
    residual_norm = float(np.linalg.norm(residual))
    load_norm = float(np.linalg.norm(reduced.load_f))
    limit = tolerances.equilibrium_rtol * max(load_norm, 1.0)
    if residual_norm > limit:
        raise NumericalStabilityError(
            f"reduced equilibrium failed: ||K_ff u_f - F_f||={residual_norm} exceeds {limit}"
        )


def assert_finite_vector(vector: npt.NDArray[np.float64], name: str) -> None:
    if not np.all(np.isfinite(vector)):
        raise NumericalStabilityError(f"{name} contains non-finite values")


def validate_solved_system(
    stiffness: npt.NDArray[np.float64],
    load_vector: npt.NDArray[np.float64],
    displacement: npt.NDArray[np.float64],
    reactions: npt.NDArray[np.float64],
    reduced: ReducedSystem,
    u_free: npt.NDArray[np.float64],
    model: TrussModel,
    tolerances: NumericalTolerances,
) -> None:
    assert_symmetric(stiffness, tolerances)
    assert_finite_vector(displacement, "displacement")
    assert_finite_vector(reactions, "reactions")
    assert_reduced_equilibrium(reduced, u_free, tolerances)
    assert_global_equilibrium(load_vector, reactions, model, tolerances)
    constrained = list(reduced.constrained_dofs)
    if constrained and np.linalg.norm(displacement[constrained]) != 0.0:
        raise NumericalStabilityError("constrained DOFs are not identically zero")
