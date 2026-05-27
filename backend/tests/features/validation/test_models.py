"""Tests for ValidationReport / ValidationResultItem."""

from datetime import datetime, timezone

from app.features.validation.models import ValidationReport, ValidationResultItem, _worst_status


def _item(status: str, name: str = "test") -> ValidationResultItem:
    return ValidationResultItem(
        validator_name=name,
        source="builtin",
        source_module=None,
        status=status,  # type: ignore[arg-type]
        message="msg",
        details=None,
    )


class TestWorstStatus:
    """Severity ordering of _worst_status()."""

    def test_empty_returns_pass(self) -> None:
        assert _worst_status([]) == "pass"

    def test_all_pass(self) -> None:
        assert _worst_status(["pass", "pass"]) == "pass"

    def test_warn_over_pass(self) -> None:
        assert _worst_status(["pass", "warn", "pass"]) == "warn"

    def test_fail_over_warn(self) -> None:
        assert _worst_status(["warn", "fail", "pass"]) == "fail"

    def test_error_over_fail(self) -> None:
        # error is treated as more severe than fail because it points
        # to a validator implementation issue.
        assert _worst_status(["fail", "error"]) == "error"


class TestValidationReportAggregate:
    """Tests for ValidationReport.aggregate()."""

    def test_aggregate_empty(self) -> None:
        report = ValidationReport.aggregate(
            results=[],
            task_name=None,
            executed_at=datetime.now(timezone.utc),
        )
        assert report.overall_status == "pass"
        assert report.results == []
        assert report.task_name is None

    def test_aggregate_with_mixed_statuses(self) -> None:
        items = [_item("pass"), _item("warn"), _item("fail")]
        report = ValidationReport.aggregate(
            results=items,
            task_name="my_task",
            executed_at=datetime.now(timezone.utc),
        )
        assert report.overall_status == "fail"
        assert report.task_name == "my_task"
        assert len(report.results) == 3
