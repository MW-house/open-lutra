"""Load and save `validation_result.json`.

Stored alongside `quality_report.json` in the recording directory.
"""

import json
import logging
from pathlib import Path

from app.features.validation.models import ValidationReport

logger = logging.getLogger(__name__)

CACHE_FILENAME = "validation_result.json"


def save_report(directory: Path, report: ValidationReport) -> None:
    """Persist the ValidationReport as validation_result.json."""
    path = directory / CACHE_FILENAME
    path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Saved validation report: %s", path)


def load_report(directory: Path) -> ValidationReport | None:
    """Read validation_result.json if present.

    Returns None when the file is missing or unreadable (only a warning
    is logged in the latter case).
    """
    path = directory / CACHE_FILENAME
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return ValidationReport.model_validate(data)
    except (json.JSONDecodeError, ValueError, OSError) as e:
        logger.warning("Failed to read validation report: %s (%s)", path, e)
        return None
