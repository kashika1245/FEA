from __future__ import annotations

import numpy as np
import pytest

from app.scientific.config import ScientificConfig
from app.scientific.fem.assembly import assemble_global_stiffness, assemble_load_vector
from app.scientific.fem.reactions import equilibrium_residuals, reaction_vector
from app.scientific.fem.solver import analyze
from app.scientific.model import TrussModel
from app.scientific.parameters import StructuralParameters


def test_reduced_and_global_equilibrium(ten_bar: TrussModel, config: ScientificConfig) -> None:
    parameters = StructuralParameters.uniform(ten_bar, 90.0, 210.0, 8.0)
    result = analyze(ten_bar, parameters, config)
    stiffness = assemble_global_stiffness(ten_bar, parameters)
    load = assemble_load_vector(ten_bar, parameters.f_n)
    residual = stiffness @ result.displacement_vector - load - result.reactions
    assert float(np.linalg.norm(residual)) <= 1e-12
    sum_fx, sum_fy, sum_mz = equilibrium_residuals(load, result.reactions, ten_bar)
    force_scale = max(float(np.linalg.norm(load)), 1.0)
    assert abs(sum_fx) <= config.solver.tolerances.equilibrium_force_rtol * force_scale
    assert abs(sum_fy) <= config.solver.tolerances.equilibrium_force_rtol * force_scale
    moment_scale = force_scale * config.solver.tolerances.length_reference_mm
    assert abs(sum_mz) <= config.solver.tolerances.equilibrium_moment_rtol * moment_scale


def test_reactions_balance_applied_load(ten_bar: TrussModel, config: ScientificConfig) -> None:
    parameters = StructuralParameters.uniform(ten_bar, 70.0, 200.0, 2.0)
    result = analyze(ten_bar, parameters, config)
    stiffness = assemble_global_stiffness(ten_bar, parameters)
    load = assemble_load_vector(ten_bar, parameters.f_n)
    reactions = reaction_vector(stiffness, result.displacement_vector, load)
    np.testing.assert_allclose(reactions, result.reactions)
    total_fy = float(np.sum(load[1::2] + reactions[1::2]))
    total_fx = float(np.sum(load[0::2] + reactions[0::2]))
    assert total_fx == pytest.approx(0.0, abs=1e-9)
    assert total_fy == pytest.approx(0.0, abs=1e-9)
