"""Secure resolution of experiment artefacts. Clients never supply absolute paths."""

from __future__ import annotations

from pathlib import Path

from app.infrastructure.errors import ForbiddenError, NotFoundError
from app.infrastructure.ids import validate_experiment_id, validate_relative_artifact_path
from app.scientific.dataset.storage import data_root
from app.scientific.exceptions import StorageSecurityError
from app.scientific.reproducibility import repo_root_from_package


def experiments_root(repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else repo_root_from_package()
    return (data_root(root) / "experiments").resolve()


def app_data_root(repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else repo_root_from_package()
    path = (data_root(root) / "app").resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def experiment_dir(experiment_id: str, repo_root: Path | None = None) -> Path:
    validate_experiment_id(experiment_id)
    base = experiments_root(repo_root)
    candidate = (base / experiment_id).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise ForbiddenError(
            "PATH_ESCAPE", "Resolved experiment path left the approved root."
        ) from exc
    if candidate != base / experiment_id and not str(candidate).startswith(str(base)):
        raise ForbiddenError("PATH_ESCAPE", "Resolved experiment path left the approved root.")
    return candidate


def resolve_artifact(experiment_id: str, relative_path: str, repo_root: Path | None = None) -> Path:
    rel = validate_relative_artifact_path(relative_path)
    root = experiment_dir(experiment_id, repo_root)
    if not root.is_dir():
        raise NotFoundError("EXPERIMENT_NOT_FOUND", "Experiment does not exist.")
    candidate = root / rel
    if candidate.is_symlink() or any(
        parent.is_symlink() for parent in candidate.parents if str(parent).startswith(str(root))
    ):
        raise ForbiddenError("SYMLINK_REJECTED", "Symlinked artifacts are not served.")
    target = candidate.resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise ForbiddenError("PATH_ESCAPE", "Artifact path escaped the experiment root.") from exc
    if not target.is_file():
        raise NotFoundError("ARTIFACT_NOT_FOUND", "Artifact does not exist.")
    if target.is_symlink():
        raise ForbiddenError("SYMLINK_REJECTED", "Symlinked artifacts are not served.")
    return target


def confine_or_forbidden(path: Path, repo_root: Path | None = None) -> Path:
    from app.scientific.dataset.storage import confine_under_data_root

    try:
        return confine_under_data_root(path, repo_root)
    except StorageSecurityError as exc:
        raise ForbiddenError("PATH_ESCAPE", "Path is outside the approved data root.") from exc
