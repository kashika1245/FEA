"""Members, supports, and load placement. Magnitudes are not stored here."""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.scientific.exceptions import InvalidLoadError, InvalidTopologyError
from app.scientific.units import require_finite

_DIRECTION_UNIT_TOLERANCE = 1e-12


@dataclass(frozen=True, slots=True)
class Member:
    member_id: int
    node_i: int
    node_j: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.member_id, int)
            or isinstance(self.member_id, bool)
            or self.member_id < 1
        ):
            raise InvalidTopologyError(
                f"member_id must be a positive integer, got {self.member_id!r}"
            )
        if not isinstance(self.node_i, int) or isinstance(self.node_i, bool) or self.node_i < 1:
            raise InvalidTopologyError(f"member {self.member_id} node_i must be a positive integer")
        if not isinstance(self.node_j, int) or isinstance(self.node_j, bool) or self.node_j < 1:
            raise InvalidTopologyError(f"member {self.member_id} node_j must be a positive integer")
        if self.node_i == self.node_j:
            raise InvalidTopologyError(
                f"member {self.member_id} connects node {self.node_i} to itself"
            )


@dataclass(frozen=True, slots=True)
class Support:
    support_id: int
    node_id: int
    restrain_ux: bool
    restrain_uy: bool

    def __post_init__(self) -> None:
        if (
            not isinstance(self.support_id, int)
            or isinstance(self.support_id, bool)
            or self.support_id < 1
        ):
            raise InvalidTopologyError(
                f"support_id must be a positive integer, got {self.support_id!r}"
            )
        if not isinstance(self.node_id, int) or isinstance(self.node_id, bool) or self.node_id < 1:
            raise InvalidTopologyError(
                f"support {self.support_id} node_id must be a positive integer"
            )
        if not self.restrain_ux and not self.restrain_uy:
            raise InvalidTopologyError(
                f"support {self.support_id} restrains no DOF at node {self.node_id}"
            )


@dataclass(frozen=True, slots=True)
class LoadSpec:
    """Location and unit direction of an applied concentrated load. Magnitude is a parameter."""

    load_id: int
    node_id: int
    direction_x: float
    direction_y: float

    def __post_init__(self) -> None:
        if not isinstance(self.load_id, int) or isinstance(self.load_id, bool) or self.load_id < 1:
            raise InvalidLoadError(f"load_id must be a positive integer, got {self.load_id!r}")
        if not isinstance(self.node_id, int) or isinstance(self.node_id, bool) or self.node_id < 1:
            raise InvalidLoadError(f"load {self.load_id} node_id must be a positive integer")
        dx = require_finite(self.direction_x, f"load {self.load_id} direction_x")
        dy = require_finite(self.direction_y, f"load {self.load_id} direction_y")
        norm = math.hypot(dx, dy)
        if norm == 0.0:
            raise InvalidLoadError(f"load {self.load_id} has zero direction vector")
        if abs(norm - 1.0) > _DIRECTION_UNIT_TOLERANCE:
            raise InvalidLoadError(
                f"load {self.load_id} direction must be a unit vector, got norm={norm}"
            )
        object.__setattr__(self, "direction_x", dx)
        object.__setattr__(self, "direction_y", dy)
