"""Train-only z-score normalization for inputs and outputs."""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt
from pydantic import BaseModel, ConfigDict, Field

from app.scientific.phase2_errors import NormalizationError
from app.scientific.surrogate.config import INPUT_NAMES, OUTPUT_NAMES
from app.scientific.surrogate.reproducibility import hash_mapping

STD_FLOOR = 1.0e-12


class FeatureScaler(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    feature_names: tuple[str, ...]
    mean: tuple[float, ...]
    std: tuple[float, ...]
    training_sample_count: int = Field(gt=0)
    method: str
    dataset_hash: str
    space: str

    def transform(self, values: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        array = np.asarray(values, dtype=np.float64)
        if array.ndim != 2 or array.shape[1] != len(self.feature_names):
            raise NormalizationError(
                f"expected (n, {len(self.feature_names)}) array, got {array.shape}"
            )
        mean = np.asarray(self.mean, dtype=np.float64)
        std = np.asarray(self.std, dtype=np.float64)
        return (array - mean) / std

    def inverse_transform(self, values: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        array = np.asarray(values, dtype=np.float64)
        if array.ndim != 2 or array.shape[1] != len(self.feature_names):
            raise NormalizationError(
                f"expected (n, {len(self.feature_names)}) array, got {array.shape}"
            )
        mean = np.asarray(self.mean, dtype=np.float64)
        std = np.asarray(self.std, dtype=np.float64)
        return array * std + mean

    def content_hash(self) -> str:
        return hash_mapping(self.model_dump())


class NormalizationBundle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    inputs: FeatureScaler
    outputs: FeatureScaler
    dataset_hash: str

    def content_hash(self) -> str:
        return hash_mapping(
            {
                "inputs": self.inputs.model_dump(),
                "outputs": self.outputs.model_dump(),
                "dataset_hash": self.dataset_hash,
            }
        )


def _fit_zscore(
    matrix: npt.NDArray[np.float64],
    names: tuple[str, ...],
    dataset_hash: str,
    space: str,
) -> FeatureScaler:
    if matrix.ndim != 2 or matrix.shape[0] < 2 or matrix.shape[1] != len(names):
        raise NormalizationError(f"cannot fit {space} scaler on shape {matrix.shape}")
    if not np.all(np.isfinite(matrix)):
        raise NormalizationError(f"{space} training matrix contains non-finite values")
    mean = matrix.mean(axis=0)
    std = matrix.std(axis=0, ddof=0)
    if np.any(std < STD_FLOOR):
        raise NormalizationError(f"{space} standard deviation below floor {STD_FLOOR}")
    return FeatureScaler(
        feature_names=names,
        mean=tuple(float(value) for value in mean),
        std=tuple(float(value) for value in std),
        training_sample_count=int(matrix.shape[0]),
        method="zscore",
        dataset_hash=dataset_hash,
        space=space,
    )


def fit_train_only_normalization(
    train_inputs: npt.NDArray[np.float64],
    train_outputs: npt.NDArray[np.float64],
    dataset_hash: str,
) -> NormalizationBundle:
    inputs = _fit_zscore(train_inputs, INPUT_NAMES, dataset_hash, "inputs")
    outputs = _fit_zscore(train_outputs, OUTPUT_NAMES, dataset_hash, "outputs")
    return NormalizationBundle(inputs=inputs, outputs=outputs, dataset_hash=dataset_hash)


def assert_train_only_fit(
    bundle: NormalizationBundle,
    forbidden_inputs: npt.NDArray[np.float64] | None = None,
) -> None:
    """Documented invariant: callers must pass only the train split into the fitter."""

    if bundle.inputs.training_sample_count != bundle.outputs.training_sample_count:
        raise NormalizationError("input and output scalers used different training counts")
    if (
        forbidden_inputs is not None
        and forbidden_inputs.size
        and bundle.inputs.training_sample_count == int(forbidden_inputs.shape[0])
    ):
        raise NormalizationError("normalization training count equals a forbidden split size")


def scaler_payload(bundle: NormalizationBundle) -> dict[str, Any]:
    return bundle.model_dump()
