"""Typed dataset row schema in paper-facing units."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SplitName = Literal["train", "validation", "interpolation_test"]

COLUMN_ORDER: tuple[str, ...] = (
    "sample_id",
    "split",
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
    "u_max",
    "sigma_max",
    "C",
)

COLUMN_UNITS: dict[str, str] = {
    "sample_id": "1",
    "split": "categorical",
    "A1": "mm^2",
    "A2": "mm^2",
    "A3": "mm^2",
    "A4": "mm^2",
    "A5": "mm^2",
    "A6": "mm^2",
    "A7": "mm^2",
    "A8": "mm^2",
    "A9": "mm^2",
    "A10": "mm^2",
    "E": "GPa",
    "F": "kN",
    "u_max": "mm",
    "sigma_max": "N/mm^2",
    "C": "N*mm",
}


class DatasetRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sample_id: int = Field(ge=1)
    split: SplitName
    A1: float
    A2: float
    A3: float
    A4: float
    A5: float
    A6: float
    A7: float
    A8: float
    A9: float
    A10: float
    E: float
    F: float
    u_max: float
    sigma_max: float
    C: float

    def to_ordered_dict(self) -> dict[str, int | float | str]:
        payload = self.model_dump()
        return {key: payload[key] for key in COLUMN_ORDER}
