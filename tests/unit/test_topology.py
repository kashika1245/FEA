from __future__ import annotations

import pytest

from app.scientific.canonical import canonical_ten_bar_truss
from app.scientific.config import ScientificConfig
from app.scientific.exceptions import InvalidLoadError, InvalidTopologyError
from app.scientific.geometry import Node
from app.scientific.model import TrussModel
from app.scientific.topology import LoadSpec, Member, Support


def test_canonical_connectivity(ten_bar: TrussModel) -> None:
    pairs = {(m.member_id, m.node_i, m.node_j) for m in ten_bar.members}
    assert pairs == {
        (1, 5, 3),
        (2, 3, 1),
        (3, 6, 4),
        (4, 4, 2),
        (5, 3, 4),
        (6, 1, 2),
        (7, 5, 4),
        (8, 6, 3),
        (9, 3, 2),
        (10, 4, 1),
    }


def test_canonical_supports_and_load(ten_bar: TrussModel) -> None:
    assert ten_bar.constrained_dofs() == (8, 9, 10, 11)
    assert ten_bar.free_dofs() == (0, 1, 2, 3, 4, 5, 6, 7)
    assert ten_bar.loads[0].node_id == 2
    assert ten_bar.loads[0].direction_x == 0.0
    assert ten_bar.loads[0].direction_y == -1.0


def test_member_unknown_node(config: ScientificConfig) -> None:
    with pytest.raises(InvalidTopologyError):
        TrussModel(
            nodes=(Node(1, 0.0, 0.0), Node(2, 10.0, 0.0)),
            members=(Member(1, 1, 9),),
            supports=(Support(1, 1, True, True),),
            loads=(LoadSpec(1, 2, 1.0, 0.0),),
            geometry_version="bad",
            min_length_mm=config.solver.tolerances.min_length_mm,
        )


def test_non_unit_load_direction_rejected() -> None:
    with pytest.raises(InvalidLoadError):
        LoadSpec(1, 2, 1.0, 1.0)


def test_support_with_no_restraints_rejected() -> None:
    with pytest.raises(InvalidTopologyError):
        Support(1, 1, False, False)


def test_canonical_factory_is_deterministic(config: ScientificConfig) -> None:
    first = canonical_ten_bar_truss(config=config)
    second = canonical_ten_bar_truss(config=config)
    assert first.nodes == second.nodes
    assert first.members == second.members
