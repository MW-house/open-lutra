"""Tests for the TotalDurationSec validator."""

from app.features.validation.builtins.total_duration_sec import TotalDurationSec
from tests.features.validation.conftest import make_ctx


class TestTotalDurationSec:
    """Tests for TotalDurationSec.validate()."""

    def test_no_bounds_returns_pass(self) -> None:
        validator = TotalDurationSec()
        result = validator.validate(make_ctx(duration_sec=60.0))
        assert result.status == "pass"
        assert "No duration bounds" in result.message

    def test_within_range_returns_pass(self) -> None:
        validator = TotalDurationSec(min_sec=10.0, max_sec=600.0)
        result = validator.validate(make_ctx(duration_sec=60.0))
        assert result.status == "pass"
        assert "within range" in result.message

    def test_below_min_returns_fail(self) -> None:
        validator = TotalDurationSec(min_sec=30.0)
        result = validator.validate(make_ctx(duration_sec=10.0))
        assert result.status == "fail"
        assert "below minimum" in result.message
        assert result.details is not None
        assert result.details["min_sec"] == 30.0

    def test_above_max_returns_fail(self) -> None:
        validator = TotalDurationSec(max_sec=30.0)
        result = validator.validate(make_ctx(duration_sec=120.0))
        assert result.status == "fail"
        assert "exceeds maximum" in result.message
        assert result.details is not None
        assert result.details["max_sec"] == 30.0

    def test_only_min_set_within_range(self) -> None:
        validator = TotalDurationSec(min_sec=10.0)
        result = validator.validate(make_ctx(duration_sec=1000.0))
        assert result.status == "pass"

    def test_only_max_set_within_range(self) -> None:
        validator = TotalDurationSec(max_sec=1000.0)
        result = validator.validate(make_ctx(duration_sec=10.0))
        assert result.status == "pass"

    def test_exactly_at_min_passes(self) -> None:
        validator = TotalDurationSec(min_sec=10.0)
        result = validator.validate(make_ctx(duration_sec=10.0))
        assert result.status == "pass"

    def test_exactly_at_max_passes(self) -> None:
        validator = TotalDurationSec(max_sec=10.0)
        result = validator.validate(make_ctx(duration_sec=10.0))
        assert result.status == "pass"
