"""Tests for the exception handlers.

Verifies that each recording exception is mapped to the correct HTTP status code.

NOTE: app.main requires rclpy, so this can only run inside Docker (make test).
"""

import pytest

rclpy = pytest.importorskip("rclpy", reason="rclpy is required (run via 'make test')")

from unittest.mock import MagicMock  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from app.dependencies import set_recorder  # noqa: E402
from app.dependencies.services import get_recorder  # noqa: E402
from app.features.recording import AlreadyRecordingError, NotRecordingError, RecorderError  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    """Test client for exception tests."""
    app = create_app()
    recorder = MagicMock()
    recorder.is_recording = False
    set_recorder(recorder)
    return TestClient(app)


class TestAlreadyRecordingHandler:
    """AlreadyRecordingError -> 409 Conflict."""

    def test_returns_409(self, client: TestClient) -> None:
        recorder = get_recorder()
        recorder.start.side_effect = AlreadyRecordingError("Already recording")
        response = client.post("/api/recording/start")
        assert response.status_code == 409
        assert response.json()["detail"] == "Already recording"


class TestNotRecordingHandler:
    """NotRecordingError -> 409 Conflict."""

    def test_returns_409(self, client: TestClient) -> None:
        recorder = get_recorder()
        recorder.stop.side_effect = NotRecordingError("Not currently recording")
        response = client.post("/api/recording/stop")
        assert response.status_code == 409
        assert response.json()["detail"] == "Not currently recording"


class TestRecorderErrorHandler:
    """RecorderError -> 500 Internal Server Error."""

    def test_returns_500(self, client: TestClient) -> None:
        recorder = get_recorder()
        recorder.start.side_effect = RecorderError("Internal error")
        response = client.post("/api/recording/start")
        assert response.status_code == 500
        assert response.json()["detail"] == "Internal error"
