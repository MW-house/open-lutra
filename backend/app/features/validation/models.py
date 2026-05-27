"""Domain models for validation results.

A single `ValidationReport` is produced per recording (aggregating each
validator's outcome) and persisted as `validation_result.json`.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.features.validation.base import ValidationStatus

# Weights used to compute overall_status. "error" outranks "fail" because
# it indicates a validator implementation problem rather than a data
# problem, and should surface prominently in the UI.
_SEVERITY_ORDER: dict[ValidationStatus, int] = {
    "pass": 0,
    "warn": 1,
    "fail": 2,
    "error": 3,
}


class ValidationResultItem(BaseModel):
    """A single validator's outcome."""

    validator_name: str
    source: str = Field(..., pattern=r"^(builtin|custom)$")
    source_module: str | None = Field(
        ...,
        description='Only set for custom validators. Example: "app.features.validation.custom.my_check"',
    )
    status: ValidationStatus
    message: str
    details: dict[str, object] | None


class ValidationReport(BaseModel):
    """All validation results for one recording."""

    overall_status: ValidationStatus
    results: list[ValidationResultItem]
    task_name: str | None
    executed_at: datetime

    @classmethod
    def aggregate(
        cls,
        *,
        results: list[ValidationResultItem],
        task_name: str | None,
        executed_at: datetime,
    ) -> "ValidationReport":
        """Build a report from individual results, deriving overall_status."""
        return cls(
            overall_status=_worst_status([r.status for r in results]),
            results=results,
            task_name=task_name,
            executed_at=executed_at,
        )


def _worst_status(statuses: list[ValidationStatus]) -> ValidationStatus:
    """Return the most severe status. Defaults to "pass" for an empty list."""
    worst: ValidationStatus = "pass"
    for s in statuses:
        if _SEVERITY_ORDER[s] > _SEVERITY_ORDER[worst]:
            worst = s
    return worst
