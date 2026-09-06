from __future__ import annotations

import torch

from app.scientific.surrogate.model import INPUT_DIM, OUTPUT_DIM, assert_architecture, build_mlp


def test_frozen_mlp_shape() -> None:
    model = build_mlp()
    assert_architecture(model)
    output = model(torch.zeros(4, INPUT_DIM))
    assert tuple(output.shape) == (4, OUTPUT_DIM)
