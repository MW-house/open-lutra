"""Validator that checks the total recording duration (seconds)."""

from typing import ClassVar

from app.features.validation.base import RecordingValidator, ValidationResult
from app.features.validation.context import ValidationContext


class TotalDurationSec(RecordingValidator):
    """Verify the recording's duration_sec falls within `[min_sec, max_sec]`.

    Passing `None` for `min_sec` or `max_sec` disables that side of the
    check. When both are `None`, the validator always returns pass.
    """

    name: ClassVar[str] = "total_duration_sec"

    def __init__(self, *, min_sec: float | None = None, max_sec: float | None = None) -> None:
        self.min_sec = min_sec
        self.max_sec = max_sec

    def validate(self, ctx: ValidationContext) -> ValidationResult:
        if self.min_sec is None and self.max_sec is None:
            return ValidationResult(status="pass", message="No duration bounds configured")

        duration = ctx.report.duration_sec

        if self.min_sec is not None and duration < self.min_sec:
            return ValidationResult(
                status="fail",
                message=f"Duration {duration:.1f}s is below minimum {self.min_sec:.1f}s",
                details={"duration_sec": duration, "min_sec": self.min_sec},
            )

        if self.max_sec is not None and duration > self.max_sec:
            return ValidationResult(
                status="fail",
                message=f"Duration {duration:.1f}s exceeds maximum {self.max_sec:.1f}s",
                details={"duration_sec": duration, "max_sec": self.max_sec},
            )

        return ValidationResult(status="pass", message=f"Duration {duration:.1f}s (within range)")
