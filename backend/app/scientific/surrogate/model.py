"""Frozen MLP: 12 → 128 → 128 → 128 → 3 with ReLU hidden activations."""

from __future__ import annotations

import numpy as np
import torch
from torch import nn

from app.scientific.phase2_errors import SurrogateError

INPUT_DIM = 12
OUTPUT_DIM = 3
HIDDEN_UNITS = (128, 128, 128)


class StructuralMLP(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(INPUT_DIM, HIDDEN_UNITS[0]),
            nn.ReLU(),
            nn.Linear(HIDDEN_UNITS[0], HIDDEN_UNITS[1]),
            nn.ReLU(),
            nn.Linear(HIDDEN_UNITS[1], HIDDEN_UNITS[2]),
            nn.ReLU(),
            nn.Linear(HIDDEN_UNITS[2], OUTPUT_DIM),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        if inputs.ndim != 2 or inputs.shape[1] != INPUT_DIM:
            raise SurrogateError(f"MLP expects (n, {INPUT_DIM}) inputs, got {tuple(inputs.shape)}")
        output: torch.Tensor = self.net(inputs)
        return output


def build_mlp() -> StructuralMLP:
    return StructuralMLP()


def assert_architecture(model: StructuralMLP) -> None:
    linear_layers = [module for module in model.net if isinstance(module, nn.Linear)]
    shapes = [(layer.in_features, layer.out_features) for layer in linear_layers]
    expected = [(12, 128), (128, 128), (128, 128), (128, 3)]
    if shapes != expected:
        raise SurrogateError(f"architecture {shapes} does not match frozen {expected}")
    activations = [type(module).__name__ for module in model.net if isinstance(module, nn.ReLU)]
    if activations != ["ReLU", "ReLU", "ReLU"]:
        raise SurrogateError("hidden activations must be exactly three ReLU layers")


def state_to_numpy(model: StructuralMLP) -> dict[str, np.ndarray]:
    return {key: value.detach().cpu().numpy() for key, value in model.state_dict().items()}


def load_numpy_state(model: StructuralMLP, weights: dict[str, np.ndarray]) -> StructuralMLP:
    tensor_state = {key: torch.tensor(value) for key, value in weights.items()}
    model.load_state_dict(tensor_state, strict=True)
    model.eval()
    return model
