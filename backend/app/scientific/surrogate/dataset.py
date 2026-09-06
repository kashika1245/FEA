"""Phase 1 dataset loading, integrity verification, and strict split isolation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import numpy.typing as npt

from app.scientific.config import ScientificConfig, load_default_scientific_config
from app.scientific.dataset.metadata import DatasetMetadata
from app.scientific.dataset.schema import COLUMN_ORDER, DatasetRow
from app.scientific.dataset.storage import read_parquet
from app.scientific.dataset.validation import require_quality, validate_dataset_rows
from app.scientific.phase2_errors import Phase1IntegrityError
from app.scientific.reproducibility import repo_root_from_package, sha256_file
from app.scientific.surrogate.config import INPUT_NAMES, OUTPUT_NAMES

EXPECTED_DATASET_ID = "paper-a.phase1.v1-n10000-seed20260905"
EXPECTED_DATASET_HASH = "a78de261b1686363ed6d830cd370b763800da657bce0991047fe43fb9504e99e"
EXPECTED_CONFIGURATION_HASH = "449e9b7cfd50bcce39c9293bb5f12b63724d49ae44cc0cd427290b3e998e4752"
EXPECTED_GEOMETRY_VERSION = "tenbar.cantilever.v1"
EXPECTED_SOLVER_VERSION = "planar-truss-direct-stiffness.v1"
EXPECTED_SPLIT_COUNTS = {"train": 7000, "validation": 1500, "interpolation_test": 1500}


@dataclass(frozen=True, slots=True)
class LoadedPhase1Dataset:
    rows: tuple[DatasetRow, ...]
    metadata: DatasetMetadata
    parquet_path: Path
    dataset_hash: str
    train: tuple[DatasetRow, ...]
    validation: tuple[DatasetRow, ...]
    interpolation_test: tuple[DatasetRow, ...]


def default_phase1_dataset_dir(repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else repo_root_from_package()
    return root / "data" / "datasets" / EXPECTED_DATASET_ID


def rows_to_matrix(rows: tuple[DatasetRow, ...], names: tuple[str, ...]) -> npt.NDArray[np.float64]:
    matrix = np.empty((len(rows), len(names)), dtype=np.float64)
    for index, row in enumerate(rows):
        payload = row.to_ordered_dict()
        matrix[index, :] = [float(payload[name]) for name in names]
    return matrix


def inputs_of(rows: tuple[DatasetRow, ...]) -> npt.NDArray[np.float64]:
    return rows_to_matrix(rows, INPUT_NAMES)


def outputs_of(rows: tuple[DatasetRow, ...]) -> npt.NDArray[np.float64]:
    return rows_to_matrix(rows, OUTPUT_NAMES)


def load_and_validate_phase1_dataset(
    dataset_dir: Path | None = None,
    config: ScientificConfig | None = None,
    repo_root: Path | None = None,
) -> LoadedPhase1Dataset:
    root = repo_root if repo_root is not None else repo_root_from_package()
    resolved_config = config if config is not None else load_default_scientific_config()
    directory = dataset_dir if dataset_dir is not None else default_phase1_dataset_dir(root)
    parquet_path = directory / "dataset.parquet"
    metadata_path = directory / "metadata.json"
    if not parquet_path.is_file():
        raise Phase1IntegrityError(f"Phase 1 parquet is missing: {parquet_path}")
    if not metadata_path.is_file():
        raise Phase1IntegrityError(f"Phase 1 metadata is missing: {metadata_path}")
    metadata = DatasetMetadata.model_validate_json(metadata_path.read_text(encoding="utf-8"))
    rows = tuple(read_parquet(parquet_path, repo_root=root))
    dataset_hash = sha256_file(parquet_path)
    notes: list[str] = []
    if metadata.dataset_id != EXPECTED_DATASET_ID:
        notes.append(f"dataset_id {metadata.dataset_id!r} != {EXPECTED_DATASET_ID!r}")
    if metadata.dataset_hash != EXPECTED_DATASET_HASH or dataset_hash != EXPECTED_DATASET_HASH:
        notes.append("dataset hash mismatch against frozen Phase 1 value")
    if metadata.configuration_hash != EXPECTED_CONFIGURATION_HASH:
        notes.append("configuration hash mismatch against frozen Phase 1 value")
    if metadata.geometry_version != EXPECTED_GEOMETRY_VERSION:
        notes.append("geometry_version mismatch")
    if metadata.solver_version != EXPECTED_SOLVER_VERSION:
        notes.append("solver_version mismatch")
    if metadata.split_counts != EXPECTED_SPLIT_COUNTS:
        notes.append(f"split counts {metadata.split_counts} != {EXPECTED_SPLIT_COUNTS}")
    if tuple(COLUMN_ORDER) != (
        "sample_id",
        "split",
        *INPUT_NAMES,
        *OUTPUT_NAMES,
    ):
        notes.append("column order drifted from Phase 1 schema")
    quality = validate_dataset_rows(list(rows), resolved_config, metadata.failed_fea_count)
    try:
        require_quality(quality)
    except Exception as exc:
        raise Phase1IntegrityError(f"Phase 1 quality gate failed: {exc}") from exc
    train = tuple(row for row in rows if row.split == "train")
    validation = tuple(row for row in rows if row.split == "validation")
    interpolation_test = tuple(row for row in rows if row.split == "interpolation_test")
    if (
        len(train) != EXPECTED_SPLIT_COUNTS["train"]
        or len(validation) != EXPECTED_SPLIT_COUNTS["validation"]
        or len(interpolation_test) != EXPECTED_SPLIT_COUNTS["interpolation_test"]
    ):
        notes.append("materialized split lengths do not match frozen counts")
    train_ids = {row.sample_id for row in train}
    val_ids = {row.sample_id for row in validation}
    test_ids = {row.sample_id for row in interpolation_test}
    if train_ids & val_ids or train_ids & test_ids or val_ids & test_ids:
        notes.append("split sample_id overlap detected")
    if notes:
        raise Phase1IntegrityError("Phase 1 integrity failed: " + "; ".join(notes))
    return LoadedPhase1Dataset(
        rows=rows,
        metadata=metadata,
        parquet_path=parquet_path,
        dataset_hash=dataset_hash,
        train=train,
        validation=validation,
        interpolation_test=interpolation_test,
    )
