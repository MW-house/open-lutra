"""Validation feature.

Public API:
    RecordingValidator: base class for per-recording validators
    ValidationContext: the bundle of inputs each validator receives
    ValidationResult: the value a validator returns
    ValidationStatus: pass / warn / fail / error
    register_validator: decorator that registers a custom validator
    ValidationReport, ValidationResultItem: result models
    ValidationRunner: runs every validator and aggregates results

See `custom/README.md` for how to add a custom validator.
"""

from app.features.validation.base import RecordingValidator, ValidationResult, ValidationStatus
from app.features.validation.context import ValidationContext
from app.features.validation.models import ValidationReport, ValidationResultItem
from app.features.validation.registry import load_custom_validators, register_validator
from app.features.validation.runner import ValidationRunner

__all__ = [
    "RecordingValidator",
    "ValidationContext",
    "ValidationReport",
    "ValidationResult",
    "ValidationResultItem",
    "ValidationRunner",
    "ValidationStatus",
    "load_custom_validators",
    "register_validator",
]
