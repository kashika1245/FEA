"""SQLite application state. Does not store scientific Parquet rows."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    stage TEXT,
    completed_units INTEGER,
    total_units INTEGER,
    message TEXT,
    error_code TEXT,
    error_message TEXT,
    idempotency_key TEXT UNIQUE,
    worker_pid INTEGER
);

CREATE INDEX IF NOT EXISTS idx_jobs_experiment ON jobs(experiment_id, created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);

CREATE TABLE IF NOT EXISTS experiment_locks (
    experiment_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    acquired_at TEXT NOT NULL
);
"""


class ThreadSafeConnection:
    """Serialize SQLite use across the API thread and the job worker."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._lock = threading.RLock()

    def execute(self, sql: str, parameters: tuple[Any, ...] | list[Any] = ()) -> sqlite3.Cursor:
        with self._lock:
            return self._connection.execute(sql, parameters)

    def executescript(self, script: str) -> sqlite3.Cursor:
        with self._lock:
            return self._connection.executescript(script)

    def commit(self) -> None:
        with self._lock:
            self._connection.commit()

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def transaction(self) -> _Transaction:
        return _Transaction(self)


class _Transaction:
    def __init__(self, connection: ThreadSafeConnection) -> None:
        self._connection = connection

    def __enter__(self) -> ThreadSafeConnection:
        self._connection._lock.acquire()
        self._connection._connection.execute("BEGIN IMMEDIATE")
        return self._connection

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: object
    ) -> None:
        try:
            if exc_type is None:
                self._connection._connection.execute("COMMIT")
            else:
                self._connection._connection.execute("ROLLBACK")
        finally:
            self._connection._lock.release()


def connect(db_path: Path) -> ThreadSafeConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path), check_same_thread=False, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    return ThreadSafeConnection(connection)


def initialize(connection: ThreadSafeConnection) -> None:
    connection.executescript(SCHEMA)
    row = connection.execute("SELECT version FROM schema_version").fetchone()
    if row is None:
        connection.execute("INSERT INTO schema_version(version) VALUES (?)", (SCHEMA_VERSION,))
        return
    if int(row["version"]) != SCHEMA_VERSION:
        raise RuntimeError(f"unsupported application schema version {row['version']}")
