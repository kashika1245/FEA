"""Strongly typed scientific configuration. Domain bounds live here, not as magic numbers."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.scientific.exceptions import InvalidConfigurationError
from app.scientific.units import INTERNAL_UNITS, UnitSystem


class ClosedInterval(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    min: float
    max: float

    @model_validator(mode="after")
    def min_le_max(self) -> Self:
        if self.min >= self.max:
            raise ValueError(f"interval requires min < max, got [{self.min}, {self.max}]")
        return self


class ParameterDomain(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    area_mm2: ClosedInterval
    youngs_modulus_gpa: ClosedInterval
    load_kn: ClosedInterval


class DatasetSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    n_samples: int = Field(gt=0)
    train_fraction: float = Field(gt=0.0, lt=1.0)
    validation_fraction: float = Field(gt=0.0, lt=1.0)
    interpolation_test_fraction: float = Field(gt=0.0, lt=1.0)
    random_seed: int = Field(ge=0)

    @model_validator(mode="after")
    def fractions_sum_to_one(self) -> Self:
        total = self.train_fraction + self.validation_fraction + self.interpolation_test_fraction
        if abs(total - 1.0) > 1e-12:
            raise ValueError(f"split fractions must sum to 1, got {total}")
        return self

    def split_counts(self, n_samples: int | None = None) -> tuple[int, int, int]:
        n = self.n_samples if n_samples is None else n_samples
        n_train = int(n * self.train_fraction)
        n_validation = int(n * self.validation_fraction)
        n_test = n - n_train - n_validation
        if n_test <= 0 or n_train <= 0 or n_validation <= 0:
            raise InvalidConfigurationError(
                f"split of N={n} yields non-positive part: "
                f"train={n_train}, validation={n_validation}, test={n_test}"
            )
        return n_train, n_validation, n_test


class NumericalTolerances(BaseModel):
    """Documented FEM comparison tolerances. See paper-a-specification.md §9."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    symmetry_atol: float = Field(gt=0.0)
    symmetry_rtol: float = Field(gt=0.0)
    equilibrium_rtol: float = Field(gt=0.0)
    equilibrium_force_rtol: float = Field(gt=0.0)
    equilibrium_moment_rtol: float = Field(gt=0.0)
    scaling_rtol: float = Field(gt=0.0)
    reference_rtol: float = Field(gt=0.0)
    reference_atol: float = Field(gt=0.0)
    min_length_mm: float = Field(gt=0.0)
    length_reference_mm: float = Field(gt=0.0)


class SolverSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    max_condition_number: float = Field(gt=1.0)
    tolerances: NumericalTolerances


class ReproducibilitySettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    bit_generator: Literal["PCG64"]
    hash_algorithm: Literal["sha256"]


class ScientificConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    software_version: str
    geometry_version: str
    solver_version: str
    dataset_version: str
    parameter_domain: ParameterDomain
    dataset: DatasetSettings
    solver: SolverSettings
    reproducibility: ReproducibilitySettings

    @property
    def units(self) -> UnitSystem:
        return INTERNAL_UNITS

    @property
    def number_of_nodes(self) -> int:
        return 6

    @property
    def number_of_members(self) -> int:
        return 10


def load_scientific_config(path: Path) -> ScientificConfig:
    """Load configuration from YAML using a safe loader."""

    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise InvalidConfigurationError(f"configuration file does not exist: {resolved}")
    try:
        text = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        raise InvalidConfigurationError(f"cannot read configuration file: {resolved}") from exc
    loaded = yaml.safe_load(text)
    if not isinstance(loaded, dict):
        raise InvalidConfigurationError("configuration root must be a mapping")
    try:
        return ScientificConfig.model_validate(loaded)
    except ValidationError as exc:
        raise InvalidConfigurationError(f"invalid scientific configuration: {exc}") from exc


def default_config_path() -> Path:
    """Repository configs/scientific.yaml relative to this file."""

    return Path(__file__).resolve().parents[3] / "configs" / "scientific.yaml"


def load_default_scientific_config() -> ScientificConfig:
    return load_scientific_config(default_config_path())
