"""Physical-unit interpolation and residual metrics."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from app.scientific.phase2_errors import SurrogateError
from app.scientific.surrogate.config import OUTPUT_NAMES


@dataclass(frozen=True, slots=True)
class ResponseMetrics:
    response: str
    mae: float
    rmse: float
    mean_relative_error_pct: float
    median_relative_error_pct: float
    max_relative_error_pct: float
    mean_signed_error: float
    median_signed_error: float
    r2: float
    n: int


def signed_error(
    prediction: npt.NDArray[np.float64], reference: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    return np.asarray(prediction, dtype=np.float64) - np.asarray(reference, dtype=np.float64)


def absolute_error(
    prediction: npt.NDArray[np.float64], reference: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    return np.abs(signed_error(prediction, reference))


def relative_error_pct(
    prediction: npt.NDArray[np.float64],
    reference: npt.NDArray[np.float64],
    epsilon: float,
) -> npt.NDArray[np.float64]:
    if epsilon <= 0.0:
        raise SurrogateError("relative-error epsilon must be positive")
    denom = np.abs(np.asarray(reference, dtype=np.float64)) + epsilon
    return 100.0 * absolute_error(prediction, reference) / denom


def r_squared(prediction: npt.NDArray[np.float64], reference: npt.NDArray[np.float64]) -> float:
    reference = np.asarray(reference, dtype=np.float64)
    prediction = np.asarray(prediction, dtype=np.float64)
    residual = np.sum((reference - prediction) ** 2)
    centered = np.sum((reference - np.mean(reference)) ** 2)
    if centered == 0.0:
        return 1.0 if residual == 0.0 else 0.0
    return float(1.0 - residual / centered)


def summarize_response(
    prediction: npt.NDArray[np.float64],
    reference: npt.NDArray[np.float64],
    response: str,
    epsilon: float,
) -> ResponseMetrics:
    if response not in OUTPUT_NAMES:
        raise SurrogateError(f"unknown response {response}")
    pred = np.asarray(prediction, dtype=np.float64)
    ref = np.asarray(reference, dtype=np.float64)
    if pred.shape != ref.shape:
        raise SurrogateError("prediction/reference shape mismatch")
    if not np.all(np.isfinite(pred)) or not np.all(np.isfinite(ref)):
        raise SurrogateError(f"non-finite values in {response} interpolation metrics")
    signed = signed_error(pred, ref)
    abs_err = np.abs(signed)
    rel = relative_error_pct(pred, ref, epsilon)
    return ResponseMetrics(
        response=response,
        mae=float(np.mean(abs_err)),
        rmse=float(np.sqrt(np.mean(signed**2))),
        mean_relative_error_pct=float(np.mean(rel)),
        median_relative_error_pct=float(np.median(rel)),
        max_relative_error_pct=float(np.max(rel)),
        mean_signed_error=float(np.mean(signed)),
        median_signed_error=float(np.median(signed)),
        r2=r_squared(pred, ref),
        n=int(pred.size),
    )
