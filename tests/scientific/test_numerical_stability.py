from __future__ import annotations

import pytest

from app.scientific.config import ScientificConfig
from app.scientific.exceptions import (
    InvalidMaterialError,
    InvalidParameterError,
    SingularStructureError,
)
from app.scientific.fem.solver import analyze
from app.scientific.geometry import Node
from app.scientific.model import TrussModel
from app.scientific.parameters import StructuralParameters
from app.scientific.topology import LoadSpec, Member, Support
from tests.conftest import single_bar_model


def test_zero_and_negative_area_rejected(ten_bar: TrussModel) -> None:
    with pytest.raises(InvalidMaterialError):
        StructuralParameters.uniform(ten_bar, 0.0, 200.0, 1.0)
    with pytest.raises(InvalidMaterialError):
        StructuralParameters.uniform(ten_bar, -5.0, 200.0, 1.0)


def test_zero_and_negative_modulus_rejected(ten_bar: TrussModel) -> None:
    with pytest.raises(InvalidMaterialError):
        StructuralParameters.uniform(ten_bar, 50.0, 0.0, 1.0)
    with pytest.raises(InvalidMaterialError):
        StructuralParameters.uniform(ten_bar, 50.0, -180.0, 1.0)


def test_nan_and_inf_parameters_rejected(ten_bar: TrussModel) -> None:
    with pytest.raises(InvalidParameterError):
        StructuralParameters.from_paper_units(
            {i: 50.0 for i in ten_bar.member_ids}, float("nan"), 1.0
        )
    with pytest.raises(InvalidParameterError):
        StructuralParameters.from_paper_units(
            {i: float("inf") for i in ten_bar.member_ids}, 200.0, 1.0
        )
    with pytest.raises(InvalidParameterError):
        StructuralParameters.from_paper_units(
            {i: 50.0 for i in ten_bar.member_ids}, 200.0, float("inf")
        )


def test_singular_unconstrained_bar(config: ScientificConfig) -> None:
    model = TrussModel(
        nodes=(Node(1, 0.0, 0.0), Node(2, 1000.0, 0.0)),
        members=(Member(1, 1, 2),),
        supports=(Support(1, 1, restrain_ux=True, restrain_uy=False),),
        loads=(LoadSpec(1, 2, 0.0, -1.0),),
        geometry_version="test.mechanism",
        min_length_mm=config.solver.tolerances.min_length_mm,
    )
    parameters = StructuralParameters.uniform(model, 50.0, 200.0, 1.0)
    with pytest.raises(SingularStructureError):
        analyze(model, parameters, config)


def test_domain_boundary_values_solve(ten_bar: TrussModel, config: ScientificConfig) -> None:
    domain = config.parameter_domain
    low = StructuralParameters.uniform(
        ten_bar, domain.area_mm2.min, domain.youngs_modulus_gpa.min, domain.load_kn.min
    )
    high = StructuralParameters.uniform(
        ten_bar, domain.area_mm2.max, domain.youngs_modulus_gpa.max, domain.load_kn.max
    )
    r_low = analyze(ten_bar, low, config)
    r_high = analyze(ten_bar, high, config)
    assert r_low.validated and r_high.validated
    assert r_low.u_max_mm > 0.0 and r_high.u_max_mm > 0.0
    # Corner (A,E,F) = (min,min,min) vs (max,max,max) does not imply a universal
    # u_max ordering because F increases by 10x while AE increases by less.


def test_small_positive_area_solves(config: ScientificConfig) -> None:
    model = single_bar_model(config.solver.tolerances.min_length_mm)
    parameters = StructuralParameters.uniform(model, 1e-3, 200.0, 1.0)
    result = analyze(model, parameters, config)
    assert result.validated
    assert result.u_max_mm > 0.0
