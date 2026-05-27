"""Validation API endpoints."""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends

from app.dependencies import require_dir
from app.features.validation.schemas import ValidationResponse
from app.features.validation.service import get_validation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/validation", tags=["validation"])


@router.get("", response_model=ValidationResponse, operation_id="getValidation")
async def get_validation(  # pragma: no cover
    target: Path = Depends(require_dir),
) -> ValidationResponse:
    """Return the cached validation report (no side effects).

    Trigger a new run via POST /api/validation/analyze.
    """
    return await get_validation_service().get(target)


@router.post("/analyze", response_model=ValidationResponse, operation_id="startValidation")
async def start_validation(  # pragma: no cover
    target: Path = Depends(require_dir),
) -> ValidationResponse:
    """Trigger validation (idempotent: returns the existing job's status if running)."""
    return await get_validation_service().start(target)
