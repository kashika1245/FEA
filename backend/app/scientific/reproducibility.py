"""Deterministic hashing and provenance helpers. No pickle. No untrusted code."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from app.scientific.config import ScientificConfig
from app.scientific.exceptions import DatasetError

HASH_ALGORITHM = "sha256"


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise DatasetError(f"payload is not canonically serializable: {exc}") from exc


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def configuration_hash(config: ScientificConfig, geometry_payload: Mapping[str, Any]) -> str:
    payload = {
        "config": config.model_dump(),
        "geometry": geometry_payload,
    }
    return sha256_bytes(canonical_json_bytes(payload))


def git_commit_or_none(repo_root: Path) -> str | None:
    """Read HEAD from a git directory without invoking a shell."""

    git_dir = repo_root / ".git"
    head_path = git_dir / "HEAD"
    if not head_path.is_file():
        return None
    try:
        text = head_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if text.startswith("ref:"):
        ref = text.split(":", 1)[1].strip()
        if not ref or ".." in ref or ref.startswith("/") or ref.startswith("\\"):
            return None
        ref_path = (git_dir / ref).resolve()
        try:
            ref_path.relative_to(git_dir.resolve())
        except ValueError:
            return None
        if not ref_path.is_file():
            return None
        try:
            return ref_path.read_text(encoding="utf-8").strip()[:40]
        except OSError:
            return None
    if len(text) >= 7:
        return text[:40]
    return None


def repo_root_from_package() -> Path:
    return Path(__file__).resolve().parents[3]
