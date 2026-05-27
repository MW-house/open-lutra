"""Shared API endpoint dependencies and exception handlers."""

from app.dependencies.exception_handlers import register_exception_handlers
from app.dependencies.path_validators import require_dir, resolve_safe_path
from app.dependencies.services import (
    MonitorDep,
    RecorderDep,
    ROS2CommandDep,
    get_monitor,
    get_recorder,
    get_ros2_command,
    set_monitor,
    set_recorder,
    set_ros2_command,
)

__all__ = [
    "MonitorDep",
    "ROS2CommandDep",
    "RecorderDep",
    "get_monitor",
    "get_recorder",
    "get_ros2_command",
    "register_exception_handlers",
    "require_dir",
    "resolve_safe_path",
    "set_monitor",
    "set_recorder",
    "set_ros2_command",
]
