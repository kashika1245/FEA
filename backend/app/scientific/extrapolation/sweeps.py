"""Variable-isolated sweep construction. Exactly one coordinate changes."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.scientific.config import ParameterDomain
from app.scientific.extrapolation.anchors import Anchor
from app.scientific.extrapolation.config import input_index, variable_bounds
from app.scientific.extrapolation.coordinates import DirectionName, extrapolated_value
from app.scientific.surrogate.config import INPUT_NAMES, Phase2Config


@dataclass(frozen=True, slots=True)
class SweepPoint:
    anchor_id: int
    source_sample_id: int
    variable: str
    direction: str
    delta: float
    inputs: tuple[float, ...]


def build_variable_wise_points(
    anchors: tuple[Anchor, ...],
    config: Phase2Config,
    domain: ParameterDomain,
    *,
    variables: tuple[str, ...] | None = None,
    directions: tuple[str, ...] | None = None,
    deltas: tuple[float, ...] | None = None,
) -> tuple[SweepPoint, ...]:
    selected_variables = variables if variables is not None else config.extrapolation.variables
    selected_directions = directions if directions is not None else config.extrapolation.directions
    selected_deltas = deltas if deltas is not None else config.extrapolation.deltas
    points: list[SweepPoint] = []
    for anchor in anchors:
        base = np.asarray(anchor.values, dtype=np.float64)
        for variable in selected_variables:
            xmin, xmax = variable_bounds(domain, variable)
            index = input_index(variable)
            for direction in selected_directions:
                for delta in selected_deltas:
                    vector = base.copy()
                    if direction not in {"lower", "upper"}:
                        raise ValueError(f"invalid direction {direction}")
                    typed_direction: DirectionName = "lower" if direction == "lower" else "upper"
                    vector[index] = extrapolated_value(xmin, xmax, typed_direction, delta)
                    points.append(
                        SweepPoint(
                            anchor_id=anchor.anchor_id,
                            source_sample_id=anchor.source_sample_id,
                            variable=variable,
                            direction=direction,
                            delta=float(delta),
                            inputs=tuple(float(value) for value in vector),
                        )
                    )
    return tuple(points)


def assert_variable_isolation(point: SweepPoint, anchor: Anchor) -> None:
    for name, value, original in zip(INPUT_NAMES, point.inputs, anchor.values, strict=True):
        if name == point.variable:
            continue
        if value != original:
            raise AssertionError(f"non-target variable {name} changed")
