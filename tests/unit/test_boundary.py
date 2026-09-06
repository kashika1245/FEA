from __future__ import annotations

import numpy as np
import pytest

from app.scientific.config import ScientificConfig
from app.scientific.exceptions import InvalidTopologyError
from app.scientific.fem.assembly import assemble_global_stiffness, assemble_load_vector
from app.scientific.fem.boundary import partition_system, reconstruct_displacement
from app.scientific.geometry import Node
from app.scientific.model import TrussModel
from app.scientific.parameters import StructuralParameters
from app.scientific.topology import LoadSpec, Member, Support


def test_partition_canonical(ten_bar: TrussModel, config: ScientificConfig) -> None:
    parameters = StructuralParameters.uniform(ten_bar, 80.0, 200.0, 4.0)
    stiffness = assemble_global_stiffness(ten_bar, parameters)
    load = assemble_load_vector(ten_bar, parameters.f_n)
    reduced = partition_system(stiffness, load, ten_bar)
    assert reduced.free_dofs == (0, 1, 2, 3, 4, 5, 6, 7)
    assert reduced.constrained_dofs == (8, 9, 10, 11)
    assert reduced.stiffness_ff.shape == (8, 8)
    assert reduced.load_f.shape == (8,)


def test_reconstruct_sets_supports_to_zero(ten_bar: TrussModel, config: ScientificConfig) -> None:
    parameters = StructuralParameters.uniform(ten_bar, 80.0, 200.0, 4.0)
    stiffness = assemble_global_stiffness(ten_bar, parameters)
    load = assemble_load_vector(ten_bar, parameters.f_n)
    reduced = partition_system(stiffness, load, ten_bar)
    u_free = np.arange(8, dtype=np.float64)
    global_u = reconstruct_displacement(u_free, reduced)
    assert global_u[list(reduced.constrained_dofs)].tolist() == [0.0, 0.0, 0.0, 0.0]
    np.testing.assert_array_equal(global_u[list(reduced.free_dofs)], u_free)


def test_no_free_dofs_partition_fails(config: ScientificConfig) -> None:
    model = TrussModel(
        nodes=(Node(1, 0.0, 0.0), Node(2, 10.0, 0.0)),
        members=(Member(1, 1, 2),),
        supports=(
            Support(1, 1, True, True),
            Support(2, 2, True, True),
        ),
        loads=(LoadSpec(1, 2, 1.0, 0.0),),
        geometry_version="test.fully-fixed",
        min_length_mm=config.solver.tolerances.min_length_mm,
    )
    parameters = StructuralParameters.uniform(model, 50.0, 200.0, 1.0)
    stiffness = assemble_global_stiffness(model, parameters)
    load = assemble_load_vector(model, parameters.f_n)
    with pytest.raises(InvalidTopologyError, match="no free degrees of freedom"):
        partition_system(stiffness, load, model)
