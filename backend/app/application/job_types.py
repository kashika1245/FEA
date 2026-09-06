"""Server-side job types. Clients cannot invent scientific configurations."""

from __future__ import annotations

from typing import Literal

JobType = Literal[
    "TRAIN_SURROGATE",
    "INTERPOLATION_EVALUATION",
    "EXTRAPOLATION",
    "COMBINED_EXTRAPOLATION",
    "PROFILE_BUILD",
    "REPORT_BUILD",
    "FULL_PHASE2_PIPELINE",
]

PilotProfile = Literal["pilot_tiny", "pilot_10a", "frozen_readonly"]

IMMUTABLE_PREFIX = "paper-a.phase2."
