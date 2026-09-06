"""Process settings. Not a scientific configuration file."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.infrastructure.paths import app_data_root
from app.scientific.reproducibility import repo_root_from_package

DEFAULT_CORS = "http://127.0.0.1:5173,http://localhost:5173"


def cors_origins_from_env() -> tuple[str, ...]:
    raw = os.environ.get("PAPER_A_CORS_ORIGINS", DEFAULT_CORS)
    return tuple(item.strip() for item in raw.split(",") if item.strip() and item.strip() != "*")


@dataclass(frozen=True, slots=True)
class AppSettings:
    repo_root: Path
    db_path: Path
    max_running_jobs: int
    max_page_limit: int
    research_page_limit: int
    mutate_rate_limit: int
    trusted_network: bool
    cors_origins: tuple[str, ...]

    @classmethod
    def from_repo(cls, repo_root: Path | None = None, db_path: Path | None = None) -> AppSettings:
        root = repo_root if repo_root is not None else repo_root_from_package()
        database = db_path if db_path is not None else app_data_root(root) / "phase3.sqlite"
        return cls(
            repo_root=root,
            db_path=database,
            max_running_jobs=1,
            max_page_limit=100,
            research_page_limit=2000,
            mutate_rate_limit=30,
            trusted_network=True,
            cors_origins=cors_origins_from_env(),
        )
