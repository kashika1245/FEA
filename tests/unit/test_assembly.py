from __future__ import annotations

import numpy as np

from app.scientific.config import ScientificConfig
from app.scientific.fem.assembly import (
    assemble_global_stiffness,
    assemble_load_vector,
    symmetry_residual,
)
from app.scientific.model import TrussModel
from app.scientific.parameters import StructuralParameters


def test_global_stiffness_shape_and_symmetry(ten_bar: TrussModel, config: ScientificConfig) -> None:
    parameters = StructuralParameters.uniform(ten_bar, 75.0, 200.0, 5.0)
    stiffness = assemble_global_stiffness(ten_bar, parameters)
    assert stiffness.shape == (12, 12)
    limit = max(
        config.solver.tolerances.symmetry_atol,
        config.solver.tolerances.symmetry_rtol * float(np.linalg.norm(stiffness, ord="fro")),
    )
    assert symmetry_residual(stiffness) <= limit


def test_load_vector_follows_canonical_direction(
    ten_bar: TrussModel,
) -> None:
    load = assemble_load_vector(ten_bar, 2500.0)
    expected = np.zeros(12)
    expected[ten_bar.global_dof_uy(2)] = -2500.0
    np.testing.assert_allclose(load, expected)
    assert load[ten_bar.global_dof_ux(2)] == 0.0
