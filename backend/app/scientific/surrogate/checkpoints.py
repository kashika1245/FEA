"""Safe MLP artefacts: JSON metadata + NumPy weight archives. No pickle models."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import numpy as np

from app.scientific.dataset.storage import confine_under_data_root
from app.scientific.phase2_errors import SurrogateError
from app.scientific.reproducibility import canonical_json_bytes
from app.scientific.surrogate.model import StructuralMLP, assert_architecture, load_numpy_state
from app.scientific.surrogate.normalization import NormalizationBundle


def write_checkpoint(
    directory: Path,
    *,
    seed: int,
    weights: dict[str, np.ndarray],
    metadata: dict[str, Any],
    normalization: NormalizationBundle,
    repo_root: Path | None = None,
) -> Path:
    target = confine_under_data_root(directory, repo_root)
    target.mkdir(parents=True, exist_ok=True)
    weight_path = target / "weights.npz"
    meta_path = target / "metadata.json"
    norm_path = target / "normalization.json"
    np.savez(weight_path, **cast(dict[str, Any], weights))
    meta_path.write_bytes(canonical_json_bytes(metadata))
    norm_path.write_text(normalization.model_dump_json(indent=2), encoding="utf-8")
    return target


def read_weights(directory: Path, repo_root: Path | None = None) -> dict[str, np.ndarray]:
    target = confine_under_data_root(directory, repo_root)
    weight_path = target / "weights.npz"
    if not weight_path.is_file():
        raise SurrogateError(f"missing weight archive: {weight_path}")
    with np.load(weight_path) as archive:
        return {key: np.asarray(archive[key]) for key in archive.files}


def restore_model(directory: Path, repo_root: Path | None = None) -> StructuralMLP:
    weights = read_weights(directory, repo_root)
    model = StructuralMLP()
    load_numpy_state(model, weights)
    assert_architecture(model)
    return model


def read_normalization(directory: Path, repo_root: Path | None = None) -> NormalizationBundle:
    target = confine_under_data_root(directory, repo_root)
    path = target / "normalization.json"
    if not path.is_file():
        raise SurrogateError(f"missing normalization artefact: {path}")
    return NormalizationBundle.model_validate_json(path.read_text(encoding="utf-8"))
