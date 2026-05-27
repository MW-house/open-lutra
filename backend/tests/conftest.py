"""Shared test configuration."""

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """rclpy-dependent tests that fail to import are auto-skipped (importorskip)."""
