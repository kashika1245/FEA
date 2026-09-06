from __future__ import annotations

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from app.scientific.config import ScientificConfig
from app.scientific.dataset.sampling import draw_paper_unit_sample, sample_in_domain
from app.scientific.fem.assembly import assemble_global_stiffness, symmetry_residual
from app.scientific.fem.solver import analyze
from app.scientific.model import TrussModel
from app.scientific.parameters import StructuralParameters


def _assert_rel(actual: float, expected: float, rtol: float) -> None:
    scale = max(abs(expected), 1e-15)
    if abs(actual - expected) > rtol * scale:
        raise AssertionError(f"{actual} != {expected} within rtol={rtol}")


@settings(max_examples=25, deadline=None)
@given(sample_id=st.integers(min_value=1, max_value=200))
def test_sampled_parameters_remain_in_training_domain(
    sample_id: int, config: ScientificConfig
) -> None:
    sample = draw_paper_unit_sample(
        sample_id, 200, config.dataset.random_seed, config.parameter_domain
    )
    sample_in_domain(sample, config.parameter_domain)


@settings(max_examples=12, deadline=None)
@given(
    area=st.floats(min_value=50.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    e_gpa=st.floats(min_value=180.0, max_value=220.0, allow_nan=False, allow_infinity=False),
    f_kn=st.floats(min_value=1.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    lam=st.floats(min_value=0.5, max_value=2.0, allow_nan=False, allow_infinity=False),
)
def test_load_and_compliance_scaling_property(
    area: float,
    e_gpa: float,
    f_kn: float,
    lam: float,
    ten_bar: TrussModel,
    config: ScientificConfig,
) -> None:
    base = StructuralParameters.uniform(ten_bar, area, e_gpa, f_kn)
    scaled = StructuralParameters.uniform(ten_bar, area, e_gpa, f_kn * lam)
    r1 = analyze(ten_bar, base, config)
    r2 = analyze(ten_bar, scaled, config)
    rtol = config.solver.tolerances.scaling_rtol
    _assert_rel(r2.u_max_mm, lam * r1.u_max_mm, rtol)
    _assert_rel(r2.compliance_nmm, (lam**2) * r1.compliance_nmm, rtol)
    stiffness = assemble_global_stiffness(ten_bar, base)
    fro = float(np.linalg.norm(stiffness, ord="fro"))
    limit = max(
        config.solver.tolerances.symmetry_atol, config.solver.tolerances.symmetry_rtol * fro
    )
    assert symmetry_residual(stiffness) <= limit
    for geometry in ten_bar.member_geometry():
        assert geometry.length_mm > 0.0
