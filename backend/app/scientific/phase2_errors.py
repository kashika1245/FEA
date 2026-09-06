"""Typed Phase 2 failures. Never converted into fake scientific values."""

from app.scientific.exceptions import ScientificError


class Phase2Error(ScientificError):
    """Base class for Phase 2 surrogate and extrapolation failures."""


class Phase1IntegrityError(Phase2Error):
    """The frozen Phase 1 dataset failed the Phase 2 consumption gate."""


class NormalizationError(Phase2Error):
    """Train-only normalization cannot be fitted or applied."""


class SurrogateError(Phase2Error):
    """MLP construction, training, or prediction failed."""


class InterpolationGateError(Phase2Error):
    """In-domain competence is insufficient for extrapolation interpretation."""


class ExtrapolationError(Phase2Error):
    """Extrapolation coordinate generation or evaluation failed."""


class ExperimentError(Phase2Error):
    """Experiment orchestration, resume, or integrity failed."""


class ReportingError(Phase2Error):
    """A report or plot cannot be generated from stored artefacts."""
