"""Immutable planar truss aggregate: nodes, members, supports, loads, DOF map."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.scientific.exceptions import InvalidGeometryError, InvalidLoadError, InvalidTopologyError
from app.scientific.geometry import Node
from app.scientific.topology import LoadSpec, Member, Support


def dof_ux(node_index: int) -> int:
    """Global u_x DOF for a 0-based node index in the sorted node-id order."""

    return 2 * node_index


def dof_uy(node_index: int) -> int:
    """Global u_y DOF for a 0-based node index in the sorted node-id order."""

    return 2 * node_index + 1


@dataclass(frozen=True, slots=True)
class MemberGeometry:
    member_id: int
    node_i: int
    node_j: int
    length_mm: float
    cosine: float
    sine: float
    dof_indices: tuple[int, int, int, int]


@dataclass(frozen=True, slots=True)
class TrussModel:
    """Validated planar truss. Node IDs determine DOF ordering: sorted IDs, ux then uy."""

    nodes: tuple[Node, ...]
    members: tuple[Member, ...]
    supports: tuple[Support, ...]
    loads: tuple[LoadSpec, ...]
    geometry_version: str
    min_length_mm: float
    _node_index: dict[int, int] = field(init=False, repr=False, compare=False)
    _nodes_by_id: dict[int, Node] = field(init=False, repr=False, compare=False)
    _member_geometry: tuple[MemberGeometry, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        nodes = tuple(sorted(self.nodes, key=lambda item: item.node_id))
        members = tuple(sorted(self.members, key=lambda item: item.member_id))
        supports = tuple(sorted(self.supports, key=lambda item: item.support_id))
        loads = tuple(sorted(self.loads, key=lambda item: item.load_id))
        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(self, "members", members)
        object.__setattr__(self, "supports", supports)
        object.__setattr__(self, "loads", loads)
        _validate_truss(self)
        object.__setattr__(
            self, "_node_index", {node.node_id: i for i, node in enumerate(self.nodes)}
        )
        object.__setattr__(self, "_nodes_by_id", {node.node_id: node for node in self.nodes})
        object.__setattr__(self, "_member_geometry", _compute_member_geometry(self))

    @property
    def n_nodes(self) -> int:
        return len(self.nodes)

    @property
    def n_members(self) -> int:
        return len(self.members)

    @property
    def n_dof(self) -> int:
        return 2 * self.n_nodes

    @property
    def node_ids(self) -> tuple[int, ...]:
        return tuple(node.node_id for node in self.nodes)

    @property
    def member_ids(self) -> tuple[int, ...]:
        return tuple(member.member_id for member in self.members)

    def node_index(self, node_id: int) -> int:
        try:
            return self._node_index[node_id]
        except KeyError as exc:
            raise InvalidTopologyError(f"unknown node_id {node_id}") from exc

    def node_by_id(self, node_id: int) -> Node:
        try:
            return self._nodes_by_id[node_id]
        except KeyError as exc:
            raise InvalidTopologyError(f"unknown node_id {node_id}") from exc

    def global_dof_ux(self, node_id: int) -> int:
        return dof_ux(self.node_index(node_id))

    def global_dof_uy(self, node_id: int) -> int:
        return dof_uy(self.node_index(node_id))

    def member_geometry(self) -> tuple[MemberGeometry, ...]:
        return self._member_geometry

    def constrained_dofs(self) -> tuple[int, ...]:
        constrained: set[int] = set()
        for support in self.supports:
            if support.restrain_ux:
                constrained.add(self.global_dof_ux(support.node_id))
            if support.restrain_uy:
                constrained.add(self.global_dof_uy(support.node_id))
        return tuple(sorted(constrained))

    def free_dofs(self) -> tuple[int, ...]:
        constrained = set(self.constrained_dofs())
        return tuple(dof for dof in range(self.n_dof) if dof not in constrained)


def _validate_truss(model: TrussModel) -> None:
    if model.min_length_mm <= 0.0 or model.min_length_mm != model.min_length_mm:
        raise InvalidGeometryError(
            f"min_length_mm must be a positive finite value, got {model.min_length_mm}"
        )
    if not model.geometry_version:
        raise InvalidGeometryError("geometry_version must be a non-empty string")
    if len(model.nodes) < 2:
        raise InvalidTopologyError("a truss requires at least two nodes")
    if len(model.members) < 1:
        raise InvalidTopologyError("a truss requires at least one member")
    node_ids = [node.node_id for node in model.nodes]
    if len(set(node_ids)) != len(node_ids):
        raise InvalidTopologyError("duplicate node_id")
    member_ids = [member.member_id for member in model.members]
    if len(set(member_ids)) != len(member_ids):
        raise InvalidTopologyError("duplicate member_id")
    support_ids = [support.support_id for support in model.supports]
    if len(set(support_ids)) != len(support_ids):
        raise InvalidTopologyError("duplicate support_id")
    load_ids = [load.load_id for load in model.loads]
    if len(set(load_ids)) != len(load_ids):
        raise InvalidLoadError("duplicate load_id")
    node_id_set = set(node_ids)
    for member in model.members:
        if member.node_i not in node_id_set or member.node_j not in node_id_set:
            raise InvalidTopologyError(
                f"member {member.member_id} references a nonexistent node "
                f"({member.node_i}, {member.node_j})"
            )
    nodes_by_id = {node.node_id: node for node in model.nodes}
    for member in model.members:
        left = nodes_by_id[member.node_i]
        right = nodes_by_id[member.node_j]
        length = math.hypot(right.x_mm - left.x_mm, right.y_mm - left.y_mm)
        if length <= model.min_length_mm:
            raise InvalidGeometryError(
                f"member {member.member_id} has length {length} mm, "
                f"not greater than min_length_mm={model.min_length_mm}"
            )
    if not model.supports:
        raise InvalidTopologyError("at least one support is required")
    if not model.loads:
        raise InvalidLoadError("at least one load specification is required")
    for support in model.supports:
        if support.node_id not in node_id_set:
            raise InvalidTopologyError(
                f"support {support.support_id} references nonexistent node {support.node_id}"
            )
    for load in model.loads:
        if load.node_id not in node_id_set:
            raise InvalidLoadError(
                f"load {load.load_id} references nonexistent node {load.node_id}"
            )


def _compute_member_geometry(model: TrussModel) -> tuple[MemberGeometry, ...]:
    items: list[MemberGeometry] = []
    for member in model.members:
        node_i = model.node_by_id(member.node_i)
        node_j = model.node_by_id(member.node_j)
        dx = node_j.x_mm - node_i.x_mm
        dy = node_j.y_mm - node_i.y_mm
        length = math.hypot(dx, dy)
        cosine = dx / length
        sine = dy / length
        dofs = (
            model.global_dof_ux(member.node_i),
            model.global_dof_uy(member.node_i),
            model.global_dof_ux(member.node_j),
            model.global_dof_uy(member.node_j),
        )
        items.append(
            MemberGeometry(
                member_id=member.member_id,
                node_i=member.node_i,
                node_j=member.node_j,
                length_mm=length,
                cosine=cosine,
                sine=sine,
                dof_indices=dofs,
            )
        )
    return tuple(items)
