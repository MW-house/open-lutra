"""Shared fixtures for validation tests.

- Clears the custom validator registry before and after each test.
- Provides helpers for building minimal QualityReport / ValidationContext
  / TopicQuality objects.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest

from app.features.analysis.models import MessageSizeStats, QualityReport, TopicQuality
from app.features.recordings.meta import RecordingMeta
from app.features.validation.context import ValidationContext
from app.features.validation.registry import clear_registry


@pytest.fixture(autouse=True)
def _clear_validator_registry() -> Iterator[None]:
    """Clear the custom validator registry before/after each test.

    The registry is module-global state, so without isolation one
    test's registrations leak into the next.
    """
    clear_registry()
    yield
    clear_registry()


def make_topic(name: str, msg_count: int = 100) -> TopicQuality:
    """Build a minimal TopicQuality for tests."""
    return TopicQuality(
        name=name,
        msg_type="test_msgs/Test",
        message_count=msg_count,
        actual_frequency_hz=30.0,
        expected_frequency_hz=30.0,
        loss_rate=0.0,
        frequency_std_hz=0.0,
        data_continuity_score=1.0,
        gap_count=0,
        gaps=[],
        loss_events=[],
        loss_count=0,
        minor_loss_count=0,
        major_loss_count=0,
        timestamp_source="log_time",
        avg_message_size_bytes=100,
        size_stats=MessageSizeStats.empty(),
        start_delay_sec=0.0,
        end_early_sec=0.0,
        status="ok",
    )


def make_report(
    *,
    topics: list[TopicQuality] | None = None,
    duration_sec: float = 60.0,
    file_size_bytes: int = 1024,
) -> QualityReport:
    """Build a minimal QualityReport for tests."""
    topics = topics or []
    return QualityReport(
        duration_sec=duration_sec,
        total_messages=sum(t.message_count for t in topics),
        total_topics=len(topics),
        file_size_bytes=file_size_bytes,
        topics=topics,
    )


def make_ctx(
    *,
    topics: list[TopicQuality] | None = None,
    duration_sec: float = 60.0,
    file_size_bytes: int = 1024,
    recording_dir: Path | None = None,
    mcap_path: Path | None = None,
    recording_meta: RecordingMeta | None = None,
    report: QualityReport | None = None,
) -> ValidationContext:
    """Build a minimal ValidationContext for tests.

    If `report` is provided it is used as-is; otherwise a report is built
    from the `topics` / `duration_sec` / `file_size_bytes` kwargs.
    """
    if report is None:
        report = make_report(
            topics=topics,
            duration_sec=duration_sec,
            file_size_bytes=file_size_bytes,
        )
    return ValidationContext(
        report=report,
        recording_dir=recording_dir or Path("/tmp/recording"),
        mcap_path=mcap_path,
        recording_meta=recording_meta,
    )
