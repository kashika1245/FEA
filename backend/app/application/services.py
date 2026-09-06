"""Application services used by the API."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.compute as pc
import pyarrow.parquet as pq

from app.application.executor import JobExecutor
from app.application.experiment_catalog import (
    inventory_artifacts,
    is_immutable,
    list_experiment_ids,
    read_manifest,
    require_experiment,
    row_count,
)
from app.application.job_repo import (
    active_for_experiment,
    get_job,
    insert_job,
    latest_of_type,
    list_jobs,
    running_count,
    transition,
    utc_now,
)
from app.application.job_types import JobType
from app.infrastructure.db import ThreadSafeConnection
from app.infrastructure.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ValidationAppError,
)
from app.infrastructure.ids import (
    decode_artifact_id,
    new_job_id,
    validate_experiment_id,
    validate_job_id,
)
from app.infrastructure.paths import experiment_dir, resolve_artifact
from app.infrastructure.settings import AppSettings
from app.scientific.surrogate.config import OUTPUT_NAMES
from app.scientific.surrogate.dataset import EXPECTED_DATASET_HASH


class RateLimiter:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self._count = 0

    def hit(self) -> None:
        self._count += 1
        if self._count > self.limit:
            raise RateLimitError()


class AppServices:
    def __init__(
        self,
        settings: AppSettings,
        connection: ThreadSafeConnection,
        executor: JobExecutor,
    ) -> None:
        self.settings = settings
        self.connection = connection
        self.executor = executor
        self.limiter = RateLimiter(settings.mutate_rate_limit)

    def health(self) -> dict[str, str]:
        return {"status": "ok"}

    def ready(self) -> dict[str, object]:
        dataset = (
            self.settings.repo_root
            / "data"
            / "datasets"
            / "paper-a.phase1.v1-n10000-seed20260905"
            / "dataset.parquet"
        )
        checks = {
            "data_root": (self.settings.repo_root / "data").is_dir(),
            "sqlite": True,
            "phase1_dataset": dataset.is_file(),
        }
        ready = all(checks.values())
        return {"ready": ready, "checks": checks}

    def list_experiments(self, offset: int, limit: int) -> list[dict[str, Any]]:
        ids = list_experiment_ids(self.settings.repo_root)
        page = ids[offset : offset + limit]
        return [self.experiment_summary(item) for item in page]

    def experiment_summary(self, experiment_id: str) -> dict[str, Any]:
        validate_experiment_id(experiment_id)
        directory = require_experiment(experiment_id, self.settings.repo_root)
        manifest = read_manifest(experiment_id, self.settings.repo_root)
        artifacts = inventory_artifacts(experiment_id, self.settings.repo_root)
        observations = directory / "extrapolation" / "observations.parquet"
        combined = directory / "combined" / "observations.parquet"
        profiles = directory / "profiles" / "profiles.parquet"
        return {
            "experiment_id": experiment_id,
            "status": None if manifest is None else manifest.get("status"),
            "immutable": is_immutable(experiment_id),
            "dataset_hash": None if manifest is None else manifest.get("dataset_hash"),
            "normalization_hash": None if manifest is None else manifest.get("normalization_hash"),
            "configuration_hash": None if manifest is None else manifest.get("configuration_hash"),
            "artifact_count": len(artifacts),
            "variable_wise_rows": row_count(observations),
            "combined_rows": row_count(combined),
            "profile_rows": row_count(profiles),
        }

    def experiment_detail(self, experiment_id: str) -> dict[str, Any]:
        summary = self.experiment_summary(experiment_id)
        manifest = read_manifest(experiment_id, self.settings.repo_root)
        artifacts = inventory_artifacts(experiment_id, self.settings.repo_root)
        ranking_path = (
            experiment_dir(experiment_id, self.settings.repo_root)
            / "models"
            / "validation_ranking.json"
        )
        ranking = None
        if ranking_path.is_file():
            ranking = json.loads(ranking_path.read_text(encoding="utf-8"))
        return {
            **summary,
            "manifest": manifest,
            "artifacts": artifacts,
            "validation_ranking": ranking,
            "frozen_dataset_hash": EXPECTED_DATASET_HASH,
        }

    def create_experiment(self, experiment_id: str) -> dict[str, Any]:
        self.limiter.hit()
        validate_experiment_id(experiment_id)
        if not experiment_id.startswith("paper-a.phase3."):
            raise ValidationAppError(
                "INVALID_EXPERIMENT_ID",
                "New experiments must use the paper-a.phase3.* prefix.",
            )
        if is_immutable(experiment_id):
            raise ForbiddenError(
                "EXPERIMENT_IMMUTABLE", "Frozen Phase 2 experiments cannot be created."
            )
        directory = experiment_dir(experiment_id, self.settings.repo_root)
        directory.mkdir(parents=True, exist_ok=True)
        return self.experiment_summary(experiment_id)

    def run_experiment(
        self,
        experiment_id: str,
        job_type: JobType,
        idempotency_key: str | None,
    ) -> dict[str, Any]:
        self.limiter.hit()
        validate_experiment_id(experiment_id)
        if is_immutable(experiment_id):
            raise ForbiddenError(
                "EXPERIMENT_IMMUTABLE",
                "Frozen Phase 2 artefacts cannot be overwritten by a job.",
            )
        require_experiment(experiment_id, self.settings.repo_root)
        if idempotency_key:
            existing = self.connection.execute(
                "SELECT * FROM jobs WHERE idempotency_key = ?", (idempotency_key,)
            ).fetchone()
            if existing is not None:
                return dict(existing)
        active = active_for_experiment(self.connection, experiment_id)
        if active is not None:
            raise ConflictError(
                "JOB_ALREADY_RUNNING", "An active job already owns this experiment."
            )
        if running_count(self.connection) >= self.settings.max_running_jobs:
            raise ConflictError("GLOBAL_JOB_LIMIT", "A scientific job is already running.")
        latest = latest_of_type(self.connection, experiment_id, job_type)
        if latest is not None and latest["status"] == "completed":
            return latest
        job_id = new_job_id()
        return insert_job(
            self.connection,
            job_id=job_id,
            experiment_id=experiment_id,
            job_type=job_type,
            idempotency_key=idempotency_key,
        )

    def get_job(self, job_id: str) -> dict[str, Any]:
        return get_job(self.connection, validate_job_id(job_id))

    def list_jobs(self, offset: int, limit: int, experiment_id: str | None) -> list[dict[str, Any]]:
        if experiment_id is not None:
            validate_experiment_id(experiment_id)
        return list_jobs(self.connection, offset=offset, limit=limit, experiment_id=experiment_id)

    def cancel_active_experiment(self, experiment_id: str) -> dict[str, Any]:
        validate_experiment_id(experiment_id)
        active = active_for_experiment(self.connection, experiment_id)
        if active is None:
            raise NotFoundError("JOB_NOT_FOUND", "No active job exists for this experiment.")
        return self.cancel_job(str(active["job_id"]))

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        self.limiter.hit()
        job = get_job(self.connection, validate_job_id(job_id))
        if job["status"] == "queued":
            return transition(
                self.connection,
                job_id,
                "cancelled",
                completed_at=utc_now(),
                stage="cancelled",
                message="cancelled before start",
            )
        if job["status"] == "running":
            updated = transition(
                self.connection, job_id, "cancel_requested", message="cancel requested"
            )
            self.executor.request_cancel(job_id)
            return updated
        if job["status"] == "cancel_requested":
            return job
        raise ConflictError(
            "INVALID_JOB_TRANSITION", "Job is not cancellable in its current state."
        )

    def list_artifacts(self, experiment_id: str, offset: int, limit: int) -> list[dict[str, Any]]:
        items = inventory_artifacts(validate_experiment_id(experiment_id), self.settings.repo_root)
        return items[offset : offset + limit]

    def artifact_detail(self, artifact_id: str) -> dict[str, Any]:
        experiment_id, relative = decode_artifact_id(artifact_id)
        items = inventory_artifacts(experiment_id, self.settings.repo_root)
        for item in items:
            if item["artifact_id"] == artifact_id:
                return item
        resolve_artifact(experiment_id, relative, self.settings.repo_root)
        raise NotFoundError("ARTIFACT_NOT_FOUND", "Artifact does not exist.")

    def artifact_file(self, artifact_id: str) -> Path:
        experiment_id, relative = decode_artifact_id(artifact_id)
        return resolve_artifact(experiment_id, relative, self.settings.repo_root)

    def research_summary(self, experiment_id: str) -> dict[str, Any]:
        return self.experiment_detail(experiment_id)

    def read_json_dir(
        self, experiment_id: str, relative_dir: str, pattern: str
    ) -> list[dict[str, Any]]:
        directory = require_experiment(experiment_id, self.settings.repo_root) / relative_dir
        if not directory.is_dir():
            raise NotFoundError("ARTIFACT_NOT_FOUND", "Research artefact directory does not exist.")
        rows = []
        for path in sorted(directory.glob(pattern)):
            if path.suffix == ".json":
                rows.append(json.loads(path.read_text(encoding="utf-8")))
        return rows

    def read_parquet_page(
        self,
        experiment_id: str,
        relative_path: str,
        offset: int,
        limit: int,
        filters: dict[str, Any],
        columns: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        path = resolve_artifact(experiment_id, relative_path, self.settings.repo_root)
        table = pq.read_table(path, columns=columns)
        for name, value in filters.items():
            if value is None or name not in table.column_names:
                continue
            table = table.filter(pc.equal(table[name], value))
        sliced = table.slice(offset, limit)
        return list(sliced.to_pylist())

    def combined_grid(
        self,
        experiment_id: str,
        *,
        response: str,
        direction_a3: str,
        direction_f: str,
        seed: int,
    ) -> dict[str, Any]:
        if response not in OUTPUT_NAMES:
            raise ValidationAppError("INVALID_RESPONSE", "Response is not a known output name.")
        if direction_a3 not in {"lower", "upper"} or direction_f not in {"lower", "upper"}:
            raise ValidationAppError("INVALID_DIRECTION", "Direction must be lower or upper.")
        column = f"relative_{response}_error"
        path = resolve_artifact(experiment_id, "combined/observations.parquet", self.settings.repo_root)
        table = pq.read_table(
            path,
            columns=["direction_a3", "direction_f", "delta_a3", "delta_f", "seed", column],
        )
        table = table.filter(pc.equal(table["direction_a3"], direction_a3))
        table = table.filter(pc.equal(table["direction_f"], direction_f))
        table = table.filter(pc.equal(table["seed"], seed))
        buckets: dict[tuple[float, float], list[float]] = {}
        for row in table.to_pylist():
            key = (float(row["delta_a3"]), float(row["delta_f"]))
            buckets.setdefault(key, []).append(float(row[column]))
        cells = []
        for (delta_a3, delta_f), values in sorted(buckets.items()):
            array = np.asarray(values, dtype=np.float64)
            cells.append(
                {
                    "delta_a3": delta_a3,
                    "delta_f": delta_f,
                    "median_relative_error_pct": float(np.median(array)),
                    "n": int(array.size),
                }
            )
        return {
            "experiment_id": experiment_id,
            "response": response,
            "direction_a3": direction_a3,
            "direction_f": direction_f,
            "seed": seed,
            "cells": cells,
        }
