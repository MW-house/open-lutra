"""Tests for QoSOverrideFile."""

from pathlib import Path

from app.infra.ros2 import QoSOverrideFile


class TestQoSOverrideFile:
    """Tests for generating and managing the QoS override YAML file."""

    def test_creates_yaml_file(self) -> None:
        """Verifies that the YAML file is created."""
        qos = QoSOverrideFile({"/topic_a": "reliable"})
        args = qos.to_args()
        assert len(args) == 2
        assert args[0] == "--qos-profile-overrides-path"

        content = Path(args[1]).read_text()
        assert "/topic_a:" in content
        assert "reliability: reliable" in content
        assert "history: keep_last" in content
        assert "depth: 10" in content

        qos.cleanup()

    def test_creates_yaml_with_multiple_topics(self) -> None:
        """YAML for multiple topics is generated correctly."""
        qos = QoSOverrideFile({"/topic_a": "reliable", "/topic_b": "best_effort"})
        content = Path(qos.to_args()[1]).read_text()
        assert "/topic_a:" in content
        assert "reliability: reliable" in content
        assert "/topic_b:" in content
        assert "reliability: best_effort" in content

        qos.cleanup()

    def test_cleanup_removes_file(self) -> None:
        """The file is removed after cleanup."""
        qos = QoSOverrideFile({"/topic": "reliable"})
        file_path = Path(qos.to_args()[1])
        assert file_path.exists()

        qos.cleanup()
        assert not file_path.exists()
