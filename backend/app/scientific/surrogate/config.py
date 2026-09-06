"""Typed Phase 2 configuration. Frozen protocol numbers live here, not in callers."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.scientific.exceptions import InvalidConfigurationError

INPUT_NAMES: tuple[str, ...] = (
    "A1",
    "A2",
    "A3",
    "A4",
    "A5",
    "A6",
    "A7",
    "A8",
    "A9",
    "A10",
    "E",
    "F",
)
OUTPUT_NAMES: tuple[str, ...] = ("u_max", "sigma_max", "C")
SPLIT_NAMES: tuple[str, ...] = ("train", "validation", "interpolation_test")
DirectionName = Literal["lower", "upper"]
VariableName = Literal["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "E", "F"]


class SurrogateSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    hidden_units: tuple[int, int, int]
    activation: Literal["relu"]
    loss: Literal["mse"]
    optimizer: Literal["adam"]
    learning_rate: float = Field(gt=0.0)
    batch_size: int = Field(gt=0)
    max_epochs: int = Field(gt=0)
    early_stopping_patience: int = Field(gt=0)
    input_normalization: Literal["zscore"]
    output_scaling: Literal["zscore"]
    seeds: tuple[int, ...]
    model_selection_rule: Literal["retain_all_five_seeds"]
    ranking_rule: Literal["lowest_validation_mse_only"]

    @model_validator(mode="after")
    def architecture_is_frozen(self) -> Self:
        if self.hidden_units != (128, 128, 128):
            raise ValueError("frozen architecture requires hidden_units=(128, 128, 128)")
        if len(self.seeds) != 5:
            raise ValueError("exactly five deterministic seeds are required")
        if len(set(self.seeds)) != 5:
            raise ValueError("seeds must be unique")
        return self


class InterpolationGateSettings(BaseModel):
    """Predetermined in-domain competence criteria. Not engineering safety limits."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    min_r2: float
    max_median_relative_error_pct: float = Field(gt=0.0)
    max_catastrophic_relative_error_pct: float = Field(gt=0.0)
    require_finite: bool
    all_seeds_must_pass: bool


class AnchorSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    count: int = Field(gt=0)
    source_split: Literal["interpolation_test"]
    selection_method: Literal["pcg64_without_replacement"]
    selection_seed: int = Field(ge=0)


class ExtrapolationSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    variables: tuple[VariableName, ...]
    directions: tuple[DirectionName, ...]
    deltas: tuple[float, ...]
    threshold_pct: tuple[float, ...]

    @model_validator(mode="after")
    def protocol_is_complete(self) -> Self:
        expected_vars = INPUT_NAMES
        if self.variables != expected_vars:
            raise ValueError(f"frozen variable list must be {expected_vars}")
        if self.directions != ("lower", "upper"):
            raise ValueError("both lower and upper directions are required")
        if len(self.deltas) < 2 or self.deltas[0] != 0.0:
            raise ValueError("delta grid must start at 0.0")
        if any(delta < 0.0 for delta in self.deltas):
            raise ValueError("distance delta must be non-negative")
        if tuple(self.deltas) != tuple(sorted(self.deltas)):
            raise ValueError("delta grid must be strictly non-decreasing")
        if any(value <= 0.0 for value in self.threshold_pct):
            raise ValueError("threshold percentages must be positive")
        return self


class CombinedSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    variables: tuple[VariableName, VariableName]
    deltas_a3: tuple[float, ...]
    deltas_f: tuple[float, ...]
    directions_a3: tuple[DirectionName, ...]
    directions_f: tuple[DirectionName, ...]

    @model_validator(mode="after")
    def combined_is_a3_f(self) -> Self:
        if self.variables != ("A3", "F"):
            raise ValueError("the only combined experiment is A3 + F")
        if self.deltas_a3[0] != 0.0 or self.deltas_f[0] != 0.0:
            raise ValueError("combined delta grids must include 0.0")
        if any(delta < 0.0 for delta in (*self.deltas_a3, *self.deltas_f)):
            raise ValueError("combined deltas must be non-negative")
        return self


class PerformanceSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mlp_batch_size: int = Field(gt=0)
    fem_cache: bool


class Phase2Config(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    phase2_version: str
    software_version: str
    paper: str
    phase: Literal[2]
    relative_error_epsilon: float = Field(gt=0.0)
    surrogate: SurrogateSettings
    interpolation_gate: InterpolationGateSettings
    anchors: AnchorSettings
    extrapolation: ExtrapolationSettings
    combined: CombinedSettings
    performance: PerformanceSettings

    def expected_variable_wise_count(self, n_models: int, n_anchors: int) -> int:
        return (
            n_anchors
            * len(self.extrapolation.variables)
            * len(self.extrapolation.directions)
            * len(self.extrapolation.deltas)
            * n_models
        )

    def expected_combined_count(self, n_models: int, n_anchors: int) -> int:
        return (
            n_anchors
            * len(self.combined.deltas_a3)
            * len(self.combined.deltas_f)
            * len(self.combined.directions_a3)
            * len(self.combined.directions_f)
            * n_models
        )


def load_phase2_config(path: Path) -> Phase2Config:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise InvalidConfigurationError(f"Phase 2 configuration file does not exist: {resolved}")
    try:
        loaded = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    except OSError as exc:
        raise InvalidConfigurationError(f"cannot read Phase 2 configuration: {resolved}") from exc
    if not isinstance(loaded, dict):
        raise InvalidConfigurationError("Phase 2 configuration root must be a mapping")
    try:
        return Phase2Config.model_validate(loaded)
    except ValidationError as exc:
        raise InvalidConfigurationError(f"invalid Phase 2 configuration: {exc}") from exc


def default_phase2_config_path() -> Path:
    return Path(__file__).resolve().parents[4] / "configs" / "phase2.yaml"


def load_default_phase2_config() -> Phase2Config:
    return load_phase2_config(default_phase2_config_path())
