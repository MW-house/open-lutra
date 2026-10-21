from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml

from data_collection_management.aggregate import build_summary, filter_recordings, format_duration
from data_collection_management.fields import load_metadata_fields
from data_collection_management.models import UNSET_DISPLAY, UNSET_VALUE
from data_collection_management.scanner import scan_recordings

from .conftest import write_recording


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0, "0秒"),
        (5.71, "6秒"),
        (90.5, "1分31秒"),
        (3661, "1時間01分01秒"),
        (-5, "0秒"),
    ],
)
def test_format_duration(seconds: float, expected: str) -> None:
    assert format_duration(seconds) == expected


def summarize(
    output_dir: Path,
    recording_config_path: Path,
    filters: dict[str, str] | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    return build_summary(
        recordings=scan_recordings(output_dir),
        fields=load_metadata_fields(recording_config_path),
        filters=filters or {},
        output_dir=str(output_dir),
        recording_config_path=str(recording_config_path),
        date_from=date_from,
        date_to=date_to,
    )


def groups_of(summary, key: str) -> dict[str, tuple[int, str]]:
    field = next(item for item in summary.field_summaries if item.key == key)
    return {group.display: (group.count, group.duration_text) for group in field.groups}


def test_totals_cover_every_recording(output_dir: Path, recording_config_path: Path) -> None:
    summary = summarize(output_dir, recording_config_path)

    assert summary.total_count == 3
    assert summary.total_duration_sec == 3781.5
    assert summary.total_duration_text == "1時間03分02秒"


def test_groups_by_master_option_including_zero_counts(
    output_dir: Path, recording_config_path: Path
) -> None:
    summary = summarize(output_dir, recording_config_path)

    assert groups_of(summary, "object") == {
        "A000_フェイスタオル": (1, "1時間01分01秒"),
        "A001_バスタオル": (2, "2分01秒"),
    }
    # A free-input field has no master options, so its groups come from the data.
    assert groups_of(summary, "operator_id") == {"002": (2, "1時間01分31秒"), "003": (1, "1分31秒")}


def test_filter_narrows_counts_and_recordings(
    output_dir: Path, recording_config_path: Path
) -> None:
    summary = summarize(output_dir, recording_config_path, {"object": "A001"})

    assert summary.total_count == 2
    assert summary.total_duration_text == "2分01秒"
    assert groups_of(summary, "object")["A000_フェイスタオル"] == (0, "0秒")
    assert [item.name for item in summary.recordings] == ["20260801_060723", "20260801_060708"]


def test_filters_combine(output_dir: Path, recording_config_path: Path) -> None:
    summary = summarize(output_dir, recording_config_path, {"object": "A001", "operator_id": "003"})

    assert summary.total_count == 1


def test_empty_filter_value_is_ignored(output_dir: Path, recording_config_path: Path) -> None:
    summary = summarize(output_dir, recording_config_path, {"object": ""})

    assert summary.total_count == 3


def test_unset_and_unknown_values_are_reported(
    output_dir: Path, recording_config_path: Path
) -> None:
    write_recording(output_dir / "20260801_070000", {"object": "A999"}, 10.0)
    summary = summarize(output_dir, recording_config_path)

    object_groups = groups_of(summary, "object")
    assert object_groups["A999"] == (1, "10秒")
    assert groups_of(summary, "operator_id")[UNSET_DISPLAY] == (1, "10秒")

    operator_field = next(item for item in summary.fields if item.key == "operator_id")
    assert operator_field.options[-1].value == UNSET_VALUE


def test_unset_is_filterable(output_dir: Path, recording_config_path: Path) -> None:
    write_recording(output_dir / "20260801_070000", {"object": "A999"}, 10.0)
    summary = summarize(output_dir, recording_config_path, {"operator_id": UNSET_VALUE})

    assert [item.name for item in summary.recordings] == ["20260801_070000"]


def test_filter_recordings_returns_all_when_no_filter(output_dir: Path) -> None:
    recordings = scan_recordings(output_dir)

    assert filter_recordings(recordings, {}) == recordings


def rates_of(summary, key: str) -> dict[str, tuple[int, int, float | None]]:
    field = next(item for item in summary.field_summaries if item.key == key)
    return {
        group.display: (group.success_count, group.failure_count, group.success_rate)
        for group in field.groups
    }


def test_groups_report_success_failure_and_rate(
    output_dir: Path, recording_config_path: Path
) -> None:
    summary = summarize(output_dir, recording_config_path)

    assert rates_of(summary, "operator_id") == {"002": (2, 0, 1.0), "003": (0, 1, 0.0)}


def test_success_rate_ignores_unevaluated_recordings(
    output_dir: Path, recording_config_path: Path
) -> None:
    write_recording(output_dir / "20260801_070000", {"operator_id": "002", "object": "A001"}, 10.0)
    summary = summarize(output_dir, recording_config_path)

    # The third 002 recording carries no evaluation: counted in 件数, not in the rate.
    assert rates_of(summary, "operator_id")["002"] == (2, 0, 1.0)
    assert groups_of(summary, "operator_id")["002"] == (3, "1時間01分41秒")


def test_success_rate_is_null_when_nothing_is_evaluated(
    tmp_path: Path, recording_config_path: Path
) -> None:
    directory = tmp_path / "unevaluated"
    directory.mkdir()
    write_recording(directory / "20260801_060659", {"operator_id": "009"}, 10.0)

    assert rates_of(summarize(directory, recording_config_path), "operator_id") == {
        "009": (0, 0, None)
    }


def test_partially_evaluated_group_reports_a_fraction(
    output_dir: Path, recording_config_path: Path
) -> None:
    write_recording(
        output_dir / "20260801_070000",
        {"operator_id": "003", "task_evaluation": "success"},
        10.0,
    )
    summary = summarize(output_dir, recording_config_path)

    assert rates_of(summary, "operator_id")["003"] == (1, 1, 0.5)


def test_evaluation_totals_split_success_and_failure(
    output_dir: Path, recording_config_path: Path
) -> None:
    summary = summarize(output_dir, recording_config_path)

    assert [
        (item.display, item.count, item.duration_text) for item in summary.evaluation_totals
    ] == [
        ("success_成功", 2, "1時間01分31秒"),
        ("failure_失敗", 1, "1分31秒"),
    ]


def test_evaluation_totals_follow_the_filters(
    output_dir: Path, recording_config_path: Path
) -> None:
    summary = summarize(output_dir, recording_config_path, {"operator_id": "003"})

    assert {item.value: item.count for item in summary.evaluation_totals} == {
        "success": 0,
        "failure": 1,
    }


def test_evaluation_totals_are_empty_without_the_field(tmp_path: Path, output_dir: Path) -> None:
    config_path = tmp_path / "no_evaluation.yaml"
    config_path.write_text(
        yaml.safe_dump({"metadata_fields": [{"key": "object", "label": "対象物"}]}),
        encoding="utf-8",
    )

    assert summarize(output_dir, config_path).evaluation_totals == []


def test_date_range_narrows_the_aggregation(output_dir: Path, recording_config_path: Path) -> None:
    write_recording(output_dir / "20260725_100000", {"object": "A001"}, 10.0)

    summary = summarize(
        output_dir, recording_config_path, date_from=date(2026, 8, 1), date_to=date(2026, 8, 1)
    )

    assert summary.total_count == 3
    assert summary.date_from == "2026-08-01"
    assert summary.date_to == "2026-08-01"
    assert all(item.recorded_date == "2026-08-01" for item in summary.recordings)


def test_date_range_bounds_are_inclusive(output_dir: Path, recording_config_path: Path) -> None:
    write_recording(output_dir / "20260725_100000", {"object": "A001"}, 10.0)

    summary = summarize(
        output_dir, recording_config_path, date_from=date(2026, 7, 25), date_to=date(2026, 8, 1)
    )

    assert summary.total_count == 4


def test_open_ended_range_is_allowed(output_dir: Path, recording_config_path: Path) -> None:
    write_recording(output_dir / "20260725_100000", {"object": "A001"}, 10.0)

    assert summarize(output_dir, recording_config_path, date_to=date(2026, 7, 31)).total_count == 1
    assert (
        summarize(output_dir, recording_config_path, date_from=date(2026, 7, 26)).total_count == 3
    )


def test_date_range_excludes_recordings_without_a_date(
    output_dir: Path, recording_config_path: Path
) -> None:
    write_recording(output_dir / "undated", {"object": "A001"}, 10.0)

    assert summarize(output_dir, recording_config_path).total_count == 4
    assert summarize(output_dir, recording_config_path, date_from=date(2026, 1, 1)).total_count == 3


def test_date_range_combines_with_metadata_filters(
    output_dir: Path, recording_config_path: Path
) -> None:
    summary = summarize(
        output_dir,
        recording_config_path,
        {"object": "A001"},
        date_from=date(2026, 8, 1),
        date_to=date(2026, 8, 1),
    )

    assert summary.total_count == 2
