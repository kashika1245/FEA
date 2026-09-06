"""Independently auditable experiment manifest."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from app.scientific.reproducibility import canonical_json_bytes, sha256_bytes
from app.scientific.surrogate.config import Phase2Config


class ExperimentManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    experiment_id: str
    paper: str
    phase: int
    dataset_id: str
    dataset_hash: str
    geometry_version: str
    solver_version: str
    model_architecture: str
    seeds: tuple[int, ...]
    anchor_count: int
    variables: tuple[str, ...]
    directions: tuple[str, ...]
    delta_grid: tuple[float, ...]
    epsilon: float
    normalization_hash: str
    selection_rule: str
    ranking_rule: str
    combined_experiment: str
    software_version: str
    configuration_hash: str
    status: str
    expected_variable_wise_observations: int
    expected_combined_observations: int


def build_manifest(
    config: Phase2Config,
    *,
    dataset_id: str,
    dataset_hash: str,
    geometry_version: str,
    solver_version: str,
    normalization_hash: str,
    n_models: int,
    n_anchors: int,
    status: str,
) -> ExperimentManifest:
    payload = config.model_dump()
    configuration_hash = sha256_bytes(canonical_json_bytes(payload))
    return ExperimentManifest(
        experiment_id=config.phase2_version,
        paper=config.paper,
        phase=config.phase,
        dataset_id=dataset_id,
        dataset_hash=dataset_hash,
        geometry_version=geometry_version,
        solver_version=solver_version,
        model_architecture="12-128-128-128-3",
        seeds=config.surrogate.seeds,
        anchor_count=n_anchors,
        variables=config.extrapolation.variables,
        directions=config.extrapolation.directions,
        delta_grid=config.extrapolation.deltas,
        epsilon=config.relative_error_epsilon,
        normalization_hash=normalization_hash,
        selection_rule=config.surrogate.model_selection_rule,
        ranking_rule=config.surrogate.ranking_rule,
        combined_experiment="A3+F",
        software_version=config.software_version,
        configuration_hash=configuration_hash,
        status=status,
        expected_variable_wise_observations=config.expected_variable_wise_count(
            n_models, n_anchors
        ),
        expected_combined_observations=config.expected_combined_count(n_models, n_anchors),
    )


def write_manifest(path: Any, manifest: ExperimentManifest) -> None:
    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
