"""Daily CSV report: success / failure counts and durations per metadata combination.

The grouping columns are not fixed here — they are **every field the recording config
declares**, in declaration order, headed by the field's `key`. Adding a field to
`metadata_fields:` therefore adds a column.

The one field held back is the evaluation axis: it feeds the success / failure pairs
rather than splitting rows, so both land on the same row.

The CSV feeds an existing spreadsheet, so the columns that sheet derives itself
(オペレーター氏名 via VLOOKUP, 1タスクあたり / 合計件数 / 合計時間 via formulas) are
deliberately left out — only the raw aggregates are emitted.
"""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass
from datetime import date

from .aggregate import (
    EVALUATION_FIELD_KEY,
    FAILURE_VALUE,
    SUCCESS_VALUE,
    filter_recordings,
    value_of,
)
from .fields import MetadataField
from .models import UNSET_DISPLAY, UNSET_VALUE
from .scanner import Recording

DATE_HEADER = "日付"
# Trailing metric columns: both pairs are filled from the same row's recordings.
METRIC_HEADERS = ("成功件数", "成功時間", "失敗件数", "失敗時間")


def header_row(fields: list[MetadataField]) -> list[str]:
    """The CSV header: the date, one column per grouping field key, then the metrics."""
    return [DATE_HEADER, *(field.key for field in group_fields(fields)), *METRIC_HEADERS]


def group_fields(fields: list[MetadataField]) -> list[MetadataField]:
    """The fields that become columns: every declared one but the evaluation axis.

    Keeping task_evaluation out is what lets a row carry both metric pairs — grouping by
    it would split every combination into a success row and a failure row.
    """
    return [field for field in fields if field.key != EVALUATION_FIELD_KEY]


def build_daily_csv(
    recordings: list[Recording],
    fields: list[MetadataField],
    target_date: date,
) -> str:
    """One row per combination of grouping field values recorded on `target_date`.

    Only combinations the data actually contains are emitted — unlike the UI tables,
    which pad with the master's zero-count options.
    """
    matched = filter_recordings(recordings, {}, target_date, target_date)
    columns = group_fields(fields)

    tallies: dict[tuple[str, ...], _Tally] = {}
    for recording in matched:
        key = tuple(value_of(recording, field.key) for field in columns)
        tallies.setdefault(key, _Tally()).add(recording)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header_row(fields))
    for key in sorted(tallies):
        tally = tallies[key]
        writer.writerow(
            [
                format_report_date(target_date),
                *(_display(field, value) for field, value in zip(columns, key, strict=True)),
                tally.success_count,
                format_clock(tally.success_sec),
                tally.failure_count,
                format_clock(tally.failure_sec),
            ]
        )
    return buffer.getvalue()


def format_clock(seconds: float) -> str:
    """Format a duration as "H:MM:SS", the form a spreadsheet reads back as a time."""
    # Half-up, matching format_duration: 4.5s reads as 0:00:05, not 0:00:04.
    total = math.floor(max(seconds, 0.0) + 0.5)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def format_report_date(value: date) -> str:
    """Format a date as "2026/8/3" — unpadded, matching the existing sheet."""
    return f"{value.year}/{value.month}/{value.day}"


@dataclass
class _Tally:
    """Running success / failure totals for one grouping combination.

    Both pairs come from the same set of recordings, so one row reports the day's
    successes and failures side by side. Recordings with no task evaluation land in
    neither pair, mirroring how the per-field breakdown counts them (see
    aggregate._field_summary); a master without an evaluation field reports zeros
    across all four columns.
    """

    success_count: int = 0
    success_sec: float = 0.0
    failure_count: int = 0
    failure_sec: float = 0.0

    def add(self, recording: Recording) -> None:
        evaluation = value_of(recording, EVALUATION_FIELD_KEY)
        if evaluation == SUCCESS_VALUE:
            self.success_count += 1
            self.success_sec += recording.duration_sec
        elif evaluation == FAILURE_VALUE:
            self.failure_count += 1
            self.failure_sec += recording.duration_sec


def _display(field: MetadataField, value: str) -> str:
    """Human-readable form: the master's "{id}_{label}", or the raw id when unknown."""
    if value == UNSET_VALUE:
        return UNSET_DISPLAY
    return field.display_for(value)
