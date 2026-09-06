"""Controlled A3 + F combined extrapolation. One case study, not the full domain."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.scientific.config import ParameterDomain
from app.scientific.extrapolation.anchors import Anchor
from app.scientific.extrapolation.config import input_index, variable_bounds
from app.scientific.extrapolation.coordinates import extrapolated_value
from app.scientific.surrogate.config import Phase2Config


@dataclass(frozen=True, slots=True)
class CombinedPoint:
    anchor_id: int
    source_sample_id: int
    direction_a3: str
    direction_f: str
    delta_a3: float
    delta_f: float
    inputs: tuple[float, ...]


def build_combined_points(
    anchors: tuple[Anchor, ...],
    config: Phase2Config,
    domain: ParameterDomain,
) -> tuple[CombinedPoint, ...]:
    a3_index = input_index("A3")
    f_index = input_index("F")
    a3_min, a3_max = variable_bounds(domain, "A3")
    f_min, f_max = variable_bounds(domain, "F")
    points: list[CombinedPoint] = []
    for anchor in anchors:
        base = np.asarray(anchor.values, dtype=np.float64)
        for direction_a3 in config.combined.directions_a3:
            for direction_f in config.combined.directions_f:
                for delta_a3 in config.combined.deltas_a3:
                    for delta_f in config.combined.deltas_f:
                        vector = base.copy()
                        vector[a3_index] = extrapolated_value(
                            a3_min, a3_max, direction_a3, delta_a3
                        )
                        vector[f_index] = extrapolated_value(f_min, f_max, direction_f, delta_f)
                        points.append(
                            CombinedPoint(
                                anchor_id=anchor.anchor_id,
                                source_sample_id=anchor.source_sample_id,
                                direction_a3=direction_a3,
                                direction_f=direction_f,
                                delta_a3=float(delta_a3),
                                delta_f=float(delta_f),
                                inputs=tuple(float(value) for value in vector),
                            )
                        )
    return tuple(points)
