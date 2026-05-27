"""Tests for the service DI dependency functions."""

import pytest
from fastapi import HTTPException

from app.dependencies.services import get_monitor, get_recorder, set_monitor, set_recorder


class TestGetRecorder:
    """Tests for get_recorder()."""

    def test_raises_when_not_initialized(self) -> None:
        """Returns 503 when uninitialized."""
        # Set explicitly to None to avoid cross-test contamination
        import app.dependencies.services as svc

        original = svc._recorder
        try:
            svc._recorder = None
            with pytest.raises(HTTPException) as exc_info:
                get_recorder()
            assert exc_info.value.status_code == 503
        finally:
            svc._recorder = original

    def test_returns_recorder_when_set(self) -> None:
        """Returns the instance once set."""
        import app.dependencies.services as svc

        original = svc._recorder
        try:
            sentinel = object()
            set_recorder(sentinel)  # type: ignore[arg-type]
            assert get_recorder() is sentinel
        finally:
            svc._recorder = original


class TestGetMonitor:
    """Tests for get_monitor()."""

    def test_raises_when_not_initialized(self) -> None:
        """Returns 503 when uninitialized."""
        import app.dependencies.services as svc

        original = svc._monitor
        try:
            svc._monitor = None
            with pytest.raises(HTTPException) as exc_info:
                get_monitor()
            assert exc_info.value.status_code == 503
        finally:
            svc._monitor = original

    def test_returns_monitor_when_set(self) -> None:
        """Returns the instance once set."""
        import app.dependencies.services as svc

        original = svc._monitor
        try:
            sentinel = object()
            set_monitor(sentinel)  # type: ignore[arg-type]
            assert get_monitor() is sentinel
        finally:
            svc._monitor = original
