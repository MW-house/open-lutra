from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml

from data_collection_management.csv_report import build_daily_csv, format_clock, format_report_date
from data_collection_management.fields import MetadataField, load_metadata_fields
from data_collection_management.scanner import scan_recordings

from .conftest import write_recording

# Every declared field but task_evaluation becomes a column, so this master defines the
# whole report shape.
REPORT_CONFIG = {
    "metadata_fields": [
        {"key": "operator_id", "label": "オペレーターID", "type": "number"},
        {
            "key": "object",
            "label": "アイテム",
            "type": "select",
            # No label, so the display stays the bare value ("Tシャツ", not "Tシャツ_...").
            "options": [{"value": "Tシャツ"}, {"value": "タオル"}],
        },
        {
            "key": "operation",
            "label": "タスク",
            "type": "select",
            "options": [{"value": "D000", "label": "端から持ち上げて中央に置く"}],
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

HEADER = [
    "日付",
    "operator_id",
    "object",
    "operation",
    "成功件数",
    "成功時間",
    "失敗件数",
    "失敗時間",
]


def _load_fields(tmp_path: Path, config: dict, name: str = "report.yaml") -> list[MetadataField]:
    path = tmp_path / name
    path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")
    return load_metadata_fields(path)


@pytest.fixture
def report_fields(tmp_path: Path) -> list[MetadataField]:
    return _load_fields(tmp_path, REPORT_CONFIG)


@pytest.fixture
def report_output_dir(tmp_path: Path) -> Path:
    """Two successes and a failure for one combination on 2026-08-03, plus a neighbour day."""
    directory = tmp_path / "report_output"
    directory.mkdir()
    for name, evaluation, duration in [
        ("20260803_090000", "success", 5.0),
        ("20260803_091500", "success", 7.0),
        ("20260803_093000", "failure", 15.0),
    ]:
        write_recording(directory / name, _metadata(evaluation), duration)
    write_recording(directory / "20260804_090000", _metadata("success"), 99.0)
    return directory


def _metadata(evaluation: str) -> dict[str, str]:
    return {
        "operator_id": "0005",
        "object": "Tシャツ",
        "operation": "D000",
        "task_evaluation": evaluation,
    }


def _rows(csv_text: str) -> list[list[str]]:
    return [line.split(",") for line in csv_text.strip().split("\r\n")]


def test_build_daily_csv_heads_each_column_with_its_field_key(
    report_output_dir: Path, report_fields: list[MetadataField]
) -> None:
    rows = _rows(
        build_daily_csv(scan_recordings(report_output_dir), report_fields, date(2026, 8, 3))
    )

    assert rows[0] == HEADER


def test_build_daily_csv_keeps_the_evaluation_field_out_of_the_columns(
    report_output_dir: Path, report_fields: list[MetadataField]
) -> None:
    """It drives the metric pairs instead, so it must not split the rows."""
    rows = _rows(
        build_daily_csv(scan_recordings(report_output_dir), report_fields, date(2026, 8, 3))
    )

    assert "task_evaluation" in {field.key for field in report_fields}
    assert "task_evaluation" not in rows[0]


def test_build_daily_csv_reports_one_row_per_combination(
    report_output_dir: Path, report_fields: list[MetadataField]
) -> None:
    rows = _rows(
        build_daily_csv(scan_recordings(report_output_dir), report_fields, date(2026, 8, 3))
    )

    # The day's successes and its failure share one row. The 2026-08-04 recording is
    # out of range, so a single combination remains.
    assert rows[1:] == [
        [
            "2026/8/3",
            "0005",
            "Tシャツ",
            "D000_端から持ち上げて中央に置く",
            "2",
            "0:00:12",
            "1",
            "0:00:15",
        ]
    ]


def test_build_daily_csv_columns_follow_the_master(report_output_dir: Path, tmp_path: Path) -> None:
    """A field added to the master becomes a column, and splits the rows behind it."""
    extended = {"metadata_fields": [*REPORT_CONFIG["metadata_fields"], {"key": "station_id"}]}
    write_recording(
        report_output_dir / "20260803_094500", {**_metadata("success"), "station_id": "S-01"}, 4.0
    )

    rows = _rows(
        build_daily_csv(
            scan_recordings(report_output_dir),
            _load_fields(tmp_path, extended, "extended.yaml"),
            date(2026, 8, 3),
        )
    )

    assert rows[0] == [*HEADER[:4], "station_id", *HEADER[4:]]
    assert [(row[4], row[5], row[7]) for row in rows[1:]] == [
        ("S-01", "1", "0"),
        ("未設定", "2", "1"),
    ]


def test_build_daily_csv_splits_differing_combinations(
    report_output_dir: Path, report_fields: list[MetadataField]
) -> None:
    write_recording(
        report_output_dir / "20260803_094500",
        {**_metadata("success"), "object": "タオル"},
        4.0,
    )

    rows = _rows(
        build_daily_csv(scan_recordings(report_output_dir), report_fields, date(2026, 8, 3))
    )

    assert [(row[2], row[4], row[6]) for row in rows[1:]] == [
        ("Tシャツ", "2", "1"),
        ("タオル", "1", "0"),
    ]


def test_build_daily_csv_marks_missing_values_as_unset(
    tmp_path: Path, report_fields: list[MetadataField]
) -> None:
    directory = tmp_path / "sparse"
    directory.mkdir()
    write_recording(directory / "20260803_090000", {"task_evaluation": "success"}, 3.0)

    rows = _rows(build_daily_csv(scan_recordings(directory), report_fields, date(2026, 8, 3)))

    assert rows[1] == ["2026/8/3", *["未設定"] * 3, "1", "0:00:03", "0", "0:00:00"]


def test_build_daily_csv_leaves_unevaluated_recordings_out_of_both_columns(
    tmp_path: Path, report_fields: list[MetadataField]
) -> None:
    directory = tmp_path / "unevaluated"
    directory.mkdir()
    write_recording(directory / "20260803_090000", {"operator_id": "0005"}, 3.0)

    rows = _rows(build_daily_csv(scan_recordings(directory), report_fields, date(2026, 8, 3)))

    assert rows[1][4:] == ["0", "0:00:00", "0", "0:00:00"]


def test_build_daily_csv_reports_a_master_without_fields(
    report_output_dir: Path, tmp_path: Path
) -> None:
    """No declared field means no grouping column: the whole day collapses into one row."""
    rows = _rows(
        build_daily_csv(
            scan_recordings(report_output_dir),
            _load_fields(tmp_path, {"metadata_fields": []}, "empty.yaml"),
            date(2026, 8, 3),
        )
    )

    assert rows[0] == ["日付", "成功件数", "成功時間", "失敗件数", "失敗時間"]
    assert rows[1] == ["2026/8/3", "2", "0:00:12", "1", "0:00:15"]


def test_build_daily_csv_holds_only_the_header_when_nothing_matches(
    report_output_dir: Path, report_fields: list[MetadataField]
) -> None:
    rows = _rows(
        build_daily_csv(scan_recordings(report_output_dir), report_fields, date(2026, 7, 1))
    )

    assert len(rows) == 1


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [(0.0, "0:00:00"), (4.5, "0:00:05"), (15.0, "0:00:15"), (3842.0, "1:04:02"), (-1.0, "0:00:00")],
)
def test_format_clock(seconds: float, expected: str) -> None:
    assert format_clock(seconds) == expected


def test_format_report_date_is_unpadded() -> None:
    assert format_report_date(date(2026, 8, 3)) == "2026/8/3"
