"""Dependency injection for service instances."""

from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.features.recording import ROS2BagRecorder
from app.features.topics import TopicMonitorService
from app.infra.ros2 import ROS2Command

# ---------------------------------------------------------------------------
# Recorder
# ---------------------------------------------------------------------------

_recorder: ROS2BagRecorder | None = None


def get_recorder() -> ROS2BagRecorder:
    """DI dependency that returns the recorder instance."""
    if _recorder is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recorder service not initialized",
        )
    return _recorder


def set_recorder(recorder: ROS2BagRecorder) -> None:
    """Set the global recorder instance (called at application startup)."""
    global _recorder
    _recorder = recorder


RecorderDep = Annotated[ROS2BagRecorder, Depends(get_recorder)]

# ---------------------------------------------------------------------------
# TopicMonitorService
# ---------------------------------------------------------------------------

_monitor: TopicMonitorService | None = None


def get_monitor() -> TopicMonitorService:
    """DI dependency that returns the TopicMonitorService instance."""
    if _monitor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Topic monitor not initialized",
        )
    return _monitor


def set_monitor(monitor: TopicMonitorService) -> None:
    """Set the global monitor instance (called at application startup)."""
    global _monitor
    _monitor = monitor


MonitorDep = Annotated[TopicMonitorService, Depends(get_monitor)]

# ---------------------------------------------------------------------------
# ROS2Command
# ---------------------------------------------------------------------------

_ros2_command: ROS2Command | None = None


def get_ros2_command() -> ROS2Command:  # pragma: no cover
    """DI dependency that returns the ROS2Command instance."""
    if _ros2_command is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ROS2Command service not initialized",
        )
    return _ros2_command


def set_ros2_command(ros2_command: ROS2Command) -> None:  # pragma: no cover
    """Set the global ROS2Command instance (called at application startup)."""
    global _ros2_command
    _ros2_command = ros2_command


ROS2CommandDep = Annotated[ROS2Command, Depends(get_ros2_command)]
