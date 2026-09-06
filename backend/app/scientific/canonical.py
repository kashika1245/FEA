"""The single canonical 10-bar planar truss. Do not duplicate these numbers elsewhere."""

from __future__ import annotations

from app.scientific.config import (
    NumericalTolerances,
    ScientificConfig,
    load_default_scientific_config,
)
from app.scientific.exceptions import InvalidGeometryError, InvalidTopologyError
from app.scientific.geometry import Node
from app.scientific.model import TrussModel
from app.scientific.topology import LoadSpec, Member, Support

GEOMETRY_VERSION = "tenbar.cantilever.v1"

# Exact conversion of the classic 360 inch bay: 360 * 25.4 = 9144 mm.
BAY_LENGTH_MM = 9144.0

CANONICAL_NODES: tuple[Node, ...] = (
    Node(1, 2.0 * BAY_LENGTH_MM, BAY_LENGTH_MM),
    Node(2, 2.0 * BAY_LENGTH_MM, 0.0),
    Node(3, BAY_LENGTH_MM, BAY_LENGTH_MM),
    Node(4, BAY_LENGTH_MM, 0.0),
    Node(5, 0.0, BAY_LENGTH_MM),
    Node(6, 0.0, 0.0),
)

CANONICAL_MEMBERS: tuple[Member, ...] = (
    Member(1, 5, 3),
    Member(2, 3, 1),
    Member(3, 6, 4),
    Member(4, 4, 2),
    Member(5, 3, 4),
    Member(6, 1, 2),
    Member(7, 5, 4),
    Member(8, 6, 3),
    Member(9, 3, 2),
    Member(10, 4, 1),
)

CANONICAL_SUPPORTS: tuple[Support, ...] = (
    Support(1, 5, restrain_ux=True, restrain_uy=True),
    Support(2, 6, restrain_ux=True, restrain_uy=True),
)

CANONICAL_LOADS: tuple[LoadSpec, ...] = (LoadSpec(1, 2, direction_x=0.0, direction_y=-1.0),)

CANONICAL_NODE_COUNT = 6
CANONICAL_MEMBER_COUNT = 10


def canonical_ten_bar_truss(
    tolerances: NumericalTolerances | None = None,
    config: ScientificConfig | None = None,
) -> TrussModel:
    """Return the frozen Paper A 10-bar truss.

    All dataset generation, reports, and later frontend consumers must call this factory
    rather than reconstructing coordinates locally.
    """

    if tolerances is None:
        resolved = config if config is not None else load_default_scientific_config()
        tolerances = resolved.solver.tolerances
        geometry_version = resolved.geometry_version
    else:
        geometry_version = GEOMETRY_VERSION if config is None else config.geometry_version
    if geometry_version != GEOMETRY_VERSION:
        raise InvalidGeometryError(
            f"configuration geometry_version {geometry_version!r} does not match "
            f"canonical {GEOMETRY_VERSION!r}"
        )
    model = TrussModel(
        nodes=CANONICAL_NODES,
        members=CANONICAL_MEMBERS,
        supports=CANONICAL_SUPPORTS,
        loads=CANONICAL_LOADS,
        geometry_version=GEOMETRY_VERSION,
        min_length_mm=tolerances.min_length_mm,
    )
    _assert_canonical_invariants(model)
    return model


def _assert_canonical_invariants(model: TrussModel) -> None:
    if model.n_nodes != CANONICAL_NODE_COUNT:
        raise InvalidTopologyError(f"canonical truss must have 6 nodes, got {model.n_nodes}")
    if model.n_members != CANONICAL_MEMBER_COUNT:
        raise InvalidTopologyError(f"canonical truss must have 10 members, got {model.n_members}")
    if model.node_ids != (1, 2, 3, 4, 5, 6):
        raise InvalidTopologyError(f"canonical node IDs must be 1..6, got {model.node_ids}")
    if model.member_ids != tuple(range(1, 11)):
        raise InvalidTopologyError(f"canonical member IDs must be 1..10, got {model.member_ids}")
    if model.constrained_dofs() != (8, 9, 10, 11):
        raise InvalidTopologyError(f"unexpected constrained DOFs {model.constrained_dofs()}")
    if model.free_dofs() != (0, 1, 2, 3, 4, 5, 6, 7):
        raise InvalidTopologyError(f"unexpected free DOFs {model.free_dofs()}")
    loaded_nodes = tuple(load.node_id for load in model.loads)
    if loaded_nodes != (2,):
        raise InvalidTopologyError(f"canonical load must be on node 2, got {loaded_nodes}")
