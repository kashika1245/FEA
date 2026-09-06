from __future__ import annotations

import numpy as np
import pytest

from app.scientific.config import ScientificConfig
from app.scientific.fem.solver import analyze
from app.scientific.model import TrussModel
from app.scientific.parameters import StructuralParameters
from tests.conftest import single_bar_model
from tests.scientific.reference_solver import reference_analyze


def test_single_bar_matches_reference_and_analytics(config: ScientificConfig) -> None:
    model = single_bar_model(config.solver.tolerances.min_length_mm)
    parameters = StructuralParameters.uniform(model, 100.0, 200.0, 1.0)
    production = analyze(model, parameters, config)
    reference = reference_analyze(model, parameters)
    rtol = config.solver.tolerances.reference_rtol
    atol = config.solver.tolerances.reference_atol
    np.testing.assert_allclose(
        production.displacement_vector, reference.displacement, rtol=rtol, atol=atol
    )
    assert production.u_max_mm == pytest.approx(reference.u_max, rel=rtol, abs=atol)
    assert production.sigma_max_n_per_mm2 == pytest.approx(reference.sigma_max, rel=rtol, abs=atol)
    assert production.compliance_nmm == pytest.approx(reference.compliance, rel=rtol, abs=atol)
    assert production.u_max_mm == pytest.approx(0.05, rel=1e-12, abs=1e-15)
    assert production.sigma_max_n_per_mm2 == pytest.approx(10.0, rel=1e-12, abs=1e-15)
    assert production.compliance_nmm == pytest.approx(50.0, rel=1e-12, abs=1e-15)


def test_ten_bar_matches_reference(ten_bar: TrussModel, config: ScientificConfig) -> None:
    parameters = StructuralParameters.uniform(ten_bar, 62.5, 190.0, 3.25)
    production = analyze(ten_bar, parameters, config)
    reference = reference_analyze(ten_bar, parameters)
    rtol = config.solver.tolerances.reference_rtol
    atol = config.solver.tolerances.reference_atol
    np.testing.assert_allclose(
        production.displacement_vector, reference.displacement, rtol=rtol, atol=atol
    )
    for member in production.member_results:
        assert member.axial_force_n == pytest.approx(
            reference.axial_forces[member.member_id], rel=rtol, abs=atol
        )
        assert member.stress_n_per_mm2 == pytest.approx(
            reference.stresses[member.member_id], rel=rtol, abs=atol
        )
    assert production.u_max_mm == pytest.approx(reference.u_max, rel=rtol, abs=atol)
    assert production.sigma_max_n_per_mm2 == pytest.approx(reference.sigma_max, rel=rtol, abs=atol)
    assert production.compliance_nmm == pytest.approx(reference.compliance, rel=rtol, abs=atol)


def test_heterogeneous_areas_match_reference(ten_bar: TrussModel, config: ScientificConfig) -> None:
    areas = {i: 50.0 + 5.0 * i for i in ten_bar.member_ids}
    parameters = StructuralParameters.from_paper_units(areas, 205.0, 7.5).aligned_to(ten_bar)
    production = analyze(ten_bar, parameters, config)
    reference = reference_analyze(ten_bar, parameters)
    np.testing.assert_allclose(
        production.displacement_vector,
        reference.displacement,
        rtol=config.solver.tolerances.reference_rtol,
        atol=config.solver.tolerances.reference_atol,
    )
