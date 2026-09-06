"""Typed scientific exceptions. Failures are never silently repaired."""


class ScientificError(Exception):
    """Base class for all scientific-engine failures."""


class InvalidGeometryError(ScientificError):
    """Node coordinates or member lengths are not a valid truss geometry."""


class InvalidTopologyError(ScientificError):
    """Connectivity, supports, or load placement is structurally invalid."""


class InvalidMaterialError(ScientificError):
    """Area or Young's modulus is not a valid finite positive material parameter."""


class InvalidLoadError(ScientificError):
    """Applied load specification or magnitude is invalid."""


class InvalidParameterError(ScientificError):
    """A structural parameter vector cannot be used for analysis."""


class InvalidConfigurationError(ScientificError):
    """Scientific configuration file or object is invalid."""


class FEASolverError(ScientificError):
    """Finite-element solve failed for a reason other than singularity."""


class SingularStructureError(FEASolverError):
    """Reduced stiffness matrix is singular (mechanism or missing support)."""


class NumericalStabilityError(FEASolverError):
    """Finite but untrustworthy numerical state (non-finite values or extreme condition)."""


class DatasetError(ScientificError):
    """Dataset generation, validation, or hashing failed."""


class CheckpointError(DatasetError):
    """Checkpoint read/write or recovery failed."""


class StorageSecurityError(DatasetError):
    """A requested filesystem path is outside the allowed data root."""
