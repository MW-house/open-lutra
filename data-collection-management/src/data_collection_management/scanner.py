"""Scan the output directory into per-recording records (metadata + duration)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

META_FILENAME = "recording_meta.json"
BAG_METADATA_FILENAME = "metadata.yaml"
QUALITY_REPORT_FILENAME = "quality_report.json"

# Directories the recorder reserves for its own artifacts (e.g. _lerobot_exports).
RESERVED_PREFIX = "_"

# Recording directories are named "<YYYYmmdd>_<HHMMSS>".
NAME_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
NAME_TIMESTAMP_LENGTH = 15


@dataclass(frozen=True)
class Recording:
    name: str
    task_name: str | None
    started_at: datetime | None
    duration_sec: float
    metadata: dict[str, str] = field(default_factory=dict)


def scan_recordings(output_dir: Path) -> list[Recording]:
    """Collect every recording directory holding a recording_meta.json, newest first."""
    if not output_dir.is_dir():
        return []

    recordings = [
        recording
        for entry in output_dir.iterdir()
        if entry.is_dir() and not entry.name.startswith(RESERVED_PREFIX)
        if (recording := _read_recording(entry)) is not None
    ]
    recordings.sort(key=lambda item: item.name, reverse=True)
    return recordings


def _read_recording(directory: Path) -> Recording | None:
    meta_path = directory / META_FILENAME
    if not meta_path.is_file():
        return None

    meta = _read_json(meta_path) or {}
    raw_metadata = meta.get("metadata")
    metadata = (
        {str(key): str(value) for key, value in raw_metadata.items() if value is not None}
        if isinstance(raw_metadata, dict)
        else {}
    )

    duration_sec, started_at = _read_duration_and_start(directory)
    task_name = meta.get("task_name")
    return Recording(
        name=directory.name,
        task_name=str(task_name) if task_name else None,
        started_at=started_at or _timestamp_from_name(directory.name),
        duration_sec=duration_sec,
        metadata=metadata,
    )


def _timestamp_from_name(name: str) -> datetime | None:
    """Fallback start time for recordings whose bag metadata is missing: the directory name."""
    try:
        return datetime.strptime(name[:NAME_TIMESTAMP_LENGTH], NAME_TIMESTAMP_FORMAT)
    except ValueError:
        return None


def _read_duration_and_start(directory: Path) -> tuple[float, datetime | None]:
    """Duration comes from the bag metadata; quality_report.json is the fallback."""
    bag_info = (_read_yaml(directory / BAG_METADATA_FILENAME) or {}).get(
        "rosbag2_bagfile_information"
    )
    if isinstance(bag_info, dict):
        nanoseconds = _nested_number(bag_info, "duration", "nanoseconds")
        started_ns = _nested_number(bag_info, "starting_time", "nanoseconds_since_epoch")
        started_at = (
            datetime.fromtimestamp(started_ns / 1_000_000_000) if started_ns is not None else None
        )
        if nanoseconds is not None:
            return nanoseconds / 1_000_000_000, started_at
    else:
        started_at = None

    report = _read_json(directory / QUALITY_REPORT_FILENAME) or {}
    duration = report.get("duration_sec")
    return (float(duration) if isinstance(duration, int | float) else 0.0), started_at


def _nested_number(source: dict, outer: str, inner: str) -> float | None:
    nested = source.get(outer)
    if isinstance(nested, dict) and isinstance(nested.get(inner), int | float):
        return float(nested[inner])
    return None


def _read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def _read_yaml(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    return loaded if isinstance(loaded, dict) else None
