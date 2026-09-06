"""Strict identifier validation. Rejects traversal, injection, and log-breakers."""

from __future__ import annotations

import base64
import re
import uuid

from app.infrastructure.errors import ValidationAppError

EXPERIMENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
JOB_ID_RE = re.compile(r"^[a-f0-9]{32}$")
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
SAFE_RELATIVE_RE = re.compile(r"^[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*$")


def validate_experiment_id(value: str) -> str:
    if not EXPERIMENT_ID_RE.fullmatch(value):
        raise ValidationAppError("INVALID_EXPERIMENT_ID", "Experiment ID is not an allowed token.")
    if ".." in value or "/" in value or "\\" in value:
        raise ValidationAppError(
            "INVALID_EXPERIMENT_ID", "Experiment ID must not contain path separators."
        )
    return value


def validate_job_id(value: str) -> str:
    if not JOB_ID_RE.fullmatch(value):
        raise ValidationAppError("INVALID_JOB_ID", "Job ID must be a 32-character hex token.")
    return value


def new_job_id() -> str:
    return uuid.uuid4().hex


def validate_request_id(value: str | None) -> str:
    if value is None or not value.strip():
        return uuid.uuid4().hex
    candidate = value.strip()
    if not REQUEST_ID_RE.fullmatch(candidate):
        return uuid.uuid4().hex
    if "\n" in candidate or "\r" in candidate:
        return uuid.uuid4().hex
    return candidate


def validate_relative_artifact_path(value: str) -> str:
    if not value or value.startswith("/") or value.startswith("\\") or ":" in value:
        raise ValidationAppError(
            "INVALID_ARTIFACT_PATH", "Artifact path is not a confined relative path."
        )
    normalized = value.replace("\\", "/")
    if not normalized or normalized.startswith("/") or ".." in normalized.split("/"):
        raise ValidationAppError(
            "INVALID_ARTIFACT_PATH", "Artifact path is not a confined relative path."
        )
    if not SAFE_RELATIVE_RE.fullmatch(normalized):
        raise ValidationAppError(
            "INVALID_ARTIFACT_PATH", "Artifact path contains disallowed characters."
        )
    return normalized


def encode_artifact_id(experiment_id: str, relative_path: str) -> str:
    payload = (
        f"{validate_experiment_id(experiment_id)}:{validate_relative_artifact_path(relative_path)}"
    )
    return base64.urlsafe_b64encode(payload.encode("ascii")).decode("ascii").rstrip("=")


def decode_artifact_id(artifact_id: str) -> tuple[str, str]:
    padded = artifact_id + "=" * (-len(artifact_id) % 4)
    try:
        raw = base64.urlsafe_b64decode(padded.encode("ascii")).decode("ascii")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValidationAppError(
            "INVALID_ARTIFACT_ID", "Artifact ID is not a valid token."
        ) from exc
    if raw.count(":") != 1:
        raise ValidationAppError("INVALID_ARTIFACT_ID", "Artifact ID payload is malformed.")
    experiment_id, relative = raw.split(":", 1)
    return validate_experiment_id(experiment_id), validate_relative_artifact_path(relative)
