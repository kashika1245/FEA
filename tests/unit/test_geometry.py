from __future__ import annotations

import math

import pytest

from app.scientific.canonical import BAY_LENGTH_MM, GEOMETRY_VERSION, canonical_ten_bar_truss
from app.scientific.config import ScientificConfig
from app.scientific.exceptions import InvalidGeometryError, InvalidTopologyError
from app.scientific.geometry import Node
from app.scientific.model import TrussModel
from app.scientific.topology import LoadSpec, Member, Support


def test_canonical_node_count_and_ids(ten_bar: TrussModel) -> None:
    assert ten_bar.n_nodes == 6
    assert ten_bar.node_ids == (1, 2, 3, 4, 5, 6)


def test_canonical_coordinates_are_frozen_bay_multiples(ten_bar: TrussModel) -> None:
    expected = {
        1: (2 * BAY_LENGTH_MM, BAY_LENGTH_MM),
        2: (2 * BAY_LENGTH_MM, 0.0),
        3: (BAY_LENGTH_MM, BAY_LENGTH_MM),
        4: (BAY_LENGTH_MM, 0.0),
        5: (0.0, BAY_LENGTH_MM),
        6: (0.0, 0.0),
    }
    for node in ten_bar.nodes:
        assert node.x_mm == expected[node.node_id][0]
        assert node.y_mm == expected[node.node_id][1]


def test_canonical_geometry_version(ten_bar: TrussModel) -> None:
    assert ten_bar.geometry_version == GEOMETRY_VERSION


def test_member_lengths(ten_bar: TrussModel) -> None:
    chord = {1, 2, 3, 4, 5, 6}
    for geometry in ten_bar.member_geometry():
        if geometry.member_id in chord:
            assert geometry.length_mm == pytest.approx(BAY_LENGTH_MM)
        else:
            assert geometry.length_mm == pytest.approx(BAY_LENGTH_MM * math.sqrt(2.0))


def test_dof_mapping_is_sorted_node_id_order(ten_bar: TrussModel) -> None:
    assert ten_bar.global_dof_ux(1) == 0
    assert ten_bar.global_dof_uy(1) == 1
    assert ten_bar.global_dof_ux(6) == 10
    assert ten_bar.global_dof_uy(6) == 11
    assert ten_bar.n_dof == 12


def test_node_rejects_nan() -> None:
    with pytest.raises(InvalidGeometryError):
        Node(1, float("nan"), 0.0)


def test_zero_length_member_rejected(config: ScientificConfig) -> None:
    with pytest.raises(InvalidGeometryError):
        TrussModel(
            nodes=(Node(1, 0.0, 0.0), Node(2, 0.0, 0.0)),
            members=(Member(1, 1, 2),),
            supports=(Support(1, 1, True, True),),
            loads=(LoadSpec(1, 2, 0.0, -1.0),),
            geometry_version="bad",
            min_length_mm=config.solver.tolerances.min_length_mm,
        )


def test_self_connected_member_rejected() -> None:
    with pytest.raises(InvalidTopologyError):
        Member(1, 3, 3)


def test_duplicate_node_ids_rejected(config: ScientificConfig) -> None:
    with pytest.raises(InvalidTopologyError):
        TrussModel(
            nodes=(Node(1, 0.0, 0.0), Node(1, 10.0, 0.0)),
            members=(Member(1, 1, 2),),
            supports=(Support(1, 1, True, True),),
            loads=(LoadSpec(1, 1, 0.0, -1.0),),
            geometry_version="bad",
            min_length_mm=config.solver.tolerances.min_length_mm,
        )


def test_factory_matches_config_geometry_version(config: ScientificConfig) -> None:
    model = canonical_ten_bar_truss(config=config)
    assert model.geometry_version == config.geometry_version
