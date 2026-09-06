from __future__ import annotations

import pytest

from app.infrastructure.errors import ConflictError
from app.infrastructure.state_machine import assert_transition


def test_allowed_and_rejected_transitions() -> None:
    assert_transition("queued", "running")
    assert_transition("running", "completed")
    assert_transition("running", "cancel_requested")
    assert_transition("cancel_requested", "cancelled")
    with pytest.raises(ConflictError):
        assert_transition("completed", "running")
    with pytest.raises(ConflictError):
        assert_transition("failed", "queued")
