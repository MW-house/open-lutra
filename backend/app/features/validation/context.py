"""Context object passed to every validator.

Bundling the inputs into a single object lets us add new fields later
(recording_meta, mcap_path, ...) without changing every validator's
signature.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from app.features.analysis.models import QualityReport
    from app.features.recordings.meta import RecordingMeta


@dataclass(frozen=True)
class ValidationContext:
    """Inputs available to a validator's `validate()` call.

    Attributes:
        report: The quality analysis result. Always present (validation
            runs only after a successful quality job).
        recording_dir: The recording folder (e.g. `output/20260308_150000`).
            Useful for reading sibling artifacts.
        mcap_path: Path to the MCAP file in the recording folder, or
            `None` if the file is missing. Open with `MCAPReader` from
            `app.infra.mcap` when the validator needs raw messages.
        recording_meta: Parsed `recording_meta.json`, or `None` if the
            file is missing (older folders) or unreadable.
    """

    report: QualityReport
    recording_dir: Path
    mcap_path: Path | None
    recording_meta: RecordingMeta | None
