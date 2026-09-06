from __future__ import annotations

import numpy as np
import pytest

from app.scientific.config import ScientificConfig
from app.scientific.fem.solver import analyze
from app.scientific.model import TrussModel
from app.scientific.parameters import StructuralParameters
from tests.conftest import single_bar_model


def test_single_bar_analytical(config: ScientificConfig) -> None:
    model = single_bar_model(config.solver.tolerances.min_length_mm)
    area = 100.0
    e_gpa = 200.0
    f_kn = 1.0
    parameters = StructuralParameters.uniform(model, area, e_gpa, f_kn)
    result = analyze(model, parameters, config)
    e_internal = 200_000.0
    force = 1000.0
    length = 1000.0
    u_expected = force * length / (area * e_internal)
    assert result.u_max_mm == pytest.approx(u_expected)
    assert result.u_max_node_id == 2
    assert result.member_results[0].axial_force_n == pytest.approx(force)
    assert result.sigma_max_n_per_mm2 == pytest.approx(force / area)
    assert result.compliance_nmm == pytest.approx(force * u_expected)
    assert result.nodal_displacements[0].ux_mm == 0.0
    assert result.nodal_displacements[1].uy_mm == 0.0


def test_canonical_analysis_finite(ten_bar: TrussModel, config: ScientificConfig) -> None:
    parameters = StructuralParameters.uniform(ten_bar, 75.0, 200.0, 5.0)
    result = analyze(ten_bar, parameters, config)
    assert result.validated is True
    assert np.all(np.isfinite(result.displacement_vector))
    assert result.u_max_mm > 0.0
    assert result.sigma_max_n_per_mm2 > 0.0
    assert result.compliance_nmm > 0.0
    assert result.diagnostics.condition_number < config.solver.max_condition_number
