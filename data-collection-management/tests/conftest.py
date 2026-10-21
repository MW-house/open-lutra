"""Shared fixtures: a temporary recording config plus a temporary output directory."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest
import yaml

RECORDING_CONFIG = {
    "metadata_fields": [
        {
            "key": "object",
            "label": "対象物",
            "type": "select",
            "options": [
                {"value": "A000", "label": "A000_フェイスタオル"},
                {"value": "A001", "label": "A001_バスタオル"},
            ],
        },
        {
            "key": "operator_id",
            "label": "オペレータID",
            "type": "number",
            "pattern": "^[0-9]{3}$",
        },
        {
            "key": "task_evaluation",
            "label": "タスク評価",
            "type": "select",
            "options": [
                {"value": "success", "label": "成功"},
                {"value": "failure", "label": "失敗"},
            ],
        },
    ]
}


@pytest.fixture
def recording_config_path(tmp_path: Path) -> Path:
    path = tmp_path / "simulator.yaml"
    path.write_text(yaml.safe_dump(RECORDING_CONFIG, allow_unicode=True), encoding="utf-8")
    return path


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Three recordings, all on 2026-08-01. Date-range tests add older ones themselves."""
    directory = tmp_path / "output"
    directory.mkdir()
    write_recording(
        directory / "20260801_060659",
        {"object": "A000", "operator_id": "002", "task_evaluation": "success"},
        3661.0,
    )
    write_recording(
        directory / "20260801_060708",
        {"object": "A001", "operator_id": "002", "task_evaluation": "success"},
        30.0,
    )
    write_recording(
        directory / "20260801_060723",
        {"object": "A001", "operator_id": "003", "task_evaluation": "failure"},
        90.5,
    )
    return directory


def write_recording(
    directory: Path,
    metadata: dict[str, str],
    duration_sec: float,
    *,
    task_name: str | None = None,
    use_bag_metadata: bool = True,
) -> Path:
    """Create a recording directory; its start time comes from the directory name."""
    directory.mkdir(parents=True)
    (directory / "recording_meta.json").write_text(
        json.dumps({"task_name": task_name, "tags": [], "metadata": metadata}),
        encoding="utf-8",
    )
    if use_bag_metadata:
        bag_info: dict[str, object] = {
            "duration": {"nanoseconds": int(duration_sec * 1_000_000_000)}
        }
        started_ns = _start_nanoseconds(directory.name)
        if started_ns is not None:
            bag_info["starting_time"] = {"nanoseconds_since_epoch": started_ns}
        (directory / "metadata.yaml").write_text(
            yaml.safe_dump({"rosbag2_bagfile_information": bag_info}), encoding="utf-8"
        )
    else:
        (directory / "quality_report.json").write_text(
            json.dumps({"duration_sec": duration_sec}), encoding="utf-8"
        )
    return directory


def _start_nanoseconds(name: str) -> int | None:
    """Timestamp for directories named "<YYYYmmdd>_<HHMMSS>"; None for any other name."""
    try:
        started_at = datetime.strptime(name, "%Y%m%d_%H%M%S")
    except ValueError:
        return None
    return int(started_at.timestamp() * 1_000_000_000)
