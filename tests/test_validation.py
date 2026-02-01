"""Tests for input validation module."""

import pytest
from src.utils.validation import (
    validate_query,
    validate_class_name,
    validate_member_name,
    validate_enum_name,
    validate_topic_name,
    validate_limit,
    validate_operation_id,
    validate_flag_name,
    MAX_QUERY_LENGTH,
    MAX_NAME_LENGTH,
)


class TestValidateQuery:
    """Tests for validate_query function."""

    def test_valid_query(self):
        """Test valid query passes."""
        result = validate_query("TweenService")
        assert result == "TweenService"

    def test_query_with_spaces(self):
        """Test query with spaces."""
        result = validate_query("tween service animation")
        assert result == "tween service animation"

    def test_query_strips_whitespace(self):
        """Test whitespace is stripped."""
        result = validate_query("  hello  ")
        assert result == "hello"

    def test_empty_query_raises(self):
        """Test empty query raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_query("")

    def test_whitespace_only_query_raises(self):
        """Test whitespace-only query raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_query("   ")

    def test_none_query_raises(self):
        """Test None query raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_query(None)

    def test_query_truncated_at_max_length(self):
        """Test long query is truncated."""
        long_query = "a" * (MAX_QUERY_LENGTH + 100)
        result = validate_query(long_query)
        assert len(result) == MAX_QUERY_LENGTH


class TestValidateClassName:
    """Tests for validate_class_name function."""

    def test_valid_class_name(self):
        """Test valid class name passes."""
        result = validate_class_name("TweenService")
        assert result == "TweenService"

    def test_class_name_with_underscore(self):
        """Test class name with underscore."""
        result = validate_class_name("Some_Class")
        assert result == "Some_Class"

    def test_class_name_with_numbers(self):
        """Test class name with numbers."""
        result = validate_class_name("Vector3")
        assert result == "Vector3"

    def test_empty_class_name_raises(self):
        """Test empty class name raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_class_name("")

    def test_invalid_characters_raises(self):
        """Test invalid characters raise ValueError."""
        with pytest.raises(ValueError, match="Invalid class name"):
            validate_class_name("Part.Anchored")

    def test_spaces_raise(self):
        """Test spaces raise ValueError."""
        with pytest.raises(ValueError, match="Invalid class name"):
            validate_class_name("Tween Service")

    def test_truncated_at_max_length(self):
        """Test long name is truncated before validation."""
        long_name = "A" * (MAX_NAME_LENGTH + 10)
        result = validate_class_name(long_name)
        assert len(result) == MAX_NAME_LENGTH


class TestValidateMemberName:
    """Tests for validate_member_name function."""

    def test_valid_member_name(self):
        """Test valid member name passes."""
        result = validate_member_name("Anchored")
        assert result == "Anchored"

    def test_empty_raises(self):
        """Test empty member name raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_member_name("")

    def test_invalid_characters_raises(self):
        """Test invalid characters raise ValueError."""
        with pytest.raises(ValueError, match="Invalid member name"):
            validate_member_name("Get:Value")


class TestValidateEnumName:
    """Tests for validate_enum_name function."""

    def test_valid_enum_name(self):
        """Test valid enum name passes."""
        result = validate_enum_name("Material")
        assert result == "Material"

    def test_empty_raises(self):
        """Test empty enum name raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_enum_name("")


class TestValidateTopicName:
    """Tests for validate_topic_name function."""

    def test_valid_topic(self):
        """Test valid topic name passes."""
        result = validate_topic_name("tables")
        assert result == "tables"

    def test_topic_with_hyphens(self):
        """Test topic with hyphens passes."""
        result = validate_topic_name("type-checking")
        assert result == "type-checking"

    def test_topic_normalized_to_lowercase(self):
        """Test topic is normalized to lowercase."""
        result = validate_topic_name("Type-Checking")
        assert result == "type-checking"

    def test_topic_with_underscores_converted(self):
        """Test underscores work as identifiers."""
        result = validate_topic_name("control_structures")
        assert result == "control_structures"

    def test_empty_raises(self):
        """Test empty topic raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_topic_name("")


class TestValidateLimit:
    """Tests for validate_limit function."""

    def test_valid_limit(self):
        """Test valid limit passes through."""
        result = validate_limit(25)
        assert result == 25

    def test_none_returns_default(self):
        """Test None returns default value."""
        result = validate_limit(None, default=25)
        assert result == 25

    def test_below_min_clamped(self):
        """Test value below min is clamped."""
        result = validate_limit(0, min_val=1, max_val=50)
        assert result == 1

    def test_above_max_clamped(self):
        """Test value above max is clamped."""
        result = validate_limit(100, min_val=1, max_val=50)
        assert result == 50

    def test_custom_range(self):
        """Test custom min/max range."""
        result = validate_limit(15, min_val=10, max_val=20)
        assert result == 15


class TestValidateOperationId:
    """Tests for validate_operation_id function."""

    def test_valid_operation_id(self):
        """Test valid operation ID passes."""
        result = validate_operation_id("DataStore_GetEntry")
        assert result == "DataStore_GetEntry"

    def test_empty_raises(self):
        """Test empty operation ID raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_operation_id("")


class TestValidateFlagName:
    """Tests for validate_flag_name function."""

    def test_valid_flag_name(self):
        """Test valid flag name passes."""
        result = validate_flag_name("DFFlagDebugVisualize")
        assert result == "DFFlagDebugVisualize"

    def test_empty_raises(self):
        """Test empty flag name raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_flag_name("")

    def test_invalid_characters_raises(self):
        """Test invalid characters raise ValueError."""
        with pytest.raises(ValueError, match="Invalid flag name"):
            validate_flag_name("FFlag-Invalid")
