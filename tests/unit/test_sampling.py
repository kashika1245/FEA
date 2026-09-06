from __future__ import annotations

import pytest

from app.scientific.config import ScientificConfig
from app.scientific.dataset.sampling import draw_paper_unit_sample, sample_in_domain
from app.scientific.exceptions import InvalidParameterError


def test_samples_stay_in_domain(config: ScientificConfig) -> None:
    domain = config.parameter_domain
    for sample_id in range(1, 51):
        sample = draw_paper_unit_sample(sample_id, 50, config.dataset.random_seed, domain)
        sample_in_domain(sample, domain)
        assert len(sample.areas_mm2) == 10


def test_sampling_is_deterministic(config: ScientificConfig) -> None:
    domain = config.parameter_domain
    first = draw_paper_unit_sample(3, 20, config.dataset.random_seed, domain)
    second = draw_paper_unit_sample(3, 20, config.dataset.random_seed, domain)
    assert first == second


def test_different_seeds_differ(config: ScientificConfig) -> None:
    domain = config.parameter_domain
    a = draw_paper_unit_sample(1, 10, config.dataset.random_seed, domain)
    b = draw_paper_unit_sample(1, 10, config.dataset.random_seed + 1, domain)
    assert a.areas_mm2 != b.areas_mm2 or a.e_gpa != b.e_gpa or a.f_kn != b.f_kn


def test_invalid_sample_id(config: ScientificConfig) -> None:
    with pytest.raises(InvalidParameterError):
        draw_paper_unit_sample(0, 10, 1, config.parameter_domain)
