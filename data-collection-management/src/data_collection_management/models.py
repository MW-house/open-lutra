"""API response models."""

from __future__ import annotations

from pydantic import BaseModel

# Filter/group value standing in for "the recording has no value for this field".
UNSET_VALUE = "__unset__"
UNSET_DISPLAY = "未設定"


class FieldOptionOut(BaseModel):
    value: str
    display: str


class FieldOut(BaseModel):
    key: str
    label: str
    type: str
    options: list[FieldOptionOut]


class GroupOut(BaseModel):
    value: str
    display: str
    count: int
    duration_sec: float
    duration_text: str
    success_count: int
    failure_count: int
    # Share of the group's evaluated recordings that succeeded (0-1); null when none
    # of them carry an evaluation.
    success_rate: float | None


class FieldSummaryOut(BaseModel):
    key: str
    label: str
    groups: list[GroupOut]


class EvaluationTotalOut(BaseModel):
    """Headline total for one task evaluation (success / failure)."""

    value: str
    display: str
    count: int
    duration_sec: float
    duration_text: str


class RecordingOut(BaseModel):
    name: str
    task_name: str | None
    started_at: str | None
    recorded_date: str | None
    duration_sec: float
    duration_text: str
    metadata: dict[str, str]


class SummaryOut(BaseModel):
    aggregated_at: str
    output_dir: str
    recording_config_path: str
    date_from: str | None
    date_to: str | None
    total_count: int
    total_duration_sec: float
    total_duration_text: str
    # Headline totals split by task evaluation; empty when the master has no such field.
    evaluation_totals: list[EvaluationTotalOut]
    # Field master (every selectable value) — drives the filter controls.
    fields: list[FieldOut]
    # Per-field breakdown of the recordings matching the current filters.
    field_summaries: list[FieldSummaryOut]
    recordings: list[RecordingOut]
