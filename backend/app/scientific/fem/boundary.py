"""Constrained/free DOF partition. Constrained displacements are prescribed to zero."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from app.scientific.exceptions import FEASolverError, InvalidTopologyError
from app.scientific.model import TrussModel


@dataclass(frozen=True, slots=True)
class ReducedSystem:
    free_dofs: tuple[int, ...]
    constrained_dofs: tuple[int, ...]
    stiffness_ff: npt.NDArray[np.float64]
    load_f: npt.NDArray[np.float64]
    n_dof: int


def partition_system(
    stiffness: npt.NDArray[np.float64],
    load_vector: npt.NDArray[np.float64],
    model: TrussModel,
) -> ReducedSystem:
    """Form K_ff and F_f. Constrained DOFs are eliminated, not zeroed in-place."""

    if stiffness.shape != (model.n_dof, model.n_dof):
        raise FEASolverError(
            f"stiffness shape {stiffness.shape} does not match n_dof={model.n_dof}"
        )
    if load_vector.shape != (model.n_dof,):
        raise FEASolverError(
            f"load vector shape {load_vector.shape} does not match n_dof={model.n_dof}"
        )
    free = model.free_dofs()
    constrained = model.constrained_dofs()
    if not free:
        raise InvalidTopologyError("no free degrees of freedom remain after applying supports")
    if set(free).intersection(constrained):
        raise InvalidTopologyError("free and constrained DOF sets overlap")
    if len(free) + len(constrained) != model.n_dof:
        raise InvalidTopologyError("free and constrained DOFs do not partition the global system")
    stiffness_ff = np.array(stiffness[np.ix_(free, free)], dtype=np.float64, copy=True)
    load_f = np.array(load_vector[list(free)], dtype=np.float64, copy=True)
    return ReducedSystem(
        free_dofs=free,
        constrained_dofs=constrained,
        stiffness_ff=stiffness_ff,
        load_f=load_f,
        n_dof=model.n_dof,
    )


def reconstruct_displacement(
    u_free: npt.NDArray[np.float64],
    reduced: ReducedSystem,
) -> npt.NDArray[np.float64]:
    """Place free DOFs into the global vector; constrained DOFs remain 0."""

    if u_free.shape != (len(reduced.free_dofs),):
        raise FEASolverError(
            f"free displacement length {u_free.shape} does not match {len(reduced.free_dofs)} free DOFs"
        )
    global_u = np.zeros(reduced.n_dof, dtype=np.float64)
    global_u[list(reduced.free_dofs)] = u_free
    return global_u
