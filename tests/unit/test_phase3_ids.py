from __future__ import annotations

import pytest

from app.infrastructure.errors import ValidationAppError
from app.infrastructure.ids import (
    decode_artifact_id,
    encode_artifact_id,
    validate_experiment_id,
    validate_job_id,
    validate_relative_artifact_path,
    validate_request_id,
)


def test_experiment_id_rejects_traversal() -> None:
    with pytest.raises(ValidationAppError):
        validate_experiment_id("../etc")
    with pytest.raises(ValidationAppError):
        validate_experiment_id("a/b")


def test_artifact_round_trip() -> None:
    token = encode_artifact_id("paper-a.phase2.v1", "manifest.json")
    assert "/" not in token
    assert decode_artifact_id(token) == ("paper-a.phase2.v1", "manifest.json")


def test_relative_path_rejects_dotdot() -> None:
    with pytest.raises(ValidationAppError):
        validate_relative_artifact_path("../../etc/passwd")
    with pytest.raises(ValidationAppError):
        validate_relative_artifact_path("/absolute")


def test_job_id_and_request_id() -> None:
    with pytest.raises(ValidationAppError):
        validate_job_id("not-hex")
    assert validate_request_id("abc-123") == "abc-123"
    assert "\n" not in validate_request_id("bad\nid")
