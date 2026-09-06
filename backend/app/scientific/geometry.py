"""Nodes and coordinate validation."""

from __future__ import annotations

from dataclasses import dataclass

from app.scientific.exceptions import InvalidGeometryError, InvalidParameterError
from app.scientific.units import require_finite


@dataclass(frozen=True, slots=True)
class Node:
    node_id: int
    x_mm: float
    y_mm: float

    def __post_init__(self) -> None:
        if not isinstance(self.node_id, int) or isinstance(self.node_id, bool) or self.node_id < 1:
            raise InvalidGeometryError(f"node_id must be a positive integer, got {self.node_id!r}")
        try:
            object.__setattr__(self, "x_mm", require_finite(self.x_mm, f"node {self.node_id} x"))
            object.__setattr__(self, "y_mm", require_finite(self.y_mm, f"node {self.node_id} y"))
        except InvalidParameterError as exc:
            raise InvalidGeometryError(str(exc)) from exc
