"""Interpolation evaluation and the predetermined competence gate."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import torch

from app.scientific.phase2_errors import InterpolationGateError
from app.scientific.surrogate.config import OUTPUT_NAMES, Phase2Config
from app.scientific.surrogate.metrics import ResponseMetrics, summarize_response
from app.scientific.surrogate.model import StructuralMLP
from app.scientific.surrogate.normalization import NormalizationBundle


@dataclass(frozen=True, slots=True)
class InterpolationEvaluation:
    seed: int
    model_id: str
    predictions: npt.NDArray[np.float64]
    references: npt.NDArray[np.float64]
    metrics: tuple[ResponseMetrics, ...]
    passed_gate: bool
    gate_notes: tuple[str, ...]


def predict_physical(
    model: StructuralMLP,
    inputs: npt.NDArray[np.float64],
    normalization: NormalizationBundle,
    batch_size: int,
) -> npt.NDArray[np.float64]:
    scaled = normalization.inputs.transform(np.asarray(inputs, dtype=np.float64))
    model.eval()
    chunks: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, scaled.shape[0], batch_size):
            batch = torch.tensor(scaled[start : start + batch_size], dtype=torch.float32)
            chunks.append(model(batch).cpu().numpy().astype(np.float64))
    scaled_out = np.vstack(chunks) if chunks else np.empty((0, 3), dtype=np.float64)
    return normalization.outputs.inverse_transform(scaled_out)


def evaluate_interpolation(
    *,
    model: StructuralMLP,
    inputs: npt.NDArray[np.float64],
    references: npt.NDArray[np.float64],
    normalization: NormalizationBundle,
    config: Phase2Config,
    seed: int,
    model_id: str,
) -> InterpolationEvaluation:
    predictions = predict_physical(model, inputs, normalization, config.performance.mlp_batch_size)
    metrics = tuple(
        summarize_response(
            predictions[:, index], references[:, index], name, config.relative_error_epsilon
        )
        for index, name in enumerate(OUTPUT_NAMES)
    )
    notes: list[str] = []
    gate = config.interpolation_gate
    if gate.require_finite and not np.all(np.isfinite(predictions)):
        notes.append("non-finite predictions")
    for item in metrics:
        if item.r2 < gate.min_r2:
            notes.append(f"{item.response} R2={item.r2:.6f} < {gate.min_r2}")
        if item.median_relative_error_pct > gate.max_median_relative_error_pct:
            notes.append(
                f"{item.response} median RE={item.median_relative_error_pct:.6f}% "
                f"> {gate.max_median_relative_error_pct}%"
            )
        if item.max_relative_error_pct > gate.max_catastrophic_relative_error_pct:
            notes.append(
                f"{item.response} max RE={item.max_relative_error_pct:.6f}% "
                f"> {gate.max_catastrophic_relative_error_pct}%"
            )
    passed = not notes
    return InterpolationEvaluation(
        seed=seed,
        model_id=model_id,
        predictions=predictions,
        references=references,
        metrics=metrics,
        passed_gate=passed,
        gate_notes=tuple(notes),
    )


def require_interpolation_competence(
    evaluations: tuple[InterpolationEvaluation, ...], config: Phase2Config
) -> None:
    if config.interpolation_gate.all_seeds_must_pass and any(
        not item.passed_gate for item in evaluations
    ):
        details = [
            f"{item.model_id}: {item.gate_notes}" for item in evaluations if not item.passed_gate
        ]
        raise InterpolationGateError("interpolation competence gate failed: " + "; ".join(details))
