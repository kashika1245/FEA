"""Frozen extrapolation-distance mapping. Distance is always non-negative."""

from __future__ import annotations

from typing import Literal

from app.scientific.phase2_errors import ExtrapolationError

DirectionName = Literal["lower", "upper"]


def extrapolated_value(xmin: float, xmax: float, direction: DirectionName, delta: float) -> float:
    if xmax <= xmin:
        raise ExtrapolationError(f"invalid training interval [{xmin}, {xmax}]")
    if delta < 0.0:
        raise ExtrapolationError(f"distance delta must be non-negative, got {delta}")
    width = xmax - xmin
    if direction == "upper":
        return xmax + delta * width
    if direction == "lower":
        return xmin - delta * width
    raise ExtrapolationError(f"unknown direction {direction}")


def distance_from_value(xmin: float, xmax: float, direction: DirectionName, value: float) -> float:
    width = xmax - xmin
    if width <= 0.0:
        raise ExtrapolationError(f"invalid training interval [{xmin}, {xmax}]")
    if direction == "upper":
        return (value - xmax) / width
    return (xmin - value) / width
