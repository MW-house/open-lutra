from __future__ import annotations

from datetime import datetime
from pathlib import Path

from data_collection_management.scanner import scan_recordings

from .conftest import write_recording


def test_scans_recordings_newest_first(output_dir: Path) -> None:
    recordings = scan_recordings(output_dir)

    assert [item.name for item in recordings] == [
        "20260801_060723",
        "20260801_060708",
        "20260801_060659",
    ]
    assert recordings[-1].metadata == {
        "object": "A000",
        "operator_id": "002",
        "task_evaluation": "success",
    }
    assert recordings[-1].duration_sec == 3661.0
    assert recordings[-1].started_at is not None


def test_falls_back_to_quality_report_duration(tmp_path: Path) -> None:
    directory = tmp_path / "output"
    directory.mkdir()
    write_recording(directory / "rec", {"object": "A000"}, 12.5, use_bag_metadata=False)

    recording = scan_recordings(directory)[0]

    assert recording.duration_sec == 12.5
    assert recording.started_at is None


def test_skips_directories_without_meta_and_reserved_ones(tmp_path: Path) -> None:
    directory = tmp_path / "output"
    directory.mkdir()
    (directory / "not_a_recording").mkdir()
    write_recording(directory / "_lerobot_exports", {"object": "A000"}, 5.0)
    write_recording(directory / "rec", {"object": "A000"}, 5.0)

    assert [item.name for item in scan_recordings(directory)] == ["rec"]


def test_missing_output_dir_yields_no_recordings(tmp_path: Path) -> None:
    assert scan_recordings(tmp_path / "absent") == []


def test_tolerates_broken_files(tmp_path: Path) -> None:
    directory = tmp_path / "output"
    (directory / "rec").mkdir(parents=True)
    (directory / "rec" / "recording_meta.json").write_text("{ broken", encoding="utf-8")
    (directory / "rec" / "metadata.yaml").write_text("key: [1, 2\nbroken: {", encoding="utf-8")

    recording = scan_recordings(directory)[0]

    assert recording.metadata == {}
    assert recording.duration_sec == 0.0


def test_bag_metadata_without_duration_falls_back(tmp_path: Path) -> None:
    directory = tmp_path / "output"
    recording_dir = write_recording(
        directory / "rec", {"object": "A000"}, 7.0, use_bag_metadata=False
    )
    (recording_dir / "metadata.yaml").write_text(
        "rosbag2_bagfile_information:\n  version: 5\n", encoding="utf-8"
    )

    recording = scan_recordings(directory)[0]

    assert recording.duration_sec == 7.0
    assert recording.started_at is None


def test_start_time_falls_back_to_the_directory_name(tmp_path: Path) -> None:
    directory = tmp_path / "output"
    directory.mkdir()
    write_recording(directory / "20260725_100000", {"object": "A000"}, 5.0, use_bag_metadata=False)

    recording = scan_recordings(directory)[0]

    assert recording.started_at == datetime(2026, 7, 25, 10, 0, 0)


def test_meta_without_metadata_mapping_is_empty(tmp_path: Path) -> None:
    directory = tmp_path / "output"
    (directory / "rec").mkdir(parents=True)
    (directory / "rec" / "recording_meta.json").write_text(
        '{"task_name": "folding", "metadata": null}', encoding="utf-8"
    )

    recording = scan_recordings(directory)[0]

    assert recording.task_name == "folding"
    assert recording.metadata == {}
