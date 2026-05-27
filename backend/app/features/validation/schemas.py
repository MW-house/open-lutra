"""API schemas for validation endpoints.

Domain models live in `models.py`. This module only wraps them for HTTP responses.
"""

from pydantic import BaseModel, Field

from app.features.validation.models import ValidationReport


class ValidationResponse(BaseModel):
    """Response for GET / POST /api/validation."""

    status: str = Field(..., pattern=r"^(ready|analyzing|not_found|error)$")
    report: ValidationReport | None
    error: str | None
