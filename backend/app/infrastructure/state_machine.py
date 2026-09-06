"""Explicit job state machine. Invalid transitions are rejected."""

from __future__ import annotations

from typing import Literal

from app.infrastructure.errors import ConflictError

JobStatus = Literal[
    "queued",
    "running",
    "completed",
    "failed",
    "cancel_requested",
    "cancelled",
]

ALLOWED: dict[JobStatus, frozenset[JobStatus]] = {
    "queued": frozenset({"running", "cancelled"}),
    "running": frozenset({"completed", "failed", "cancel_requested"}),
    "cancel_requested": frozenset({"cancelled", "failed", "completed"}),
    "completed": frozenset(),
    "failed": frozenset(),
    "cancelled": frozenset(),
}


def assert_transition(current: JobStatus, nxt: JobStatus) -> None:
    if nxt not in ALLOWED[current]:
        raise ConflictError(
            "INVALID_JOB_TRANSITION",
            f"Cannot transition job from {current} to {nxt}.",
        )
