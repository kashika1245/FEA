from __future__ import annotations

import numpy as np

from app.scientific.config import load_default_scientific_config
from app.scientific.extrapolation.anchors import select_anchors
from app.scientific.extrapolation.config import variable_bounds
from app.scientific.extrapolation.coordinates import extrapolated_value
from app.scientific.extrapolation.sweeps import (
    assert_variable_isolation,
    build_variable_wise_points,
)
from app.scientific.surrogate.config import load_default_phase2_config
from app.scientific.surrogate.dataset import inputs_of, load_and_validate_phase1_dataset, outputs_of
from app.scientific.surrogate.normalization import fit_train_only_normalization


def test_phase1_dataset_isolation_and_domain() -> None:
    dataset = load_and_validate_phase1_dataset()
    train_ids = {row.sample_id for row in dataset.train}
    val_ids = {row.sample_id for row in dataset.validation}
    test_ids = {row.sample_id for row in dataset.interpolation_test}
    assert not train_ids & val_ids
    assert not train_ids & test_ids
    assert not val_ids & test_ids
    assert len(dataset.train) == 7000


def test_normalization_ignores_non_train_splits() -> None:
    dataset = load_and_validate_phase1_dataset()
    train_only = fit_train_only_normalization(
        inputs_of(dataset.train), outputs_of(dataset.train), dataset.dataset_hash
    )
    with_val = fit_train_only_normalization(
        np.vstack([inputs_of(dataset.train), inputs_of(dataset.validation)]),
        np.vstack([outputs_of(dataset.train), outputs_of(dataset.validation)]),
        dataset.dataset_hash,
    )
    assert train_only.content_hash() != with_val.content_hash()
    assert train_only.inputs.training_sample_count == 7000


def test_anchors_are_interpolation_test_and_error_independent() -> None:
    dataset = load_and_validate_phase1_dataset()
    config = load_default_phase2_config()
    first = select_anchors(dataset.interpolation_test, config, dataset.dataset_hash)
    second = select_anchors(dataset.interpolation_test, config, dataset.dataset_hash)
    assert [anchor.source_sample_id for anchor in first] == [
        anchor.source_sample_id for anchor in second
    ]
    test_ids = {row.sample_id for row in dataset.interpolation_test}
    train_ids = {row.sample_id for row in dataset.train}
    for anchor in first:
        assert anchor.source_sample_id in test_ids
        assert anchor.source_sample_id not in train_ids


def test_delta_positive_is_outside_training_boundary() -> None:
    domain = load_default_scientific_config().parameter_domain
    for name in ("A3", "E", "F"):
        xmin, xmax = variable_bounds(domain, name)
        assert extrapolated_value(xmin, xmax, "upper", 0.05) > xmax
        assert extrapolated_value(xmin, xmax, "lower", 0.05) < xmin


def test_variable_isolation_on_constructed_points() -> None:
    dataset = load_and_validate_phase1_dataset()
    config = load_default_phase2_config()
    anchors = select_anchors(dataset.interpolation_test, config, dataset.dataset_hash)[:2]
    points = build_variable_wise_points(
        anchors,
        config,
        load_default_scientific_config().parameter_domain,
        variables=("A3",),
        deltas=(0.0, 0.5),
    )
    by_id = {anchor.anchor_id: anchor for anchor in anchors}
    for point in points:
        assert_variable_isolation(point, by_id[point.anchor_id])
