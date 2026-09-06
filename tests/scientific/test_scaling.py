from __future__ import annotations

import numpy as np
import pytest

from app.scientific.config import ScientificConfig
from app.scientific.fem.solver import analyze
from app.scientific.model import TrussModel
from app.scientific.parameters import StructuralParameters


def _compare(a: np.ndarray, b: np.ndarray, rtol: float) -> None:
    np.testing.assert_allclose(a, b, rtol=rtol, atol=0.0)


def test_load_scaling(ten_bar: TrussModel, config: ScientificConfig) -> None:
    base = StructuralParameters.uniform(ten_bar, 80.0, 200.0, 3.0)
    doubled = StructuralParameters.uniform(ten_bar, 80.0, 200.0, 6.0)
    r1 = analyze(ten_bar, base, config)
    r2 = analyze(ten_bar, doubled, config)
    rtol = config.solver.tolerances.scaling_rtol
    _compare(r2.displacement_vector, 2.0 * r1.displacement_vector, rtol)
    assert r2.sigma_max_n_per_mm2 == pytest.approx(2.0 * r1.sigma_max_n_per_mm2, rel=rtol)
    assert r2.compliance_nmm == pytest.approx(4.0 * r1.compliance_nmm, rel=rtol)


def test_area_scaling(ten_bar: TrussModel, config: ScientificConfig) -> None:
    alpha = 2.0
    base = StructuralParameters.uniform(ten_bar, 60.0, 200.0, 4.0)
    scaled = StructuralParameters.uniform(ten_bar, 60.0 * alpha, 200.0, 4.0)
    r1 = analyze(ten_bar, base, config)
    r2 = analyze(ten_bar, scaled, config)
    rtol = config.solver.tolerances.scaling_rtol
    _compare(r2.displacement_vector, r1.displacement_vector / alpha, rtol)
    assert r2.compliance_nmm == pytest.approx(r1.compliance_nmm / alpha, rel=rtol)
    # Uniform area scaling leaves relative stiffnesses unchanged, so member
    # forces are invariant and stresses scale as 1/alpha.
    assert r2.sigma_max_n_per_mm2 == pytest.approx(r1.sigma_max_n_per_mm2 / alpha, rel=rtol)


def test_modulus_scaling(ten_bar: TrussModel, config: ScientificConfig) -> None:
    alpha = 1.5
    base = StructuralParameters.uniform(ten_bar, 70.0, 180.0, 5.0)
    scaled = StructuralParameters.uniform(ten_bar, 70.0, 180.0 * alpha, 5.0)
    r1 = analyze(ten_bar, base, config)
    r2 = analyze(ten_bar, scaled, config)
    rtol = config.solver.tolerances.scaling_rtol
    _compare(r2.displacement_vector, r1.displacement_vector / alpha, rtol)
    assert r2.compliance_nmm == pytest.approx(r1.compliance_nmm / alpha, rel=rtol)
    # Statically indeterminate but linear-elastic with uniform E: force distribution
    # is independent of E, so stresses are invariant under uniform E scaling.
    assert r2.sigma_max_n_per_mm2 == pytest.approx(r1.sigma_max_n_per_mm2, rel=rtol)
