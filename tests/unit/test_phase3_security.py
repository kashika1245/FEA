from __future__ import annotations

import base64
from pathlib import Path

import pytest

from app.infrastructure.errors import ForbiddenError, NotFoundError, ValidationAppError
from app.infrastructure.ids import (
    decode_artifact_id,
    encode_artifact_id,
    validate_relative_artifact_path,
)
from app.infrastructure.paths import resolve_artifact
from app.infrastructure.settings import cors_origins_from_env


@pytest.mark.parametrize(
    "value",
    [
        "../../etc/passwd",
        "..\\..\\",
        "%2e%2e/",
        "/etc/passwd",
        "foo/../../secret",
        "abs/../../../etc/passwd",
    ],
)
def test_relative_path_rejects_traversal_shapes(value: str) -> None:
    with pytest.raises(ValidationAppError):
        validate_relative_artifact_path(value)


def test_encoded_artifact_id_cannot_carry_traversal() -> None:
    raw = (
        base64.urlsafe_b64encode(b"paper-a.phase2.v1:../../etc/passwd").decode("ascii").rstrip("=")
    )
    with pytest.raises(ValidationAppError):
        decode_artifact_id(raw)


def test_symlink_and_absolute_rejected(tmp_path: Path) -> None:
    experiment = tmp_path / "data" / "experiments" / "paper-a.phase3.sec"
    experiment.mkdir(parents=True)
    (experiment / "ok.json").write_text("{}", encoding="utf-8")
    target = tmp_path / "outside.txt"
    target.write_text("secret", encoding="utf-8")
    (experiment / "escape.json").symlink_to(target)
    resolved = resolve_artifact("paper-a.phase3.sec", "ok.json", tmp_path)
    assert resolved.name == "ok.json"
    with pytest.raises((ForbiddenError, NotFoundError)):
        resolve_artifact("paper-a.phase3.sec", "escape.json", tmp_path)
    with pytest.raises(ValidationAppError):
        resolve_artifact("paper-a.phase3.sec", "/etc/passwd", tmp_path)


def test_cors_allow_list_drops_wildcard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PAPER_A_CORS_ORIGINS", "*,http://127.0.0.1:5173, ")
    origins = cors_origins_from_env()
    assert "*" not in origins
    assert origins == ("http://127.0.0.1:5173",)


def test_artifact_id_round_trip_is_opaque() -> None:
    token = encode_artifact_id("paper-a.phase2.v1", "reports/thresholds.md")
    assert ".." not in token
    assert "/" not in token
    assert decode_artifact_id(token) == ("paper-a.phase2.v1", "reports/thresholds.md")
