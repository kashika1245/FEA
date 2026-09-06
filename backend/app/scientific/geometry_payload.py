"""Canonical JSON description of the frozen 10-bar geometry for hashing."""

from __future__ import annotations

from typing import Any

from app.scientific.canonical import (
    BAY_LENGTH_MM,
    CANONICAL_LOADS,
    CANONICAL_MEMBERS,
    CANONICAL_NODES,
    CANONICAL_SUPPORTS,
    GEOMETRY_VERSION,
)
from app.scientific.model import TrussModel


def geometry_hash_payload(model: TrussModel) -> dict[str, Any]:
    return {
        "geometry_version": model.geometry_version,
        "bay_length_mm": BAY_LENGTH_MM,
        "canonical_version_constant": GEOMETRY_VERSION,
        "nodes": [{"node_id": n.node_id, "x_mm": n.x_mm, "y_mm": n.y_mm} for n in CANONICAL_NODES],
        "members": [
            {"member_id": m.member_id, "node_i": m.node_i, "node_j": m.node_j}
            for m in CANONICAL_MEMBERS
        ],
        "supports": [
            {
                "support_id": s.support_id,
                "node_id": s.node_id,
                "restrain_ux": s.restrain_ux,
                "restrain_uy": s.restrain_uy,
            }
            for s in CANONICAL_SUPPORTS
        ],
        "loads": [
            {
                "load_id": load.load_id,
                "node_id": load.node_id,
                "direction_x": load.direction_x,
                "direction_y": load.direction_y,
            }
            for load in CANONICAL_LOADS
        ],
        "dof_map": {
            str(node.node_id): {
                "ux": model.global_dof_ux(node.node_id),
                "uy": model.global_dof_uy(node.node_id),
            }
            for node in model.nodes
        },
    }
