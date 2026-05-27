"""Recording feature.

Public API:
    ROS2BagRecorder: subprocess-based recording service
    RecorderStatus / StopResult: status data
    AlreadyRecordingError / NotRecordingError / RecorderError: exceptions
"""

from app.features.recording.models import (
    AlreadyRecordingError,
    NotRecordingError,
    RecorderError,
    RecorderStatus,
    StopResult,
)
from app.features.recording.service import ROS2BagRecorder

__all__ = [
    "AlreadyRecordingError",
    "NotRecordingError",
    "ROS2BagRecorder",
    "RecorderError",
    "RecorderStatus",
    "StopResult",
]
