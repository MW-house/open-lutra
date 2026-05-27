"""Tests for the ROS2 message conversion utilities.

Only sanitize_value() is in scope. msg_to_dict() / import_message_class() are excluded
because they depend on rosidl_runtime_py.
"""

from app.infra.ros2.message import sanitize_value


class TestSanitizeBytes:
    """Sanitization of binary data."""

    def test_small_bytes_to_hex(self) -> None:
        """Small binaries are converted to a hex string."""
        result = sanitize_value(b"\x00\x01\x02")
        assert result == "000102"

    def test_large_bytes_to_summary(self) -> None:
        """Large binaries are converted to a summary representation."""
        data = b"\x00" * 1000
        result = sanitize_value(data)
        assert "<bytes:" in result
        assert "1,000B" in result

    def test_boundary_64_bytes(self) -> None:
        """Exactly 64 bytes is hex-converted."""
        data = b"\xff" * 64
        result = sanitize_value(data)
        assert result == "ff" * 64


class TestSanitizeList:
    """Sanitization of lists and tuples."""

    def test_short_list_preserved(self) -> None:
        result = sanitize_value([1, 2, 3])
        assert result == [1, 2, 3]

    def test_long_list_truncated(self) -> None:
        """Lists with more than 20 elements are truncated."""
        data = list(range(100))
        result = sanitize_value(data)
        assert result["__truncated"] is True
        assert result["length"] == 100
        assert len(result["preview"]) == 20

    def test_tuple_handled(self) -> None:
        result = sanitize_value((1, 2, 3))
        assert result == [1, 2, 3]

    def test_nested_list(self) -> None:
        result = sanitize_value([[1, 2], [3, 4]])
        assert result == [[1, 2], [3, 4]]


class TestSanitizeDict:
    """Sanitization of dictionaries."""

    def test_dict_values_sanitized(self) -> None:
        result = sanitize_value({"key": b"\x00\x01"})
        assert result == {"key": "0001"}

    def test_nested_dict(self) -> None:
        result = sanitize_value({"outer": {"inner": 42}})
        assert result == {"outer": {"inner": 42}}


class TestSanitizeFloat:
    """Special floating-point values."""

    def test_nan(self) -> None:
        result = sanitize_value(float("nan"))
        assert result == "NaN"

    def test_infinity(self) -> None:
        assert sanitize_value(float("inf")) == "Infinity"
        assert sanitize_value(float("-inf")) == "-Infinity"

    def test_normal_float_preserved(self) -> None:
        assert sanitize_value(3.14) == 3.14


class TestSanitizeOther:
    """Other types."""

    def test_int_preserved(self) -> None:
        assert sanitize_value(42) == 42

    def test_string_preserved(self) -> None:
        assert sanitize_value("hello") == "hello"

    def test_none_preserved(self) -> None:
        assert sanitize_value(None) is None

    def test_bool_preserved(self) -> None:
        assert sanitize_value(True) is True
