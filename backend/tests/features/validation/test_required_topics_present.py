"""Tests for the RequiredTopicsPresent validator."""

from app.features.validation.builtins.required_topics_present import RequiredTopicsPresent
from tests.features.validation.conftest import make_ctx, make_topic


class TestRequiredTopicsPresent:
    """Tests for RequiredTopicsPresent.validate()."""

    def test_empty_topics_returns_pass(self) -> None:
        """With no required topics configured, always pass."""
        validator = RequiredTopicsPresent(topics=[])
        ctx = make_ctx(topics=[make_topic("/a", msg_count=10)])

        result = validator.validate(ctx)
        assert result.status == "pass"
        assert "No required topics" in result.message

    def test_all_topics_present(self) -> None:
        validator = RequiredTopicsPresent(topics=["/a", "/b"])
        ctx = make_ctx(topics=[make_topic("/a"), make_topic("/b")])

        result = validator.validate(ctx)
        assert result.status == "pass"

    def test_missing_topic_returns_fail(self) -> None:
        validator = RequiredTopicsPresent(topics=["/a", "/b"])
        ctx = make_ctx(topics=[make_topic("/a")])

        result = validator.validate(ctx)
        assert result.status == "fail"
        assert "/b" in result.message
        assert result.details is not None
        assert result.details["missing_topics"] == ["/b"]
        assert result.details["required_topics"] == ["/a", "/b"]

    def test_topic_with_zero_messages_is_missing(self) -> None:
        """A topic with zero messages counts as missing."""
        validator = RequiredTopicsPresent(topics=["/a"])
        ctx = make_ctx(topics=[make_topic("/a", msg_count=0)])

        result = validator.validate(ctx)
        assert result.status == "fail"

    def test_extra_topics_are_ignored(self) -> None:
        """Topics not in the required list are ignored."""
        validator = RequiredTopicsPresent(topics=["/a"])
        ctx = make_ctx(topics=[make_topic("/a"), make_topic("/b"), make_topic("/c")])

        result = validator.validate(ctx)
        assert result.status == "pass"
