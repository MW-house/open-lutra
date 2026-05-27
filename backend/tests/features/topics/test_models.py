"""Tests for the internal domain models used by topic monitoring.

Covers TopicStats properties (actual_hz, loss_rate, continuity_score,
status) and its conversion method (to_api).
"""

from collections import deque
from unittest.mock import patch

import pytest

from app.features.topics.models import GapRecord, TopicStats


def _make_stats_with_cache(now: float = 100.0, **kwargs: object) -> TopicStats:
    """Helper that builds a TopicStats and calls refresh_cache."""
    stats = TopicStats(**kwargs)  # type: ignore[arg-type]
    stats.refresh_cache(now)
    return stats


# ---------------------------------------------------------------------------
# actual_hz
# ---------------------------------------------------------------------------


class TestActualHz:
    """Tests for the actual_hz property."""

    def test_no_timestamps(self) -> None:
        stats = TopicStats(name="/t", msg_type="std_msgs/msg/String")
        stats.refresh_cache(100.0)
        assert stats.actual_hz == 0.0

    def test_single_timestamp(self) -> None:
        stats = TopicStats(name="/t", msg_type="std_msgs/msg/String", timestamps=deque([1.0]))
        stats.refresh_cache(5.0)
        assert stats.actual_hz == 0.0

    def test_regular_10hz(self) -> None:
        """0.1 s interval = 10 Hz."""
        ts = deque([1.0 + i * 0.1 for i in range(20)])
        stats = _make_stats_with_cache(now=ts[-1] + 0.1, name="/t", msg_type="std_msgs/msg/String", timestamps=ts)
        assert stats.actual_hz == pytest.approx(10.0, abs=0.1)

    def test_regular_100hz(self) -> None:
        """0.01 s interval = 100 Hz."""
        ts = deque([1.0 + i * 0.01 for i in range(50)])
        stats = _make_stats_with_cache(now=ts[-1] + 0.01, name="/t", msg_type="std_msgs/msg/String", timestamps=ts)
        assert stats.actual_hz == pytest.approx(100.0, abs=1.0)

    def test_identical_timestamps(self) -> None:
        """When all timestamps are identical, returns 0.0 (avoids division by zero)."""
        ts = deque([1.0, 1.0, 1.0])
        stats = _make_stats_with_cache(now=2.0, name="/t", msg_type="std_msgs/msg/String", timestamps=ts)
        assert stats.actual_hz == 0.0


# ---------------------------------------------------------------------------
# loss_rate
# ---------------------------------------------------------------------------


class TestLossRate:
    """Tests for the loss_rate property."""

    def test_no_baseline(self) -> None:
        """When the baseline Hz is unset, returns 0."""
        stats = TopicStats(name="/t", msg_type="std_msgs/msg/String", message_count=100)
        stats.refresh_cache(200.0)
        assert stats.loss_rate == 0.0

    def test_initial_loss_rate_zero(self) -> None:
        """During the first minute (window not yet established) the rate is 0.0."""
        stats = TopicStats(name="/t", msg_type="std_msgs/msg/String", baseline_hz=10.0)
        stats.refresh_cache(100.0)
        assert stats.loss_rate == 0.0

    def test_perfect_reception_after_window(self) -> None:
        """All expected messages received over one minute -> loss=0%."""
        stats = TopicStats(name="/t", msg_type="std_msgs/msg/String", baseline_hz=10.0)
        for i in range(600):
            stats.tick_loss_window(100.0 + i * 0.1)
        stats.refresh_cache(160.1)
        assert stats.loss_rate == pytest.approx(0.0, abs=0.02)

    def test_half_lost_after_window(self) -> None:
        """Only half of the expected messages received over one minute -> loss=50%."""
        stats = TopicStats(name="/t", msg_type="std_msgs/msg/String", baseline_hz=10.0)
        for i in range(300):
            stats.tick_loss_window(100.0 + i * 0.2)
        stats.refresh_cache(160.1)
        assert stats.loss_rate == pytest.approx(0.5, abs=0.02)

    @patch("app.features.topics.models.time.monotonic", return_value=110.0)
    def test_danger_returns_zero(self, _mock_time: object) -> None:
        """Returns 0.0 in the danger state."""
        stats = TopicStats(
            name="/t",
            msg_type="std_msgs/msg/String",
            baseline_hz=10.0,
            message_count=1,
            _last_msg_time=100.0,
            _gap_threshold_sec=3.0,
            _last_loss_rate=0.3,
        )
        stats.refresh_cache(110.0)
        assert stats.status == "danger"
        assert stats.loss_rate == 0.0


# ---------------------------------------------------------------------------
# continuity_score
# ---------------------------------------------------------------------------


class TestContinuityScore:
    """Tests for the continuity_score property."""

    def test_no_first_received(self) -> None:
        """Returns 1.0 (no issue) when nothing has been received yet."""
        stats = TopicStats(name="/t", msg_type="std_msgs/msg/String")
        assert stats.continuity_score == 1.0

    @patch("app.features.topics.models.time.monotonic", return_value=110.0)
    def test_no_gaps(self, _mock_time: object) -> None:
        """Returns 1.0 when there are no gaps."""
        stats = TopicStats(
            name="/t",
            msg_type="std_msgs/msg/String",
            first_received_at=100.0,
            total_gap_sec=0.0,
        )
        assert stats.continuity_score == 1.0

    @patch("app.features.topics.models.time.monotonic", return_value=110.0)
    def test_with_gaps(self, _mock_time: object) -> None:
        """With a 5 s gap inside the most recent 60 s window: 1 - 5/10 = 0.5."""
        stats = TopicStats(
            name="/t",
            msg_type="std_msgs/msg/String",
            first_received_at=100.0,
            gaps=[GapRecord(timestamp=105.0, duration=5.0)],
        )
        assert stats.continuity_score == pytest.approx(0.5, abs=0.01)

    @patch("app.features.topics.models.time.monotonic", return_value=100.0)
    def test_elapsed_zero(self, _mock_time: object) -> None:
        """When elapsed time is zero, returns 1.0 (avoids division by zero)."""
        stats = TopicStats(
            name="/t",
            msg_type="std_msgs/msg/String",
            first_received_at=100.0,
        )
        assert stats.continuity_score == 1.0


# ---------------------------------------------------------------------------
# last_received_at
# ---------------------------------------------------------------------------


class TestLastReceivedAt:
    """Tests for the last_received_at property."""

    def test_empty(self) -> None:
        stats = TopicStats(name="/t", msg_type="std_msgs/msg/String")
        assert stats.last_received_at is None

    def test_with_last_msg_time(self) -> None:
        stats = TopicStats(name="/t", msg_type="std_msgs/msg/String", _last_msg_time=3.0)
        assert stats.last_received_at == 3.0


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


class TestStatus:
    """Tests for the status property."""

    def test_inactive_no_messages(self) -> None:
        stats = TopicStats(name="/t", msg_type="std_msgs/msg/String")
        stats.refresh_cache(100.0)
        assert stats.status == "inactive"

    def test_ok_recent_message(self) -> None:
        """ok when a message was received recently."""
        stats = TopicStats(
            name="/t",
            msg_type="std_msgs/msg/String",
            message_count=1,
            _last_msg_time=100.0,
            _gap_threshold_sec=3.0,
        )
        stats.refresh_cache(100.5)
        assert stats.status == "ok"

    def test_danger_stale(self) -> None:
        """danger when the threshold (3 s) is exceeded."""
        stats = TopicStats(
            name="/t",
            msg_type="std_msgs/msg/String",
            message_count=1,
            _last_msg_time=100.0,
            _gap_threshold_sec=3.0,
        )
        stats.refresh_cache(110.0)
        assert stats.status == "danger"

    def test_warning_hz_drop(self) -> None:
        """warning when Hz drops below 50% of baseline."""
        ts = deque([99.0, 100.0])
        stats = TopicStats(
            name="/t",
            msg_type="std_msgs/msg/String",
            timestamps=ts,
            message_count=2,
            baseline_hz=10.0,
            _last_msg_time=100.0,
            _gap_threshold_sec=3.0,
        )
        stats.refresh_cache(100.5)
        assert stats.status == "warning"

    def test_inactive_with_count_but_no_last_msg_time(self) -> None:
        """inactive when message_count > 0 but _last_msg_time is 0."""
        stats = TopicStats(
            name="/t",
            msg_type="std_msgs/msg/String",
            message_count=5,
        )
        stats.refresh_cache(100.0)
        assert stats.status == "inactive"


# ---------------------------------------------------------------------------
# to_api
# ---------------------------------------------------------------------------


class TestToApi:
    """Tests for to_api()."""

    def test_returns_topic_info(self) -> None:
        ts = deque([100.0 + i * 0.01 for i in range(50)])
        stats = TopicStats(
            name="/joint_states",
            msg_type="sensor_msgs/msg/JointState",
            timestamps=ts,
            message_count=50,
            is_subscribed=True,
            qos_reliability="RELIABLE",
            _last_msg_time=ts[-1],
            _gap_threshold_sec=3.0,
        )
        stats.refresh_cache(100.5)
        info = stats.to_api()
        assert info.name == "/joint_states"
        assert info.msg_type == "sensor_msgs/msg/JointState"
        assert info.actual_hz > 0
        assert info.is_subscribed is True
        assert info.qos_reliability == "RELIABLE"
        assert info.message_count == 50
