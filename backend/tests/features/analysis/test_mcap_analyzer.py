"""I/O tests for MCAP quality analysis (load_report)."""

import json
from pathlib import Path

from app.features.analysis.mcap_analyzer import load_report
from app.features.analysis.models import QualityReport


class TestLoadReport:
    """Tests for load_report()."""

    def test_load_existing_report(self, tmp_path: Path) -> None:
        """Loads a saved report correctly."""
        report = QualityReport(
            duration_sec=60.0,
            total_messages=6000,
            total_topics=1,
            file_size_bytes=1280,
            topics=[],
        )
        report_path = tmp_path / "quality_report.json"
        report_path.write_text(
            json.dumps(report.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        loaded = load_report(tmp_path)
        assert loaded is not None
        assert loaded.total_messages == 6000

    def test_load_nonexistent_report(self, tmp_path: Path) -> None:
        """Returns None when the report is absent."""
        assert load_report(tmp_path) is None

    def test_load_corrupted_report(self, tmp_path: Path) -> None:
        """Returns None when the JSON is corrupted."""
        report_path = tmp_path / "quality_report.json"
        report_path.write_text("{invalid json", encoding="utf-8")
        assert load_report(tmp_path) is None
