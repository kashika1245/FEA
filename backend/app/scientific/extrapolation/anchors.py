"""Deterministic interpolation-test anchors, independent of model error."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.scientific.dataset.schema import DatasetRow
from app.scientific.phase2_errors import ExtrapolationError
from app.scientific.surrogate.config import INPUT_NAMES, Phase2Config
from app.scientific.surrogate.dataset import inputs_of


@dataclass(frozen=True, slots=True)
class Anchor:
    anchor_id: int
    source_sample_id: int
    values: tuple[float, ...]
    selection_method: str
    selection_seed: int
    dataset_hash: str

    def as_mapping(self) -> dict[str, float]:
        return {name: self.values[index] for index, name in enumerate(INPUT_NAMES)}


def select_anchors(
    interpolation_test: tuple[DatasetRow, ...],
    config: Phase2Config,
    dataset_hash: str,
) -> tuple[Anchor, ...]:
    settings = config.anchors
    if len(interpolation_test) < settings.count:
        raise ExtrapolationError(
            f"need {settings.count} interpolation_test rows, have {len(interpolation_test)}"
        )
    source_ids = np.array([row.sample_id for row in interpolation_test], dtype=np.int64)
    matrix = inputs_of(interpolation_test)
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(settings.selection_seed)))
    chosen = rng.choice(len(interpolation_test), size=settings.count, replace=False)
    chosen_sorted = np.sort(chosen)
    anchors: list[Anchor] = []
    for anchor_id, row_index in enumerate(chosen_sorted, start=1):
        values = tuple(float(value) for value in matrix[int(row_index)])
        anchors.append(
            Anchor(
                anchor_id=anchor_id,
                source_sample_id=int(source_ids[int(row_index)]),
                values=values,
                selection_method=settings.selection_method,
                selection_seed=settings.selection_seed,
                dataset_hash=dataset_hash,
            )
        )
    if len({item.source_sample_id for item in anchors}) != settings.count:
        raise ExtrapolationError("anchor selection produced duplicate source sample_id values")
    return tuple(anchors)
