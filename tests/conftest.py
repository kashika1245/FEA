from __future__ import annotations

import pytest

from app.scientific.canonical import canonical_ten_bar_truss
from app.scientific.config import ScientificConfig, load_default_scientific_config
from app.scientific.geometry import Node
from app.scientific.model import TrussModel
from app.scientific.topology import LoadSpec, Member, Support


@pytest.fixture(scope="session")
def config() -> ScientificConfig:
    return load_default_scientific_config()


@pytest.fixture(scope="session")
def ten_bar(config: ScientificConfig) -> TrussModel:
    return canonical_ten_bar_truss(config=config)


def single_bar_model(min_length_mm: float) -> TrussModel:
    """Unit axial bar along +x, pinned at node 1, roller (uy) at node 2, Fx at node 2."""

    return TrussModel(
        nodes=(Node(1, 0.0, 0.0), Node(2, 1000.0, 0.0)),
        members=(Member(1, 1, 2),),
        supports=(
            Support(1, 1, restrain_ux=True, restrain_uy=True),
            Support(2, 2, restrain_ux=False, restrain_uy=True),
        ),
        loads=(LoadSpec(1, 2, direction_x=1.0, direction_y=0.0),),
        geometry_version="test.single-bar.v1",
        min_length_mm=min_length_mm,
    )
