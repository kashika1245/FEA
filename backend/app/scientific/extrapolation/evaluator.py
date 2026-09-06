"""Actual Phase 1 FEM oracle plus actual MLP evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import numpy.typing as npt

from app.scientific.canonical import canonical_ten_bar_truss
from app.scientific.config import ScientificConfig
from app.scientific.fem.solver import analyze
from app.scientific.model import TrussModel
from app.scientific.parameters import StructuralParameters
from app.scientific.phase2_errors import ExtrapolationError
from app.scientific.surrogate.config import INPUT_NAMES
from app.scientific.surrogate.evaluation import predict_physical
from app.scientific.surrogate.model import StructuralMLP
from app.scientific.surrogate.normalization import NormalizationBundle


@dataclass
class FemCache:
    enabled: bool
    model: TrussModel
    config: ScientificConfig
    store: dict[tuple[float, ...], tuple[float, float, float]] = field(default_factory=dict)

    def evaluate(self, inputs: tuple[float, ...]) -> tuple[float, float, float]:
        if len(inputs) != 12:
            raise ExtrapolationError("FEM input must be the 12 paper-unit coordinates")
        if self.enabled and inputs in self.store:
            return self.store[inputs]
        parameters = StructuralParameters.from_paper_units(
            {member_id: inputs[member_id - 1] for member_id in range(1, 11)},
            inputs[10],
            inputs[11],
        )
        result = analyze(self.model, parameters, self.config)
        values = (result.u_max_mm, result.sigma_max_n_per_mm2, result.compliance_nmm)
        if self.enabled:
            self.store[inputs] = values
        return values


def make_fem_cache(config: ScientificConfig, enabled: bool) -> FemCache:
    return FemCache(enabled=enabled, model=canonical_ten_bar_truss(config=config), config=config)


def evaluate_fem_matrix(
    inputs: npt.NDArray[np.float64],
    cache: FemCache,
) -> npt.NDArray[np.float64]:
    out = np.empty((inputs.shape[0], 3), dtype=np.float64)
    for index, row in enumerate(inputs):
        out[index, :] = cache.evaluate(tuple(float(value) for value in row))
    return out


def evaluate_mlp_matrix(
    inputs: npt.NDArray[np.float64],
    model: StructuralMLP,
    normalization: NormalizationBundle,
    batch_size: int,
) -> npt.NDArray[np.float64]:
    if inputs.shape[1] != len(INPUT_NAMES):
        raise ExtrapolationError("MLP input width must be 12")
    return predict_physical(model, inputs, normalization, batch_size)


def record_failure(
    *,
    experiment_id: str,
    observation_id: str,
    stage: str,
    exc: BaseException,
) -> dict[str, str]:
    return {
        "experiment_id": experiment_id,
        "observation_id": observation_id,
        "stage": stage,
        "exception_type": type(exc).__name__,
        "message": str(exc),
    }
