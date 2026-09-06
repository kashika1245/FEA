"""Deterministic five-seed MLP training on the train split only."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import torch
from torch.utils.data import DataLoader, TensorDataset

from app.scientific.phase2_errors import SurrogateError
from app.scientific.surrogate.config import Phase2Config
from app.scientific.surrogate.model import (
    StructuralMLP,
    assert_architecture,
    build_mlp,
    state_to_numpy,
)
from app.scientific.surrogate.normalization import NormalizationBundle
from app.scientific.surrogate.reproducibility import (
    configure_deterministic_runtime,
    hash_weight_map,
)


@dataclass(frozen=True, slots=True)
class SeedTrainingResult:
    seed: int
    model_id: str
    architecture: str
    optimizer: str
    learning_rate: float
    batch_size: int
    epoch_count: int
    stopping_epoch: int
    training_loss: float
    validation_loss: float
    best_validation_loss: float
    dataset_hash: str
    normalization_hash: str
    software_version: str
    model_hash: str
    weights: dict[str, np.ndarray]


def _batches(
    inputs: npt.NDArray[np.float64],
    outputs: npt.NDArray[np.float64],
    batch_size: int,
    seed: int,
    shuffle: bool,
) -> DataLoader[tuple[torch.Tensor, torch.Tensor]]:
    dataset = TensorDataset(
        torch.tensor(inputs, dtype=torch.float32),
        torch.tensor(outputs, dtype=torch.float32),
    )
    generator = torch.Generator()
    generator.manual_seed(seed)
    loader: DataLoader[tuple[torch.Tensor, torch.Tensor]] = DataLoader(
        dataset,  # type: ignore[arg-type]
        batch_size=batch_size,
        shuffle=shuffle,
        generator=generator if shuffle else None,
        drop_last=False,
    )
    return loader


def train_one_seed(
    *,
    train_inputs: npt.NDArray[np.float64],
    train_outputs: npt.NDArray[np.float64],
    validation_inputs: npt.NDArray[np.float64],
    validation_outputs: npt.NDArray[np.float64],
    normalization: NormalizationBundle,
    config: Phase2Config,
    seed: int,
    dataset_hash: str,
) -> SeedTrainingResult:
    if train_inputs.shape[0] != train_outputs.shape[0]:
        raise SurrogateError("train input/output row counts differ")
    configure_deterministic_runtime(seed)
    model = build_mlp()
    assert_architecture(model)
    x_train = normalization.inputs.transform(train_inputs)
    y_train = normalization.outputs.transform(train_outputs)
    x_val = normalization.inputs.transform(validation_inputs)
    y_val = normalization.outputs.transform(validation_outputs)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.surrogate.learning_rate)
    loss_fn = torch.nn.MSELoss()
    loader = _batches(x_train, y_train, config.surrogate.batch_size, seed, shuffle=True)
    best_state = state_to_numpy(model)
    best_val = float("inf")
    best_epoch = 0
    stale = 0
    last_val = float("inf")
    last_epoch = 0
    x_val_t = torch.tensor(x_val, dtype=torch.float32)
    y_val_t = torch.tensor(y_val, dtype=torch.float32)
    for epoch in range(1, config.surrogate.max_epochs + 1):
        model.train()
        for batch_x, batch_y in loader:
            optimizer.zero_grad(set_to_none=True)
            pred = model(batch_x)
            loss = loss_fn(pred, batch_y)
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.no_grad():
            last_val = float(loss_fn(model(x_val_t), y_val_t).item())
        last_epoch = epoch
        if last_val < best_val:
            best_val = last_val
            best_epoch = epoch
            best_state = state_to_numpy(model)
            stale = 0
        else:
            stale += 1
            if stale >= config.surrogate.early_stopping_patience:
                break
    restored = StructuralMLP()
    restored.load_state_dict({key: torch.tensor(value) for key, value in best_state.items()})
    restored.eval()
    with torch.no_grad():
        final_train = float(
            loss_fn(
                restored(torch.tensor(x_train, dtype=torch.float32)),
                torch.tensor(y_train, dtype=torch.float32),
            ).item()
        )
        final_val = float(loss_fn(restored(x_val_t), y_val_t).item())
    weights = state_to_numpy(restored)
    model_hash = hash_weight_map(weights)
    return SeedTrainingResult(
        seed=seed,
        model_id=f"mlp-128-128-128-seed{seed}",
        architecture="12-128-128-128-3",
        optimizer="adam",
        learning_rate=config.surrogate.learning_rate,
        batch_size=config.surrogate.batch_size,
        epoch_count=last_epoch,
        stopping_epoch=best_epoch,
        training_loss=final_train,
        validation_loss=final_val,
        best_validation_loss=best_val,
        dataset_hash=dataset_hash,
        normalization_hash=normalization.content_hash(),
        software_version=config.software_version,
        model_hash=model_hash,
        weights=weights,
    )


def rank_by_validation_loss(
    results: tuple[SeedTrainingResult, ...],
) -> tuple[SeedTrainingResult, ...]:
    """Validation-only ranking. Never inspect interpolation or extrapolation."""

    return tuple(sorted(results, key=lambda item: (item.best_validation_loss, item.seed)))
