from __future__ import annotations

from pathlib import Path

import pytest

from app.application.job_repo import (
    acquire_lock,
    get_job,
    insert_job,
    mark_stale_running,
    release_lock,
    transition,
)
from app.infrastructure.db import connect, initialize
from app.infrastructure.errors import ConflictError


def test_job_insert_transition_and_lock(tmp_path: Path) -> None:
    connection = connect(tmp_path / "app.sqlite")
    initialize(connection)
    job = insert_job(
        connection,
        job_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        experiment_id="paper-a.phase3.tiny-a",
        job_type="TRAIN_SURROGATE",
        idempotency_key="k1",
    )
    assert job["status"] == "queued"
    acquire_lock(connection, "paper-a.phase3.tiny-a", job["job_id"])
    with pytest.raises(ConflictError):
        acquire_lock(connection, "paper-a.phase3.tiny-a", "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
    running = transition(connection, job["job_id"], "running", stage="train")
    assert running["status"] == "running"
    with pytest.raises(ConflictError):
        transition(connection, job["job_id"], "queued")
    release_lock(connection, "paper-a.phase3.tiny-a")
    connection.close()


def test_stale_running_recovery(tmp_path: Path) -> None:
    connection = connect(tmp_path / "app.sqlite")
    initialize(connection)
    insert_job(
        connection,
        job_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        experiment_id="paper-a.phase3.tiny-a",
        job_type="TRAIN_SURROGATE",
        idempotency_key=None,
    )
    transition(connection, "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "running")
    assert mark_stale_running(connection) == 1
    assert get_job(connection, "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")["status"] == "failed"
    connection.close()
