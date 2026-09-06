from __future__ import annotations

import numpy as np
import pytest

from app.scientific.phase2_errors import NormalizationError
from app.scientific.surrogate.normalization import fit_train_only_normalization


def test_train_only_normalization_round_trip() -> None:
    rng = np.random.default_rng(0)
    train_x = rng.normal(size=(200, 12))
    train_y = rng.normal(size=(200, 3)) * np.array([10.0, 100.0, 10000.0])
    bundle = fit_train_only_normalization(train_x, train_y, "hash")
    recovered_x = bundle.inputs.inverse_transform(bundle.inputs.transform(train_x))
    recovered_y = bundle.outputs.inverse_transform(bundle.outputs.transform(train_y))
    assert np.allclose(recovered_x, train_x)
    assert np.allclose(recovered_y, train_y)


def test_extrapolation_points_do_not_alter_normalization() -> None:
    rng = np.random.default_rng(1)
    train_x = rng.uniform(50.0, 100.0, size=(80, 12))
    train_y = rng.uniform(1.0, 10.0, size=(80, 3))
    extra_x = rng.uniform(10.0, 200.0, size=(20, 12))
    extra_y = rng.uniform(1.0, 10.0, size=(20, 3))
    base = fit_train_only_normalization(train_x, train_y, "hash")
    contaminated = fit_train_only_normalization(
        np.vstack([train_x, extra_x]),
        np.vstack([train_y, extra_y]),
        "hash",
    )
    assert base.content_hash() != contaminated.content_hash()
    again = fit_train_only_normalization(train_x, train_y, "hash")
    assert again.content_hash() == base.content_hash()
    assert base.inputs.training_sample_count == 80


def test_normalization_rejects_nonfinite() -> None:
    x = np.ones((10, 12))
    y = np.ones((10, 3))
    x[0, 0] = np.nan
    with pytest.raises(NormalizationError):
        fit_train_only_normalization(x, y, "hash")
