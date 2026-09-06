"""Dataset metadata schema linked to the Parquet artefact by content hash."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DatasetMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    dataset_id: str
    dataset_version: str
    sample_count: int = Field(ge=0)
    requested_sample_count: int = Field(ge=1)
    random_seed: int
    geometry_version: str
    solver_version: str
    software_version: str
    git_commit: str | None
    unit_system: dict[str, str]
    parameter_domains: dict[str, Any]
    output_definitions: dict[str, str]
    generation_timestamp_utc: str
    configuration_hash: str
    dataset_hash: str
    parquet_path: str
    split_counts: dict[str, int]
    failed_fea_count: int = Field(ge=0)
    status: str
