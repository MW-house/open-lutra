"""The well-formed validator inside `mixed_plugin`."""

from typing import ClassVar

from app.features.validation import (
    RecordingValidator,
    ValidationContext,
    ValidationResult,
    register_validator,
)


@register_validator
class MixedGoodValidator(RecordingValidator):
    """The good validator inside `mixed_plugin`."""

    name: ClassVar[str] = "mixed_good_validator"

    def validate(self, ctx: ValidationContext) -> ValidationResult:
        return ValidationResult(status="pass", message="mixed good ok")
