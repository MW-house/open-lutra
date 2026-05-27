"""Builtin validators.

Each class is a generic implementation that takes params via its
constructor. `active_set.py` instantiates them with concrete params.
"""

from app.features.validation.builtins.required_topics_present import RequiredTopicsPresent
from app.features.validation.builtins.total_duration_sec import TotalDurationSec

__all__ = ["RequiredTopicsPresent", "TotalDurationSec"]
