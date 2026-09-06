from __future__ import annotations

import numpy as np

from app.scientific.surrogate.metrics import (
    absolute_error,
    relative_error_pct,
    signed_error,
    summarize_response,
)


def test_error_definitions() -> None:
    pred = np.array([3.0, -1.0])
    ref = np.array([1.0, 1.0])
    assert np.allclose(signed_error(pred, ref), [2.0, -2.0])
    assert np.allclose(absolute_error(pred, ref), [2.0, 2.0])
    rel = relative_error_pct(pred, ref, 1e-12)
    assert np.all(rel >= 0.0)
    assert abs(rel[0] - 200.0) < 1e-9


def test_relative_error_uses_documented_epsilon() -> None:
    pred = np.array([1e-15])
    ref = np.array([0.0])
    rel = relative_error_pct(pred, ref, 1e-12)
    assert rel[0] == 100.0 * abs(1e-15) / 1e-12


def test_summarize_response() -> None:
    pred = np.array([1.0, 2.0, 3.0])
    ref = np.array([1.0, 2.0, 3.0])
    metrics = summarize_response(pred, ref, "u_max", 1e-12)
    assert metrics.mae == 0.0
    assert metrics.r2 == 1.0
    assert metrics.median_relative_error_pct == 0.0
