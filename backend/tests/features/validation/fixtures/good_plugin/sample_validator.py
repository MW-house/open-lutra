"""A well-formed custom validator used in tests."""

from typing import ClassVar

from app.features.validation import (
    RecordingValidator,
    ValidationContext,
    ValidationResult,
    register_validator,
)


@register_validator
class SampleValidator(RecordingValidator):
    """Test validator that always returns pass."""

    name: ClassVar[str] = "sample_validator"

    def validate(self, ctx: ValidationContext) -> ValidationResult:
        return ValidationResult(status="pass", message="sample ok")
