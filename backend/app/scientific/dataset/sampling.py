"""Deterministic independent uniform sampling of Paper A inputs."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.scientific.config import ParameterDomain
from app.scientific.exceptions import InvalidParameterError


@dataclass(frozen=True, slots=True)
class PaperUnitSample:
    sample_id: int
    areas_mm2: tuple[float, ...]
    e_gpa: float
    f_kn: float


def parameter_rng(sample_id: int, n_samples: int, seed: int) -> np.random.Generator:
    if sample_id < 1 or sample_id > n_samples:
        raise InvalidParameterError(f"sample_id {sample_id} is outside 1..{n_samples}")
    children = np.random.SeedSequence(seed).spawn(n_samples)
    return np.random.Generator(np.random.PCG64(children[sample_id - 1]))


def split_rng(seed: int) -> np.random.Generator:
    """Independent of per-sample spawn(n_samples). SeedSequence([seed, 1])."""

    return np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed, 1])))


def draw_paper_unit_sample(
    sample_id: int,
    n_samples: int,
    seed: int,
    domain: ParameterDomain,
    n_members: int = 10,
) -> PaperUnitSample:
    rng = parameter_rng(sample_id, n_samples, seed)
    areas = tuple(
        float(rng.uniform(domain.area_mm2.min, domain.area_mm2.max)) for _ in range(n_members)
    )
    e_gpa = float(rng.uniform(domain.youngs_modulus_gpa.min, domain.youngs_modulus_gpa.max))
    f_kn = float(rng.uniform(domain.load_kn.min, domain.load_kn.max))
    return PaperUnitSample(sample_id=sample_id, areas_mm2=areas, e_gpa=e_gpa, f_kn=f_kn)


def sample_in_domain(sample: PaperUnitSample, domain: ParameterDomain) -> None:
    for index, area in enumerate(sample.areas_mm2, start=1):
        if not (domain.area_mm2.min <= area <= domain.area_mm2.max):
            raise InvalidParameterError(f"A{index}={area} outside training domain")
    if not (domain.youngs_modulus_gpa.min <= sample.e_gpa <= domain.youngs_modulus_gpa.max):
        raise InvalidParameterError(f"E={sample.e_gpa} GPa outside training domain")
    if not (domain.load_kn.min <= sample.f_kn <= domain.load_kn.max):
        raise InvalidParameterError(f"F={sample.f_kn} kN outside training domain")
