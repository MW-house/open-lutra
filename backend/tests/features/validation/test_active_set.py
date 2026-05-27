"""Tests for active_set."""

from app.features.validation.active_set import get_builtin_recording_validators
from app.features.validation.builtins import RequiredTopicsPresent, TotalDurationSec


class TestActiveSet:
    def test_returns_both_builtins(self) -> None:
        validators = get_builtin_recording_validators()
        types = {type(v) for v in validators}
        assert RequiredTopicsPresent in types
        assert TotalDurationSec in types

    def test_returns_new_instances_each_call(self) -> None:
        """Returns fresh instances on every call (even though validators are stateless)."""
        a = get_builtin_recording_validators()
        b = get_builtin_recording_validators()
        assert a is not b
        assert all(x is not y for x, y in zip(a, b, strict=True))
