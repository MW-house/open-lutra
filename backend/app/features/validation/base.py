"""Base classes and common types for validation.

Public API:
    RecordingValidator: base class for per-recording validators
    ValidationResult: the value a validator returns
    ValidationStatus: pass / warn / fail / error
"""

from abc import ABC, abstractmethod
from typing import ClassVar, Literal

from pydantic import BaseModel

from app.features.validation.context import ValidationContext

# pass / warn / fail are returned by the validator itself.
# error is set only by the runner when it catches an exception
# (validators are not expected to return "error" directly).
ValidationStatus = Literal["pass", "warn", "fail", "error"]


class ValidationResult(BaseModel):
    """Result of a single validator invocation.

    `status` and `message` are required. `message` is the human-facing
    sentence rendered in the recording detail page.

    `details` is an optional free-form, JSON-serializable dict used to
    record the structured evidence behind the result — typically the
    same numeric values or lists referenced in `message`, so downstream
    tooling can read them without parsing the sentence. It is persisted
    to `validation_result.json` and exposed via `GET /api/validation`,
    but is **not** rendered in the current UI; put anything users must
    see in `message` as well. Convention: leave `None` on pass; on
    warn/fail include the offending values and the threshold they were
    compared against. Examples:

        # required_topics_present (fail)
        details={"missing_topics": ["/cam/front"], "required_topics": [...]}

        # total_duration_sec (fail)
        details={"duration_sec": 4.2, "min_sec": 5.0}

    See `docs/domain/custom_validators.md` for the full conventions.
    """

    status: ValidationStatus
    message: str
    details: dict[str, object] | None = None


class RecordingValidator(ABC):
    """Base class for validators that evaluate a single recording.

    Subclasses declare `name` as a ClassVar and implement `validate()`.
    The context object exposes the QualityReport, the MCAP file path,
    and the recording meta — see `ValidationContext`.
    """

    name: ClassVar[str]

    @abstractmethod
    def validate(self, ctx: ValidationContext) -> ValidationResult:
        """Evaluate the recording and return a result.

        If this method raises, the runner converts the failure into
        a ValidationResult with status="error".
        """
