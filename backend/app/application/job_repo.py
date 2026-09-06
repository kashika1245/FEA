"""Transactional job persistence."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import Any

from app.infrastructure.db import ThreadSafeConnection
from app.infrastructure.errors import ConflictError, NotFoundError
from app.infrastructure.state_machine import JobStatus, assert_transition

JOB_COLUMNS = frozenset(
    {
        "status",
        "started_at",
        "completed_at",
        "stage",
        "completed_units",
        "total_units",
        "message",
        "error_code",
        "error_message",
        "idempotency_key",
        "worker_pid",
    }
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def insert_job(
    connection: ThreadSafeConnection,
    *,
    job_id: str,
    experiment_id: str,
    job_type: str,
    idempotency_key: str | None,
) -> dict[str, Any]:
    if idempotency_key:
        existing = connection.execute(
            "SELECT * FROM jobs WHERE idempotency_key = ?", (idempotency_key,)
        ).fetchone()
        if existing is not None:
            return dict(existing)
    try:
        connection.execute(
            """
            INSERT INTO jobs(
                job_id, experiment_id, job_type, status, created_at, stage, message, idempotency_key
            ) VALUES (?, ?, ?, 'queued', ?, 'queued', 'queued', ?)
            """,
            (job_id, experiment_id, job_type, utc_now(), idempotency_key),
        )
    except sqlite3.IntegrityError as exc:
        raise ConflictError("DUPLICATE_JOB", "Idempotency key already used.") from exc
    return get_job(connection, job_id)


def get_job(connection: ThreadSafeConnection, job_id: str) -> dict[str, Any]:
    row = connection.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    if row is None:
        raise NotFoundError("JOB_NOT_FOUND", "Job does not exist.")
    return dict(row)


def list_jobs(
    connection: ThreadSafeConnection, *, offset: int, limit: int, experiment_id: str | None = None
) -> list[dict[str, Any]]:
    if experiment_id:
        rows = connection.execute(
            """
            SELECT * FROM jobs WHERE experiment_id = ?
            ORDER BY created_at DESC, job_id DESC LIMIT ? OFFSET ?
            """,
            (experiment_id, limit, offset),
        ).fetchall()
    else:
        rows = connection.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC, job_id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [dict(row) for row in rows]


def running_count(connection: ThreadSafeConnection) -> int:
    row = connection.execute(
        "SELECT COUNT(*) AS n FROM jobs WHERE status IN ('running', 'cancel_requested')"
    ).fetchone()
    return int(row["n"])


def active_for_experiment(
    connection: ThreadSafeConnection, experiment_id: str
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT * FROM jobs WHERE experiment_id = ? AND status IN ('queued', 'running', 'cancel_requested')
        ORDER BY created_at DESC LIMIT 1
        """,
        (experiment_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def latest_of_type(
    connection: ThreadSafeConnection, experiment_id: str, job_type: str
) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT * FROM jobs WHERE experiment_id = ? AND job_type = ?
        ORDER BY created_at DESC LIMIT 1
        """,
        (experiment_id, job_type),
    ).fetchone()
    return dict(row) if row is not None else None


def transition(
    connection: ThreadSafeConnection,
    job_id: str,
    nxt: JobStatus,
    **fields: Any,
) -> dict[str, Any]:
    current = get_job(connection, job_id)
    assert_transition(current["status"], nxt)
    assignments = ["status = ?"]
    values: list[Any] = [nxt]
    for key, value in fields.items():
        if key not in JOB_COLUMNS:
            raise ConflictError("INVALID_JOB_FIELD", "Refusing unknown job column update.")
        assignments.append(f"{key} = ?")
        values.append(value)
    values.append(job_id)
    connection.execute(f"UPDATE jobs SET {', '.join(assignments)} WHERE job_id = ?", values)
    return get_job(connection, job_id)


def mark_stale_running(connection: ThreadSafeConnection) -> int:
    rows = connection.execute(
        "SELECT job_id, status FROM jobs WHERE status IN ('running', 'cancel_requested')"
    ).fetchall()
    count = 0
    for row in rows:
        nxt: JobStatus = "cancelled" if row["status"] == "cancel_requested" else "failed"
        connection.execute(
            """
            UPDATE jobs SET status = ?, completed_at = ?, error_code = ?, error_message = ?,
            message = 'worker lost during process restart'
            WHERE job_id = ?
            """,
            (
                nxt,
                utc_now(),
                "STALE_AFTER_RESTART",
                "Job was running when the process restarted.",
                row["job_id"],
            ),
        )
        connection.execute("DELETE FROM experiment_locks WHERE job_id = ?", (row["job_id"],))
        count += 1
    return count


def acquire_lock(connection: ThreadSafeConnection, experiment_id: str, job_id: str) -> None:
    try:
        connection.execute(
            "INSERT INTO experiment_locks(experiment_id, job_id, acquired_at) VALUES (?, ?, ?)",
            (experiment_id, job_id, utc_now()),
        )
    except sqlite3.IntegrityError as exc:
        raise ConflictError(
            "EXPERIMENT_LOCKED", "Another job holds the experiment write lock."
        ) from exc


def release_lock(connection: ThreadSafeConnection, experiment_id: str) -> None:
    connection.execute("DELETE FROM experiment_locks WHERE experiment_id = ?", (experiment_id,))
