"""Stable /api/v1 request and response models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.application.job_types import JobType


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorBody


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ready: bool
    checks: dict[str, bool]


class ExperimentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: str = Field(pattern=r"^paper-a\.phase3\.[A-Za-z0-9._-]{1,96}$")


class ExperimentRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_type: JobType = "FULL_PHASE2_PIPELINE"


class ArtifactSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    experiment_id: str
    relative_path: str
    media_type: str
    size_bytes: int
    sha256: str | None


class ArtifactDetail(ArtifactSummary):
    pass


class ExperimentSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: str
    status: str | None
    immutable: bool
    dataset_hash: str | None
    normalization_hash: str | None
    configuration_hash: str | None
    artifact_count: int
    variable_wise_rows: int | None
    combined_rows: int | None
    profile_rows: int | None


class ExperimentDetail(ExperimentSummary):
    manifest: dict[str, Any] | None
    artifacts: list[ArtifactSummary]
    validation_ranking: dict[str, Any] | None
    frozen_dataset_hash: str


class JobProgress(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: str | None
    completed: int | None
    total: int | None
    fraction: float | None


class JobSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    experiment_id: str
    job_type: str
    status: str
    created_at: str
    started_at: str | None
    completed_at: str | None


class JobDetail(JobSummary):
    progress: JobProgress
    message: str | None
    error_code: str | None
    error_message: str | None


class ProfileRow(BaseModel):
    model_config = ConfigDict(extra="allow")


class ProfileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: str
    rows: list[dict[str, Any]]


class ThresholdResponse(ProfileResponse):
    pass


class AsymmetryResponse(ProfileResponse):
    pass


class InterpolationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: str
    seeds: list[dict[str, Any]]


class CombinedCell(BaseModel):
    model_config = ConfigDict(extra="forbid")

    delta_a3: float
    delta_f: float
    median_relative_error_pct: float
    n: int


class CombinedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: str
    response: str
    direction_a3: str
    direction_f: str
    seed: int
    cells: list[CombinedCell]


class PageParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
