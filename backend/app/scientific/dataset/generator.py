"""Resumable FEM dataset generation. Failed solves never become fake rows."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.scientific.canonical import canonical_ten_bar_truss
from app.scientific.config import ScientificConfig
from app.scientific.dataset.checkpoint import CheckpointStore
from app.scientific.dataset.metadata import DatasetMetadata
from app.scientific.dataset.sampling import draw_paper_unit_sample, sample_in_domain, split_rng
from app.scientific.dataset.schema import COLUMN_UNITS, DatasetRow, SplitName
from app.scientific.dataset.storage import confine_under_data_root, read_parquet, write_parquet
from app.scientific.dataset.validation import (
    DatasetQualityReport,
    require_quality,
    validate_dataset_rows,
)
from app.scientific.exceptions import DatasetError, ScientificError
from app.scientific.fem.solver import analyze
from app.scientific.geometry_payload import geometry_hash_payload
from app.scientific.parameters import StructuralParameters
from app.scientific.reproducibility import (
    configuration_hash,
    git_commit_or_none,
    repo_root_from_package,
    sha256_file,
)
from app.scientific.responses import utc_timestamp
from app.scientific.units import INTERNAL_UNITS

LOGGER = logging.getLogger("paper_a.dataset")


@dataclass(frozen=True, slots=True)
class GenerationResult:
    metadata: DatasetMetadata
    quality: DatasetQualityReport
    parquet_path: Path
    metadata_path: Path
    directory: Path


def assign_splits(n_samples: int, seed: int, config: ScientificConfig) -> dict[int, SplitName]:
    n_train, n_validation, n_test = config.dataset.split_counts(n_samples)
    if n_train + n_validation + n_test != n_samples:
        raise DatasetError("split counts do not sum to n_samples")
    shuffled = split_rng(seed).permutation(np.arange(1, n_samples + 1, dtype=np.int64))
    mapping: dict[int, SplitName] = {}
    for index, sample_id in enumerate(shuffled):
        sid = int(sample_id)
        if index < n_train:
            mapping[sid] = "train"
        elif index < n_train + n_validation:
            mapping[sid] = "validation"
        else:
            mapping[sid] = "interpolation_test"
    return mapping


def generate_dataset(
    config: ScientificConfig,
    output_dir: Path | None = None,
    *,
    n_samples: int | None = None,
    resume: bool = True,
    repo_root: Path | None = None,
    dataset_id: str | None = None,
) -> GenerationResult:
    """Generate or resume a FEM dataset. In-domain solve failure aborts the job."""

    started = time.perf_counter()
    n = config.dataset.n_samples if n_samples is None else n_samples
    if n < 1:
        raise DatasetError("n_samples must be positive")
    root = repo_root if repo_root is not None else repo_root_from_package()
    model = canonical_ten_bar_truss(config=config)
    seed = config.dataset.random_seed
    resolved_id = dataset_id or f"{config.dataset_version}-n{n}-seed{seed}"
    directory = output_dir if output_dir is not None else root / "data" / "datasets" / resolved_id
    directory = confine_under_data_root(directory, root)
    directory.mkdir(parents=True, exist_ok=True)
    store = CheckpointStore(directory, resolved_id, repo_root=root)
    if not resume and store.samples_path.exists():
        raise DatasetError(
            f"checkpoint already exists at {store.samples_path}; "
            "refusing to overwrite (resume=True or choose a new dataset_id)"
        )
    splits = assign_splits(n, seed, config)
    existing = store.load_completed_rows() if resume else []
    completed = {row.sample_id: row for row in existing}
    if any(sample_id < 1 or sample_id > n for sample_id in completed):
        raise DatasetError("checkpoint contains sample_id outside the requested range")
    LOGGER.info(
        "dataset generation start",
        extra={
            "dataset_id": resolved_id,
            "stage": "start",
            "completed_count": len(completed),
            "total_count": n,
            "failure_count": 0,
        },
    )
    failure_count = 0
    for sample_id in range(1, n + 1):
        if sample_id in completed:
            continue
        sample = draw_paper_unit_sample(
            sample_id, n, seed, config.parameter_domain, model.n_members
        )
        sample_in_domain(sample, config.parameter_domain)
        parameters = StructuralParameters.from_paper_units(
            {member_id: sample.areas_mm2[member_id - 1] for member_id in model.member_ids},
            sample.e_gpa,
            sample.f_kn,
        )
        try:
            result = analyze(model, parameters, config)
        except ScientificError as exc:
            failure_count += 1
            store.append_failure(
                {
                    "sample_id": sample_id,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                    "stage": "fea",
                }
            )
            store.write_status(n, seed, set(completed), "failed")
            LOGGER.error(
                "in-domain FEA failure",
                extra={
                    "dataset_id": resolved_id,
                    "stage": "fea_failure",
                    "completed_count": len(completed),
                    "total_count": n,
                    "failure_count": failure_count,
                    "sample_id": sample_id,
                },
            )
            raise DatasetError(
                f"in-domain FEA failed for sample_id={sample_id}: {type(exc).__name__}: {exc}"
            ) from exc
        row = DatasetRow(
            sample_id=sample_id,
            split=splits[sample_id],
            A1=sample.areas_mm2[0],
            A2=sample.areas_mm2[1],
            A3=sample.areas_mm2[2],
            A4=sample.areas_mm2[3],
            A5=sample.areas_mm2[4],
            A6=sample.areas_mm2[5],
            A7=sample.areas_mm2[6],
            A8=sample.areas_mm2[7],
            A9=sample.areas_mm2[8],
            A10=sample.areas_mm2[9],
            E=sample.e_gpa,
            F=sample.f_kn,
            u_max=result.u_max_mm,
            sigma_max=result.sigma_max_n_per_mm2,
            C=result.compliance_nmm,
        )
        store.append_row(row)
        completed[sample_id] = row
        store.write_status(n, seed, set(completed), "in_progress")
        if sample_id % 50 == 0 or sample_id == n:
            LOGGER.info(
                "dataset generation progress",
                extra={
                    "dataset_id": resolved_id,
                    "stage": "progress",
                    "completed_count": len(completed),
                    "total_count": n,
                    "elapsed_s": time.perf_counter() - started,
                    "failure_count": failure_count,
                },
            )
    ordered = [completed[sample_id] for sample_id in range(1, n + 1)]
    parquet_path = directory / "dataset.parquet"
    write_parquet(ordered, parquet_path, repo_root=root)
    dataset_hash = sha256_file(parquet_path)
    config_hash = configuration_hash(config, geometry_hash_payload(model))
    quality = validate_dataset_rows(
        ordered,
        config.model_copy(update={"dataset": config.dataset.model_copy(update={"n_samples": n})}),
        failed_fea_count=failure_count,
    )
    require_quality(quality)
    n_train, n_val, n_test = config.dataset.split_counts(n)
    metadata = DatasetMetadata(
        dataset_id=resolved_id,
        dataset_version=config.dataset_version,
        sample_count=len(ordered),
        requested_sample_count=n,
        random_seed=seed,
        geometry_version=config.geometry_version,
        solver_version=config.solver_version,
        software_version=config.software_version,
        git_commit=git_commit_or_none(root),
        unit_system={
            "length": INTERNAL_UNITS.length,
            "force": INTERNAL_UNITS.force,
            "area": INTERNAL_UNITS.area,
            "youngs_modulus_internal": INTERNAL_UNITS.youngs_modulus,
            "youngs_modulus_paper": INTERNAL_UNITS.paper_youngs_modulus,
            "load_paper": INTERNAL_UNITS.paper_load,
            "stress": INTERNAL_UNITS.stress,
            "displacement": INTERNAL_UNITS.displacement,
            "compliance": INTERNAL_UNITS.compliance,
            "columns": str(COLUMN_UNITS),
        },
        parameter_domains=config.parameter_domain.model_dump(),
        output_definitions={
            "u_max": "maximum nodal displacement magnitude (mm)",
            "sigma_max": "maximum absolute member stress (N/mm^2)",
            "C": "structural compliance F_global·u (N*mm)",
        },
        generation_timestamp_utc=utc_timestamp(),
        configuration_hash=config_hash,
        dataset_hash=dataset_hash,
        parquet_path=str(parquet_path),
        split_counts={
            "train": n_train,
            "validation": n_val,
            "interpolation_test": n_test,
        },
        failed_fea_count=failure_count,
        status="completed",
    )
    metadata_path = directory / "metadata.json"
    metadata_path.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")
    store.write_status(n, seed, set(completed), "completed")
    LOGGER.info(
        "dataset generation completed",
        extra={
            "dataset_id": resolved_id,
            "stage": "completed",
            "completed_count": len(ordered),
            "total_count": n,
            "elapsed_s": time.perf_counter() - started,
            "failure_count": failure_count,
            "dataset_hash": dataset_hash,
        },
    )
    # Touch read_parquet to confirm round-trip of the artefact just written.
    round_trip = read_parquet(parquet_path, repo_root=root)
    if len(round_trip) != len(ordered):
        raise DatasetError("parquet round-trip row count mismatch")
    return GenerationResult(
        metadata=metadata,
        quality=quality,
        parquet_path=parquet_path,
        metadata_path=metadata_path,
        directory=directory,
    )
