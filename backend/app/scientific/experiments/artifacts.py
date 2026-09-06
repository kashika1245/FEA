"""Approved Phase 2 artefact directories under data/experiments."""

from __future__ import annotations

from pathlib import Path

from app.scientific.dataset.storage import confine_under_data_root
from app.scientific.reproducibility import repo_root_from_package
from app.scientific.surrogate.config import Phase2Config


class ExperimentPaths:
    def __init__(self, root: Path, experiment_id: str, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root if repo_root is not None else repo_root_from_package()
        self.root = confine_under_data_root(root, self.repo_root)
        self.experiment_id = experiment_id
        self.models = self.root / "models"
        self.interpolation = self.root / "interpolation"
        self.anchors = self.root / "anchors"
        self.extrapolation = self.root / "extrapolation"
        self.chunks = self.extrapolation / "chunks"
        self.profiles = self.root / "profiles"
        self.combined = self.root / "combined"
        self.combined_chunks = self.combined / "chunks"
        self.reports = self.root / "reports"
        self.failures = self.root / "failures"
        for path in (
            self.models,
            self.interpolation,
            self.anchors,
            self.extrapolation,
            self.chunks,
            self.profiles,
            self.combined,
            self.combined_chunks,
            self.reports,
            self.failures,
        ):
            path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def for_config(cls, config: Phase2Config, repo_root: Path | None = None) -> ExperimentPaths:
        root = (
            (repo_root if repo_root is not None else repo_root_from_package())
            / "data"
            / "experiments"
            / config.phase2_version
        )
        return cls(root, config.phase2_version, repo_root)

    def model_dir(self, seed: int) -> Path:
        return self.models / f"seed-{seed}"

    def chunk_path(self, seed: int, variable: str, direction: str) -> Path:
        return self.chunks / f"seed{seed}-{variable}-{direction}.parquet"

    def combined_chunk_path(self, seed: int, direction_a3: str, direction_f: str) -> Path:
        return self.combined_chunks / f"seed{seed}-A3{direction_a3}-F{direction_f}.parquet"
