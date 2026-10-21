"""Metadata field master, read from the recording config's `metadata_fields` section.

recording_meta.json stores only stable ids ("A000"), so the master is what turns
them into the human-readable "{id}_{label}" shown in the UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .config import ConfigError


@dataclass(frozen=True)
class FieldOption:
    value: str
    display: str


@dataclass(frozen=True)
class MetadataField:
    key: str
    label: str
    type: str
    options: tuple[FieldOption, ...]

    def display_for(self, value: str) -> str:
        """Human-readable form of a stored value; unknown values fall back to the raw id."""
        for option in self.options:
            if option.value == value:
                return option.display
        return value


def load_metadata_fields(recording_config_path: Path) -> list[MetadataField]:
    """Read the field master. A config without `metadata_fields` yields an empty list."""
    if not recording_config_path.is_file():
        raise ConfigError(f"Recording config not found: {recording_config_path}")

    raw = yaml.safe_load(recording_config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConfigError(f"Recording config must contain a YAML mapping: {recording_config_path}")

    declared = raw.get("metadata_fields") or []
    if not isinstance(declared, list):
        raise ConfigError(f"'metadata_fields' must be a list in {recording_config_path}")

    return [
        _parse_field(entry) for entry in declared if isinstance(entry, dict) and entry.get("key")
    ]


def option_display(value: str, label: str | None) -> str:
    """Format an option as "{id}_{label}", tolerating masters whose label already carries the id."""
    if not label:
        return value
    if label == value or label.startswith(f"{value}_"):
        return label
    return f"{value}_{label}"


def _parse_field(entry: dict) -> MetadataField:
    key = str(entry["key"])
    options = tuple(
        FieldOption(
            value=str(option["value"]),
            display=option_display(str(option["value"]), option.get("label")),
        )
        for option in entry.get("options") or []
        if isinstance(option, dict) and option.get("value") is not None
    )
    return MetadataField(
        key=key,
        label=str(entry.get("label") or key),
        type=str(entry.get("type") or "select"),
        options=options,
    )
