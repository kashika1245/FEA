from __future__ import annotations

from pathlib import Path

import pytest

from app.infrastructure.errors import ForbiddenError, NotFoundError, ValidationAppError
from app.infrastructure.paths import resolve_artifact


def test_path_traversal_and_absolute(tmp_path: Path) -> None:
    experiment = tmp_path / "data" / "experiments" / "paper-a.phase3.sec"
    experiment.mkdir(parents=True)
    (experiment / "manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises((ValidationAppError, ForbiddenError, NotFoundError)):
        resolve_artifact("paper-a.phase3.sec", "../../etc/passwd", tmp_path)
        with pytest.raises((ValidationAppError, ForbiddenError, NotFoundError)):
            resolve_artifact("paper-a.phase3.sec", "/etc/passwd", tmp_path)


def test_symlink_rejected(tmp_path: Path) -> None:
    experiment = tmp_path / "data" / "experiments" / "paper-a.phase3.sec"
    experiment.mkdir(parents=True)
    target = tmp_path / "outside.txt"
    target.write_text("secret", encoding="utf-8")
    link = experiment / "escape.json"
    link.symlink_to(target)
    with pytest.raises((ForbiddenError, NotFoundError)):
        resolve_artifact("paper-a.phase3.sec", "escape.json", tmp_path)
