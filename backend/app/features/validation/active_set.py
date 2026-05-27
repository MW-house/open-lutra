"""Active set (params) for builtin validators.

Per decision N1, the params for builtin validators are declared in
Python rather than YAML. Edit this file to apply project-specific
thresholds. If we later want to move configuration to YAML or similar,
only this function needs to change — the registry and runner stay
untouched.
"""

from app.features.validation.base import RecordingValidator
from app.features.validation.builtins import RequiredTopicsPresent, TotalDurationSec


def get_builtin_recording_validators() -> list[RecordingValidator]:
    """Return instantiated builtin validators.

    The MVP defaults are effectively no-ops (empty topic list, no
    bounds). Populate `topics` and `min_sec` / `max_sec` to enable
    real checks.
    """
    return [
        RequiredTopicsPresent(topics=[]),
        TotalDurationSec(min_sec=None, max_sec=None),
    ]
