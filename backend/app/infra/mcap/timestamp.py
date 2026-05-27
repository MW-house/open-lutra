"""Timestamp normalization for MCAP messages.

ROS2 messages carry two kinds of timestamps:
  - `header.stamp`: real time stamped by the sensor/driver
  - `log_time` (MCAP): the time the message was written to the MCAP

This project prefers `header.stamp` by default and falls back to `log_time`
when it is invalid (missing / 0) or when the message type has no `header`.
"""

from typing import Any

from app.shared.stamp import extract_stamp_ns, extract_stamp_sec


def resolve_timestamp_sec(decoded: Any, log_time_ns: int) -> float:
    """Prefer header.stamp (seconds); fall back to log_time converted to seconds."""
    stamp_sec = extract_stamp_sec(decoded)
    if stamp_sec is not None and stamp_sec > 0:
        return stamp_sec
    return log_time_ns / 1e9


def resolve_timestamp_ns(decoded: Any, log_time_ns: int) -> int:
    """Prefer header.stamp (nanoseconds); fall back to log_time (ns) as-is."""
    stamp_ns = extract_stamp_ns(decoded)
    if stamp_ns is not None and stamp_ns > 0:
        return stamp_ns
    return log_time_ns
