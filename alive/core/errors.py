"""The error taxonomy.

The API layer maps each class to an HTTP status via its ``status`` attribute and
surfaces ``code`` as a stable, machine-readable string. Services raise these;
the core raises only ``ValidationError``/``UnitMismatchError``/``SequenceError``
(it has no notion of HTTP or storage).
"""

from __future__ import annotations


class AliveError(Exception):
    """Base for everything the engine raises on bad input or state."""

    status = 400
    code = "error"

    def __init__(self, message: str = "") -> None:
        super().__init__(message)
        self.message = message or self.code


class ValidationError(AliveError):
    status = 400
    code = "validation_error"


class UnitMismatchError(ValidationError):
    """A sample's unit can't be normalized to the metric's canonical unit."""

    code = "unit_mismatch"


class SequenceError(ValidationError):
    """A device's per-device sequence number went backwards or repeated."""

    status = 409
    code = "sequence_error"


class NotFoundError(AliveError):
    status = 404
    code = "not_found"


class ConflictError(AliveError):
    status = 409
    code = "conflict"


class EnrollmentError(AliveError):
    """A sample arrived for a member/device that isn't enrolled."""

    status = 409
    code = "not_enrolled"
