"""Filesystem experiment discovery. Stored manifests are authoritative."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.infrastructure.errors import NotFoundError, ValidationAppError
from app.infrastructure.ids import encode_artifact_id, validate_experiment_id
from app.infrastructure.paths import experiment_dir, experiments_root
from app.scientific.reproducibility import sha256_file

ARTIFACT_SUFFIXES = {".parquet", ".json", ".md", ".pdf", ".png", ".npz"}


def list_experiment_ids(repo_root: Path) -> list[str]:
    root = experiments_root(repo_root)
    if not root.is_dir():
        return []
    ids = [
        path.name
        for path in sorted(root.iterdir())
        if path.is_dir() and not path.name.startswith(".")
    ]
    return [item for item in ids if _looks_like_id(item)]


def _looks_like_id(value: str) -> bool:
    try:
        validate_experiment_id(value)
    except Exception:
        return False
    return True


def read_manifest(experiment_id: str, repo_root: Path) -> dict[str, Any] | None:
    path = experiment_dir(experiment_id, repo_root) / "manifest.json"
    if not path.is_file():
        return None
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValidationAppError("INVALID_MANIFEST", "Manifest is not a JSON object.")
    return loaded


def require_experiment(experiment_id: str, repo_root: Path) -> Path:
    directory = experiment_dir(experiment_id, repo_root)
    if not directory.is_dir():
        raise NotFoundError("EXPERIMENT_NOT_FOUND", "Experiment does not exist.")
    return directory


def is_immutable(experiment_id: str) -> bool:
    return experiment_id.startswith("paper-a.phase2.")


def inventory_artifacts(experiment_id: str, repo_root: Path) -> list[dict[str, Any]]:
    directory = require_experiment(experiment_id, repo_root)
    items: list[dict[str, Any]] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix not in ARTIFACT_SUFFIXES:
            continue
        if path.is_symlink():
            continue
        relative = path.relative_to(directory).as_posix()
        if ".." in relative.split("/"):
            continue
        size = path.stat().st_size
        digest = sha256_file(path) if size <= 50_000_000 else None
        items.append(
            {
                "artifact_id": encode_artifact_id(experiment_id, relative),
                "experiment_id": experiment_id,
                "relative_path": relative,
                "media_type": _media_type(path.suffix),
                "size_bytes": size,
                "sha256": digest,
            }
        )
    return items


def _media_type(suffix: str) -> str:
    return {
        ".parquet": "application/vnd.apache.parquet",
        ".json": "application/json",
        ".md": "text/markdown",
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".npz": "application/octet-stream",
    }.get(suffix, "application/octet-stream")


def row_count(path: Path) -> int | None:
    if path.suffix != ".parquet" or not path.is_file():
        return None
    import pyarrow.parquet as pq

    return int(pq.ParquetFile(path).metadata.num_rows)
