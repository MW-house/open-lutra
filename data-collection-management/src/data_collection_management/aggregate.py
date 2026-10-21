"""Filtering and aggregation: how many recordings, and how long, per metadata value."""

from __future__ import annotations

import math
from datetime import date, datetime

from .fields import MetadataField
from .models import (
    UNSET_DISPLAY,
    UNSET_VALUE,
    EvaluationTotalOut,
    FieldOptionOut,
    FieldOut,
    FieldSummaryOut,
    GroupOut,
    RecordingOut,
    SummaryOut,
)
from .scanner import Recording

# The field whose values drive the headline success / failure totals. Keyed by name
# because "task evaluation" is a post-recording judgement, not just another facet.
EVALUATION_FIELD_KEY = "task_evaluation"
SUCCESS_VALUE = "success"
FAILURE_VALUE = "failure"


def format_duration(seconds: float) -> str:
    """Format a duration as "H時間MM分SS秒", dropping empty leading units."""
    # Half-up, so a total of 120.5s reads as 2分01秒 (round() would bank it down to 120).
    total = math.floor(max(seconds, 0.0) + 0.5)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}時間{minutes:02d}分{secs:02d}秒"
    if minutes:
        return f"{minutes}分{secs:02d}秒"
    return f"{secs}秒"


def filter_recordings(
    recordings: list[Recording],
    filters: dict[str, str],
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[Recording]:
    """Keep recordings matching every active filter (empty value = no filter on that field).

    The date range is inclusive on both ends and compares against the recording's start
    date. A recording with no known start date is excluded once a range is given.
    """
    active = {key: value for key, value in filters.items() if value}
    return [
        recording
        for recording in recordings
        if _in_date_range(recording, date_from, date_to)
        and all(value_of(recording, key) == value for key, value in active.items())
    ]


def build_summary(
    recordings: list[Recording],
    fields: list[MetadataField],
    filters: dict[str, str],
    output_dir: str,
    recording_config_path: str,
    date_from: date | None = None,
    date_to: date | None = None,
) -> SummaryOut:
    """Aggregate the recordings that match the filters, keeping the full master for the UI."""
    matched = filter_recordings(recordings, filters, date_from, date_to)
    return SummaryOut(
        aggregated_at=datetime.now().isoformat(timespec="seconds"),
        output_dir=output_dir,
        recording_config_path=recording_config_path,
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None,
        total_count=len(matched),
        total_duration_sec=round(sum(item.duration_sec for item in matched), 3),
        total_duration_text=format_duration(sum(item.duration_sec for item in matched)),
        evaluation_totals=_evaluation_totals(fields, matched),
        fields=[_field_out(field, recordings) for field in fields],
        field_summaries=[_field_summary(field, matched) for field in fields],
        recordings=[_recording_out(item) for item in matched],
    )


def _in_date_range(recording: Recording, date_from: date | None, date_to: date | None) -> bool:
    if date_from is None and date_to is None:
        return True
    if recording.started_at is None:
        return False
    recorded = recording.started_at.date()
    return not (
        (date_from is not None and recorded < date_from)
        or (date_to is not None and recorded > date_to)
    )


def _evaluation_totals(
    fields: list[MetadataField], recordings: list[Recording]
) -> list[EvaluationTotalOut]:
    """Headline totals per evaluation value, reusing that field's own breakdown."""
    field = next((item for item in fields if item.key == EVALUATION_FIELD_KEY), None)
    if field is None:
        return []

    return [
        EvaluationTotalOut(
            value=group.value,
            display=group.display,
            count=group.count,
            duration_sec=group.duration_sec,
            duration_text=group.duration_text,
        )
        for group in _field_summary(field, recordings).groups
    ]


def _field_out(field: MetadataField, recordings: list[Recording]) -> FieldOut:
    """Selectable values: the master options, plus anything else the data actually contains."""
    options = [
        FieldOptionOut(value=option.value, display=option.display) for option in field.options
    ]
    known = {option.value for option in field.options}
    for value in _extra_values(field, recordings, known):
        options.append(FieldOptionOut(value=value, display=field.display_for(value)))
    if any(value_of(recording, field.key) == UNSET_VALUE for recording in recordings):
        options.append(FieldOptionOut(value=UNSET_VALUE, display=UNSET_DISPLAY))
    return FieldOut(key=field.key, label=field.label, type=field.type, options=options)


def _field_summary(field: MetadataField, recordings: list[Recording]) -> FieldSummaryOut:
    counts: dict[str, int] = {}
    durations: dict[str, float] = {}
    successes: dict[str, int] = {}
    failures: dict[str, int] = {}
    for recording in recordings:
        value = value_of(recording, field.key)
        counts[value] = counts.get(value, 0) + 1
        durations[value] = durations.get(value, 0.0) + recording.duration_sec
        evaluation = value_of(recording, EVALUATION_FIELD_KEY)
        if evaluation == SUCCESS_VALUE:
            successes[value] = successes.get(value, 0) + 1
        elif evaluation == FAILURE_VALUE:
            failures[value] = failures.get(value, 0) + 1

    # Master options first (zero-count rows included, so collection gaps stay visible),
    # then values present in the data but absent from the master.
    known = {option.value for option in field.options}
    values = [option.value for option in field.options]
    values += sorted(value for value in counts if value not in known and value != UNSET_VALUE)
    if UNSET_VALUE in counts:
        values.append(UNSET_VALUE)

    return FieldSummaryOut(
        key=field.key,
        label=field.label,
        groups=[
            GroupOut(
                value=value,
                display=UNSET_DISPLAY if value == UNSET_VALUE else field.display_for(value),
                count=counts.get(value, 0),
                duration_sec=round(durations.get(value, 0.0), 3),
                duration_text=format_duration(durations.get(value, 0.0)),
                success_count=successes.get(value, 0),
                failure_count=failures.get(value, 0),
                success_rate=_success_rate(successes.get(value, 0), failures.get(value, 0)),
            )
            for value in values
        ],
    )


def _success_rate(successes: int, failures: int) -> float | None:
    """Share of evaluated recordings that succeeded; None when none were evaluated.

    Recordings with no evaluation are left out of the denominator so an unlabelled
    take does not read as a failure.
    """
    evaluated = successes + failures
    return round(successes / evaluated, 4) if evaluated else None


def _recording_out(recording: Recording) -> RecordingOut:
    return RecordingOut(
        name=recording.name,
        task_name=recording.task_name,
        started_at=recording.started_at.isoformat(timespec="seconds")
        if recording.started_at
        else None,
        recorded_date=recording.started_at.date().isoformat() if recording.started_at else None,
        duration_sec=round(recording.duration_sec, 3),
        duration_text=format_duration(recording.duration_sec),
        metadata=recording.metadata,
    )


def _extra_values(field: MetadataField, recordings: list[Recording], known: set[str]) -> list[str]:
    return sorted(
        {
            value
            for recording in recordings
            if (value := value_of(recording, field.key)) not in known and value != UNSET_VALUE
        }
    )


def value_of(recording: Recording, key: str) -> str:
    """The recording's value for a field, or UNSET_VALUE when it carries none."""
    return recording.metadata.get(key) or UNSET_VALUE
