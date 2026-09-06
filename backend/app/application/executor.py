"""Background worker. Long scientific work never runs on the API event loop."""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Any

from app.application.job_repo import (
    acquire_lock,
    get_job,
    release_lock,
    running_count,
    transition,
    utc_now,
)
from app.infrastructure.db import ThreadSafeConnection
from app.infrastructure.errors import ApplicationError, ConflictError
from app.infrastructure.logging import get_app_logger, log_app
from app.infrastructure.settings import AppSettings
from app.scientific.config import load_default_scientific_config
from app.scientific.experiments.runner import Phase2Runner
from app.scientific.phase2_errors import Phase2Error
from app.scientific.reporting.plots import (
    write_combined_heatmaps,
    write_interpolation_plots,
    write_profile_plots,
)
from app.scientific.reporting.tables import (
    write_asymmetry_table,
    write_combined_table,
    write_interpolation_table,
    write_profile_table,
    write_seed_variability_table,
    write_threshold_markdown,
)
from app.scientific.surrogate.config import load_default_phase2_config

LOGGER = get_app_logger()


class JobExecutor:
    def __init__(self, settings: AppSettings, connection: ThreadSafeConnection) -> None:
        self.settings = settings
        self.connection = connection
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, name="phase3-worker", daemon=True)
        self._cancel = set[str]()

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2.0)

    def request_cancel(self, job_id: str) -> None:
        self._cancel.add(job_id)

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._claim_one()
            except Exception as exc:
                log_app(LOGGER, "worker_loop_error", exception_type=type(exc).__name__)
            time.sleep(0.1)

    def _claim_one(self) -> None:
        if running_count(self.connection) >= self.settings.max_running_jobs:
            return
        row = self.connection.execute(
            "SELECT job_id FROM jobs WHERE status = 'queued' ORDER BY created_at ASC LIMIT 1"
        ).fetchone()
        if row is None:
            return
        job_id = str(row["job_id"])
        job = get_job(self.connection, job_id)
        try:
            with self.connection.transaction():
                acquire_lock(self.connection, job["experiment_id"], job_id)
                transition(
                    self.connection,
                    job_id,
                    "running",
                    started_at=utc_now(),
                    worker_pid=os.getpid(),
                    stage="start",
                    message="running",
                )
        except ConflictError:
            return
        except ApplicationError:
            release_lock(self.connection, job["experiment_id"])
            return
        try:
            self._execute(job_id)
        finally:
            release_lock(self.connection, job["experiment_id"])

    def _cancelled(self, job_id: str) -> bool:
        if job_id in self._cancel:
            return True
        job = get_job(self.connection, job_id)
        return str(job["status"]) == "cancel_requested"

    def _stage(self, job_id: str, stage: str, completed: int, total: int) -> None:
        if self._cancelled(job_id):
            current = get_job(self.connection, job_id)
            if current["status"] == "running":
                transition(
                    self.connection,
                    job_id,
                    "cancel_requested",
                    stage=stage,
                    message="cancel requested",
                )
            raise Cancelled()
        self.connection.execute(
            """
            UPDATE jobs SET stage = ?, completed_units = ?, total_units = ?, message = ?
            WHERE job_id = ?
            """,
            (stage, completed, total, stage, job_id),
        )

    def _execute(self, job_id: str) -> None:
        job = get_job(self.connection, job_id)
        started = time.perf_counter()
        log_app(
            LOGGER,
            "job_start",
            job_id=job_id,
            experiment_id=job["experiment_id"],
            job_type=job["job_type"],
        )
        try:
            runner = _build_runner(self.settings.repo_root, job["experiment_id"])
            _run_job_type(self, job_id, job["job_type"], runner)
            if self._cancelled(job_id):
                raise Cancelled()
            transition(
                self.connection,
                job_id,
                "completed",
                completed_at=utc_now(),
                stage="completed",
                message="completed",
                completed_units=1,
                total_units=1,
            )
            log_app(
                LOGGER,
                "job_complete",
                job_id=job_id,
                experiment_id=job["experiment_id"],
                duration_s=time.perf_counter() - started,
                status="completed",
            )
        except Cancelled:
            transition(
                self.connection,
                job_id,
                "cancelled",
                completed_at=utc_now(),
                stage="cancelled",
                message="cancelled",
            )
            self._cancel.discard(job_id)
            log_app(LOGGER, "job_cancelled", job_id=job_id, experiment_id=job["experiment_id"])
        except Phase2Error as exc:
            transition(
                self.connection,
                job_id,
                "failed",
                completed_at=utc_now(),
                stage="failed",
                error_code=type(exc).__name__,
                error_message=str(exc),
                message="scientific failure",
            )
            log_app(
                LOGGER,
                "job_failed",
                job_id=job_id,
                exception_type=type(exc).__name__,
                status="failed",
            )
        except Exception as exc:
            transition(
                self.connection,
                job_id,
                "failed",
                completed_at=utc_now(),
                stage="failed",
                error_code="JOB_EXECUTION_FAILED",
                error_message=str(exc),
                message="execution failure",
            )
            log_app(
                LOGGER,
                "job_failed",
                job_id=job_id,
                exception_type=type(exc).__name__,
                status="failed",
            )


class Cancelled(Exception):
    """Cooperative cancellation between runner stages."""


def _build_runner(repo_root: Path, experiment_id: str) -> Phase2Runner:
    phase1 = load_default_scientific_config()
    phase2 = load_default_phase2_config()
    profile = _profile_for(experiment_id)
    return Phase2Runner(
        phase1,
        phase2,
        experiment_id=experiment_id,
        n_anchors=profile["n_anchors"],
        seeds=profile["seeds"],
        variables=profile["variables"],
        deltas=profile["deltas"],
        repo_root=repo_root,
    )


def _profile_for(experiment_id: str) -> dict[str, Any]:
    if experiment_id.endswith("pilot-tiny") or ".tiny" in experiment_id:
        return {
            "n_anchors": 2,
            "seeds": (20260905,),
            "variables": ("A3",),
            "deltas": (0.0, 0.25, 0.50),
            "skip_combined": True,
        }
    if experiment_id.endswith("pilot-10a"):
        return {
            "n_anchors": 10,
            "seeds": (20260905,),
            "variables": None,
            "deltas": None,
            "skip_combined": True,
        }
    return {
        "n_anchors": None,
        "seeds": None,
        "variables": None,
        "deltas": None,
        "skip_combined": False,
    }


def _run_job_type(executor: JobExecutor, job_id: str, job_type: str, runner: Phase2Runner) -> None:
    skip_combined = bool(_profile_for(runner.experiment_id).get("skip_combined"))
    stages: list[tuple[str, Any]]
    if job_type == "TRAIN_SURROGATE":
        stages = [
            ("phase1", runner.validate_phase1),
            ("normalization", runner.fit_normalization),
            ("train", runner.train_seeds),
        ]
    elif job_type == "INTERPOLATION_EVALUATION":
        stages = [
            ("phase1", runner.validate_phase1),
            ("normalization", runner.fit_normalization),
            ("train", runner.train_seeds),
            ("interpolation", runner.evaluate_interpolation),
        ]
    elif job_type == "EXTRAPOLATION":
        stages = [
            ("phase1", runner.validate_phase1),
            ("normalization", runner.fit_normalization),
            ("train", runner.train_seeds),
            ("interpolation", runner.evaluate_interpolation),
            ("anchors", runner.select_anchors),
            ("extrapolation", runner.run_variable_wise),
        ]
    elif job_type == "COMBINED_EXTRAPOLATION":
        stages = [
            ("phase1", runner.validate_phase1),
            ("normalization", runner.fit_normalization),
            ("train", runner.train_seeds),
            ("anchors", runner.select_anchors),
            ("combined", runner.run_combined),
        ]
    elif job_type == "PROFILE_BUILD":
        stages = [
            ("phase1", runner.validate_phase1),
            ("normalization", runner.fit_normalization),
            ("train", runner.train_seeds),
            ("profiles", runner.build_profiles),
        ]
    elif job_type == "REPORT_BUILD":
        stages = [
            ("phase1", runner.validate_phase1),
            ("reports", lambda: _write_reports(runner)),
        ]
    elif job_type == "FULL_PHASE2_PIPELINE":
        stages = [
            ("phase1", runner.validate_phase1),
            ("normalization", runner.fit_normalization),
            ("train", runner.train_seeds),
            ("interpolation", runner.evaluate_interpolation),
            ("anchors", runner.select_anchors),
            ("extrapolation", runner.run_variable_wise),
            ("profiles", runner.build_profiles),
        ]
        if not skip_combined:
            stages.append(("combined", runner.run_combined))
        stages.append(("reports", lambda: _write_reports(runner)))
    else:
        raise ApplicationError("UNKNOWN_JOB_TYPE", f"Unsupported job type {job_type}.", 400)
    total = len(stages)
    for index, (name, fn) in enumerate(stages, start=1):
        executor._stage(job_id, name, index - 1, total)
        fn()
        runner.write_manifest(name)
    executor._stage(job_id, "completed", total, total)


def _write_reports(runner: Phase2Runner) -> None:
    paths = runner.paths
    if (paths.interpolation / "seed-20260905.json").is_file() or any(
        paths.interpolation.glob("seed-*.json")
    ):
        write_interpolation_table(paths)
        write_interpolation_plots(paths)
    if (paths.profiles / "profiles.parquet").is_file():
        write_profile_table(paths)
        write_threshold_markdown(paths)
        write_asymmetry_table(paths)
        write_seed_variability_table(paths)
        write_profile_plots(paths)
    if (paths.combined / "observations.parquet").is_file():
        write_combined_table(paths)
        write_combined_heatmaps(paths)
