"""Internal domain models for topic monitoring.

Mutable value objects that are updated from rclpy callbacks. Kept separate
from the Pydantic schemas used for API responses (schemas.py).

See docs/domain/quality_analysis.md for the quality metric definitions.
"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from app.features.topics.schemas import TopicInfo

# Time window for computing actual_hz (seconds).
_HZ_WINDOW_SEC = 3.0

# Cache refresh interval for actual_hz (seconds).
_HZ_CACHE_INTERVAL_SEC = 0.5

# Sliding window for gap tracking (seconds).
_QUALITY_WINDOW_SEC = 10.0

# Window for computing loss_rate (seconds).
_LOSS_RATE_WINDOW_SEC = 5.0


@dataclass
class GapRecord:
    """A record of a detected gap."""

    timestamp: float  # monotonic time
    duration: float  # seconds


@dataclass
class TopicStats:
    """Statistics for a single topic.

    When baseline_fixed is True, runs in a lightweight counter-based mode
    that skips the timestamp deque bookkeeping.
    """

    name: str
    msg_type: str
    timestamps: deque[float] = field(default_factory=lambda: deque(maxlen=200))
    message_count: int = 0
    is_subscribed: bool = False
    baseline_hz: float | None = None
    baseline_fixed: bool = False  # True: from YAML config, False: dynamically learned
    latest_message: dict[str, Any] | None = None
    # Quality metric fields
    first_received_at: float | None = None
    total_gap_sec: float = 0.0
    gaps: list[GapRecord] = field(default_factory=list)
    # Window counter for loss_rate computation (monotonic)
    _window_start: float = field(default=0.0, repr=False)
    _window_count: int = field(default=0, repr=False)
    _last_loss_rate: float = field(default=0.0, repr=False)
    _last_drop_count: int = field(default=0, repr=False)
    # Stamp-based loss count (counts lost messages exactly from header.stamp intervals)
    _last_stamp: float = field(default=0.0, repr=False)
    _stamp_window_start: float = field(default=0.0, repr=False)
    _stamp_loss_count: int = field(default=0, repr=False)
    _stamp_msg_count: int = field(default=0, repr=False)
    # Enable flag for stamp-based quality computation (controlled by stamp_quality in config/YAML)
    stamp_quality: bool = field(default=False, repr=False)
    # QoS info
    qos_reliability: str = "BEST_EFFORT"

    # Thresholds set by TopicMonitorService.__init__
    _gap_threshold_sec: float = field(default=3.0, repr=False)
    _hz_drop_threshold: float = field(default=0.5, repr=False)

    # Counter-based Hz computation (used when baseline is fixed)
    _hz_count: int = field(default=0, repr=False)
    _hz_count_start: float = field(default=0.0, repr=False)
    # Last received time (used for gap detection across all modes)
    _last_msg_time: float = field(default=0.0, repr=False)
    # On-demand message capture (flag is raised on API request; the next received message is converted)
    _capture_next: bool = field(default=False, repr=False)
    # For continuous image MJPEG streaming / sensor SSE streaming
    _live_mode: bool = field(default=False, repr=False)
    _live_raw_image: bytes = field(default=b"", repr=False)
    # Live mode: sensor data (position array + joint names)
    _live_positions: list[float] = field(default_factory=list, repr=False)
    _live_joint_names: list[str] = field(default_factory=list, repr=False)

    # actual_hz cache (shared across all modes)
    _cached_actual_hz: float = field(default=0.0, repr=False)
    _cached_at: float = field(default=0.0, repr=False)
    # status cache (avoids being recomputed multiple times inside to_api)
    _cached_status: str = field(default="inactive", repr=False)

    def on_stamp(self, now: float, stamp: float | None) -> None:
        """Update quality metrics on message receipt.

        Args:
            now: value of time.monotonic(). Used for counter-based Hz computation.
            stamp: header.stamp (seconds). Used for loss detection and dynamic
                   baseline learning. When None, falls back to ``now``.

        The _last_msg_time used for gap detection is set directly with the
        monotonic value in service.py.
        """
        # Counter-based Hz computation (for fixed baselines): always use monotonic.
        self._hz_count += 1
        if self._hz_count_start == 0.0:
            self._hz_count_start = now

        # Stamp-based loss detection: count lost messages precisely from stamp intervals.
        # Intervals below 1.5x the expected one are treated as jitter (avoids rounding error).
        if stamp is not None and self.baseline_hz and self.baseline_hz > 0:
            if self._stamp_window_start == 0.0:
                self._stamp_window_start = now
            self._stamp_msg_count += 1
            if self._last_stamp > 0:
                interval = stamp - self._last_stamp
                expected_interval = 1.0 / self.baseline_hz
                if interval > expected_interval * 1.5:
                    lost = max(0, round(interval / expected_interval) - 1)
                    self._stamp_loss_count += lost
            self._last_stamp = stamp

        # Dynamic learning: when a stamp is available, push it into the deque so
        # that frequency estimation is unaffected by jitter.
        if not self.baseline_fixed:
            self.timestamps.append(stamp if stamp is not None else now)

    def refresh_cache(self, now: float) -> None:
        """Refresh the actual_hz / loss_rate / status caches (call once per SSE tick)."""
        self._cached_actual_hz = self._compute_actual_hz(now)
        self._cached_at = now
        self._cached_status = self._compute_status(now)
        if self._cached_status == "danger":
            self._last_loss_rate = 0.0
            self._last_drop_count = 0
        else:
            self._compute_loss_rate(now)

    @property
    def actual_hz(self) -> float:
        """Return the cached actual_hz."""
        return self._cached_actual_hz

    def tick_loss_window(self, now: float) -> None:
        """Update the counter used to compute loss_rate.

        Called from on_message for every message. Only increments the counter;
        the actual loss_rate is computed during refresh_cache.
        """
        self._window_count += 1
        if self._window_start == 0.0:
            self._window_start = now

    @property
    def loss_rate(self) -> float:
        """Return the cached loss rate."""
        return self._last_loss_rate

    def recent_gaps(self, window_sec: float = _QUALITY_WINDOW_SEC) -> list[GapRecord]:
        """Return gap records from the last ``window_sec`` seconds."""
        cutoff = time.monotonic() - window_sec
        return [g for g in self.gaps if g.timestamp > cutoff]

    @property
    def continuity_score(self) -> float:
        """Data continuity score (last 10 seconds; 1.0 = no gaps)."""
        if self.first_received_at is None:
            return 1.0
        elapsed = min(time.monotonic() - self.first_received_at, _QUALITY_WINDOW_SEC)
        if elapsed <= 0:
            return 1.0
        windowed_gap_sec = sum(g.duration for g in self.recent_gaps())
        return max(0.0, 1.0 - (windowed_gap_sec / elapsed))

    @property
    def last_received_at(self) -> float | None:
        """Return the time at which the most recent message was received."""
        return self._last_msg_time if self._last_msg_time > 0 else None

    @property
    def status(self) -> str:
        """Return the cached status."""
        return self._cached_status

    def to_api(self) -> TopicInfo:
        """Convert to the Pydantic model used for API responses."""
        return TopicInfo(
            name=self.name,
            msg_type=self.msg_type,
            actual_hz=round(self._cached_actual_hz, 1),
            status=self._cached_status,
            last_received_at=self._cached_at if self.message_count > 0 else None,
            message_count=self.message_count,
            is_subscribed=self.is_subscribed,
            baseline_hz=round(self.baseline_hz, 1) if self.baseline_hz else None,
            baseline_fixed=self.baseline_fixed,
            loss_rate=round(self.loss_rate, 4),
            drop_count=self._last_drop_count,
            continuity_score=round(self.continuity_score, 3),
            qos_reliability=self.qos_reliability,
        )

    def _compute_actual_hz(self, now: float) -> float:
        """Compute actual_hz."""
        if self.baseline_fixed:
            return self._compute_hz_from_counter(now)
        return self._compute_hz_from_timestamps()

    def _compute_hz_from_counter(self, now: float) -> float:
        """Counter-based Hz computation (used with fixed baselines; O(1))."""
        if self._hz_count_start == 0.0:
            return 0.0
        elapsed = now - self._hz_count_start
        if elapsed < 0.5:
            return 0.0  # Need at least 0.5 seconds of data
        hz = self._hz_count / elapsed
        # Reset the counter once the window is exceeded
        if elapsed > _HZ_WINDOW_SEC:
            self._hz_count = 0
            self._hz_count_start = now
        return hz

    def _compute_hz_from_timestamps(self) -> float:
        """Timestamp-based Hz computation (used for dynamic learning)."""
        if len(self.timestamps) < 2:
            return 0.0
        now = self.timestamps[-1]
        cutoff = now - _HZ_WINDOW_SEC
        # Scan the deque from the tail backwards, counting entries newer than the cutoff.
        count = 0
        first_t = now
        for t in reversed(self.timestamps):
            if t <= cutoff:
                break
            first_t = t
            count += 1
        if count < 2:
            return 0.0
        elapsed = now - first_t
        if elapsed <= 0:
            return 0.0
        return (count - 1) / elapsed

    def _compute_loss_rate(self, now: float) -> None:
        """Compute loss rate and drop count.

        stamp_quality=True (real-robot mode): accumulates loss precisely from
        header.stamp intervals.
        stamp_quality=False (simulator mode): count-based (received vs.
        expected).
        """
        if self.baseline_hz is None or self.baseline_hz <= 0:
            self._last_loss_rate = 0.0
            self._last_drop_count = 0
            return

        # Stamp-based (when stamp_quality=True and stamp data is available)
        if self.stamp_quality:
            stamp_elapsed = now - self._stamp_window_start if self._stamp_window_start > 0 else 0.0
            if self._stamp_msg_count > 0 and stamp_elapsed >= 1.0:
                total = self._stamp_msg_count + self._stamp_loss_count
                self._last_loss_rate = self._stamp_loss_count / total if total > 0 else 0.0
                self._last_drop_count = round(self._stamp_loss_count / stamp_elapsed) if stamp_elapsed > 0 else 0
                if stamp_elapsed >= _LOSS_RATE_WINDOW_SEC:
                    self._stamp_window_start = now
                    self._stamp_loss_count = 0
                    self._stamp_msg_count = 0
                return

        # Count-based (default)
        if self._window_start == 0.0:
            self._last_loss_rate = 0.0
            self._last_drop_count = 0
            return
        elapsed = now - self._window_start
        if elapsed < 1.0:
            self._last_loss_rate = 0.0
            self._last_drop_count = 0
            return
        expected = self.baseline_hz * elapsed
        self._last_loss_rate = max(0.0, 1.0 - (self._window_count / expected))
        total_drops = max(0.0, expected - self._window_count)
        self._last_drop_count = round(total_drops / elapsed)
        if elapsed >= _LOSS_RATE_WINDOW_SEC:
            self._window_start = now
            self._window_count = 0

    def _compute_status(self, now: float) -> str:
        """Determine the topic's health status."""
        if self.message_count == 0:
            return "inactive"
        if self._last_msg_time == 0.0:
            return "inactive"

        elapsed = now - self._last_msg_time
        if elapsed > self._gap_threshold_sec:
            return "danger"

        if (
            self.baseline_hz is not None
            and self.baseline_hz > 0
            and self._cached_actual_hz < self.baseline_hz * self._hz_drop_threshold
        ):
            return "warning"

        return "ok"
