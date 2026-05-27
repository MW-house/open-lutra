"""Utilities for extracting header.stamp from ROS2 messages.

header.stamp represents the sensor sampling time and does not include DDS
delivery delay or OS scheduling jitter. Quality analysis, MP4 generation, and
live monitoring prefer header.stamp, falling back to log_time for message types
without a header.

Background: .local/LOG_TO_STAMP.md
"""

from typing import Any


def extract_stamp_sec(decoded: Any) -> float | None:
    """Return header.stamp from a decoded message in seconds.

    Converts a ROS2 message's header.stamp (builtin_interfaces/msg/Time) to a
    float number of seconds. Returns None if the header is missing. Supports
    both rclpy-deserialized messages and mcap-ros2-support-decoded messages.
    """
    header = getattr(decoded, "header", None)
    if header is None:
        return None
    stamp = getattr(header, "stamp", None)
    if stamp is None:
        return None
    sec: int | None = getattr(stamp, "sec", None)
    nanosec: int | None = getattr(stamp, "nanosec", None)
    if sec is None or nanosec is None:
        return None
    return float(sec) + nanosec / 1e9


def extract_stamp_ns(decoded: Any) -> int | None:
    """Return header.stamp from a decoded message in nanoseconds.

    Used when nanosecond precision is required, such as for the frame
    timestamp sequence during MP4 generation.
    """
    header = getattr(decoded, "header", None)
    if header is None:
        return None
    stamp = getattr(header, "stamp", None)
    if stamp is None:
        return None
    sec: int | None = getattr(stamp, "sec", None)
    nanosec: int | None = getattr(stamp, "nanosec", None)
    if sec is None or nanosec is None:
        return None
    return int(sec) * 1_000_000_000 + int(nanosec)
