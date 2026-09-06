"""Numerically stable reduced-system solve and the public analyze() entry point."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from app.scientific.config import ScientificConfig, load_default_scientific_config
from app.scientific.exceptions import NumericalStabilityError, SingularStructureError
from app.scientific.fem.assembly import (
    assemble_global_stiffness,
    assemble_load_vector,
    symmetry_residual,
)
from app.scientific.fem.boundary import ReducedSystem, partition_system, reconstruct_displacement
from app.scientific.fem.reactions import equilibrium_residuals, reaction_vector
from app.scientific.fem.validation import validate_solved_system
from app.scientific.model import TrussModel
from app.scientific.parameters import StructuralParameters
from app.scientific.responses import (
    SolverDiagnostics,
    StructuralResult,
    compliance,
    maximum_absolute_stress,
    maximum_displacement_magnitude,
    member_resultants,
    nodal_displacements_from_vector,
    utc_timestamp,
)


def solve_reduced_displacements(
    reduced: ReducedSystem,
    max_condition_number: float,
) -> tuple[npt.NDArray[np.float64], float]:
    """Solve K_ff u_f = F_f. Does not form an explicit inverse."""

    if reduced.stiffness_ff.shape[0] != reduced.stiffness_ff.shape[1]:
        raise NumericalStabilityError("reduced stiffness is not square")
    if reduced.stiffness_ff.shape[0] != reduced.load_f.shape[0]:
        raise NumericalStabilityError("reduced stiffness and load dimension mismatch")
    if not np.all(np.isfinite(reduced.stiffness_ff)) or not np.all(np.isfinite(reduced.load_f)):
        raise NumericalStabilityError("reduced system contains non-finite values")
    try:
        condition_number = float(np.linalg.cond(reduced.stiffness_ff))
    except np.linalg.LinAlgError as exc:
        raise SingularStructureError("failed to estimate condition number of K_ff") from exc
    if not np.isfinite(condition_number) or condition_number > max_condition_number:
        raise SingularStructureError(
            f"reduced stiffness is singular or ill-conditioned: cond={condition_number} "
            f"(limit {max_condition_number})"
        )
    try:
        u_free = np.linalg.solve(reduced.stiffness_ff, reduced.load_f)
    except np.linalg.LinAlgError as exc:
        raise SingularStructureError("numpy.linalg.solve failed on K_ff (singular matrix)") from exc
    u_free = np.asarray(u_free, dtype=np.float64)
    if not np.all(np.isfinite(u_free)):
        raise NumericalStabilityError("solved free displacements contain non-finite values")
    return u_free, condition_number


def analyze(
    model: TrussModel,
    parameters: StructuralParameters,
    config: ScientificConfig | None = None,
) -> StructuralResult:
    """Run the full linear-elastic truss analysis and validate the solution."""

    resolved = config if config is not None else load_default_scientific_config()
    parameters = parameters.aligned_to(model)
    stiffness = assemble_global_stiffness(model, parameters)
    load_vector = assemble_load_vector(model, parameters.f_n)
    reduced = partition_system(stiffness, load_vector, model)
    u_free, condition_number = solve_reduced_displacements(
        reduced, resolved.solver.max_condition_number
    )
    displacement = reconstruct_displacement(u_free, reduced)
    reactions = reaction_vector(stiffness, displacement, load_vector)
    validate_solved_system(
        stiffness=stiffness,
        load_vector=load_vector,
        displacement=displacement,
        reactions=reactions,
        reduced=reduced,
        u_free=u_free,
        model=model,
        tolerances=resolved.solver.tolerances,
    )
    nodal = nodal_displacements_from_vector(model, displacement)
    members = member_resultants(model, parameters, displacement)
    u_max, u_max_node = maximum_displacement_magnitude(nodal)
    sigma_max, sigma_max_member = maximum_absolute_stress(members)
    compliance_nmm = compliance(load_vector, displacement)
    residual = reduced.stiffness_ff @ u_free - reduced.load_f
    sum_fx, sum_fy, sum_mz = equilibrium_residuals(load_vector, reactions, model)
    diagnostics = SolverDiagnostics(
        n_free_dofs=len(reduced.free_dofs),
        n_constrained_dofs=len(reduced.constrained_dofs),
        condition_number=condition_number,
        reduced_residual_norm=float(np.linalg.norm(residual)),
        stiffness_symmetry_residual=symmetry_residual(stiffness),
        equilibrium_sum_fx_n=sum_fx,
        equilibrium_sum_fy_n=sum_fy,
        equilibrium_sum_mz_nmm=sum_mz,
    )
    return StructuralResult(
        displacement_vector=displacement,
        nodal_displacements=nodal,
        member_results=members,
        reactions=reactions,
        load_vector=load_vector,
        u_max_mm=u_max,
        u_max_node_id=u_max_node,
        sigma_max_n_per_mm2=sigma_max,
        sigma_max_member_id=sigma_max_member,
        compliance_nmm=compliance_nmm,
        diagnostics=diagnostics,
        validated=True,
        geometry_version=model.geometry_version,
        solver_version=resolved.solver_version,
        software_version=resolved.software_version,
        analyzed_at_utc=utc_timestamp(),
    )
