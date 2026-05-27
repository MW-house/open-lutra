"""Validator that checks the presence of required topics."""

from typing import ClassVar

from app.features.validation.base import RecordingValidator, ValidationResult
from app.features.validation.context import ValidationContext


class RequiredTopicsPresent(RecordingValidator):
    """Verify every listed topic exists in the MCAP with at least one message."""

    name: ClassVar[str] = "required_topics_present"

    def __init__(self, topics: list[str]) -> None:
        self.topics = list(topics)

    def validate(self, ctx: ValidationContext) -> ValidationResult:
        if not self.topics:
            return ValidationResult(status="pass", message="No required topics configured")

        present = {t.name for t in ctx.report.topics if t.message_count > 0}
        missing = [t for t in self.topics if t not in present]

        if missing:
            return ValidationResult(
                status="fail",
                message=f"Required topics missing ({len(missing)}/{len(self.topics)}): {', '.join(missing)}",
                details={"missing_topics": missing, "required_topics": self.topics},
            )

        return ValidationResult(
            status="pass",
            message=f"All {len(self.topics)} required topics present",
        )
