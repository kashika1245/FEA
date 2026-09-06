"""Named scientific protocol steps used by scripts and tests."""

from __future__ import annotations

from app.scientific.config import ScientificConfig
from app.scientific.experiments.runner import Phase2Runner
from app.scientific.surrogate.config import Phase2Config


def create_runner(
    phase1: ScientificConfig,
    phase2: Phase2Config,
    *,
    experiment_id: str | None = None,
    n_anchors: int | None = None,
    seeds: tuple[int, ...] | None = None,
    variables: tuple[str, ...] | None = None,
    deltas: tuple[float, ...] | None = None,
) -> Phase2Runner:
    return Phase2Runner(
        phase1=phase1,
        phase2=phase2,
        experiment_id=experiment_id,
        n_anchors=n_anchors,
        seeds=seeds,
        variables=variables,
        deltas=deltas,
    )
