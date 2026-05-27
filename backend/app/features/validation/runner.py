"""Validation execution loop.

Collects builtin validators (from active_set) and custom validators
(from the registry), runs each one against a `ValidationContext`,
converts unexpected exceptions into status="error", and assembles a
`ValidationReport`.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

from app.features.analysis.models import QualityReport
from app.features.recordings.meta import RecordingMeta
from app.features.validation.active_set import get_builtin_recording_validators
from app.features.validation.base import RecordingValidator, ValidationResult
from app.features.validation.context import ValidationContext
from app.features.validation.models import ValidationReport, ValidationResultItem
from app.features.validation.registry import get_custom_validators

logger = logging.getLogger(__name__)


class ValidationRunner:
    """Runs every registered validator against a recording."""

    def run(
        self,
        report: QualityReport,
        *,
        recording_dir: Path,
        mcap_path: Path | None,
        recording_meta: RecordingMeta | None,
    ) -> ValidationReport:
        """Execute all validators and aggregate the results.

        Args:
            report: The quality analysis result to validate.
            recording_dir: The recording folder. Exposed to validators
                via `ValidationContext.recording_dir`.
            mcap_path: Path to the recording's MCAP file, or None if the
                file is missing.
            recording_meta: Parsed `recording_meta.json`, or None when
                the file does not exist. `task_name` for the aggregated
                report is taken from here.

        Returns:
            A ValidationReport containing per-validator items and an
            aggregated overall_status.
        """
        ctx = ValidationContext(
            report=report,
            recording_dir=recording_dir,
            mcap_path=mcap_path,
            recording_meta=recording_meta,
        )

        items: list[ValidationResultItem] = []

        for validator in get_builtin_recording_validators():
            items.append(self._run_one(validator, ctx, source="builtin", source_module=None))

        for validator in get_custom_validators():
            items.append(
                self._run_one(
                    validator,
                    ctx,
                    source="custom",
                    source_module=type(validator).__module__,
                )
            )

        return ValidationReport.aggregate(
            results=items,
            task_name=recording_meta.task_name if recording_meta is not None else None,
            executed_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _run_one(
        validator: RecordingValidator,
        ctx: ValidationContext,
        *,
        source: str,
        source_module: str | None,
    ) -> ValidationResultItem:
        """Run a single validator. Converts unexpected exceptions into status="error"."""
        try:
            result = validator.validate(ctx)
        except Exception as e:
            logger.exception("Validator raised an exception: %s", validator.name)
            result = ValidationResult(
                status="error",
                message=f"Validator execution error: {type(e).__name__}: {e}",
            )

        return ValidationResultItem(
            validator_name=validator.name,
            source=source,
            source_module=source_module,
            status=result.status,
            message=result.message,
            details=result.details,
        )
