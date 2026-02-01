"""
Input validation utilities for MCP tools.

Provides validation and sanitization for user inputs to prevent:
- Excessively long queries that could cause performance issues
- Invalid characters in class/member names
- Out-of-range limit parameters

v3.0.0: Initial implementation
"""

from __future__ import annotations

import re

# =============================================================================
# CONSTANTS
# =============================================================================
MAX_QUERY_LENGTH = 500  # Max characters for search queries
MAX_NAME_LENGTH = 100  # Max characters for class/member names
MAX_TOPIC_LENGTH = 50  # Max characters for topic names

# Roblox identifiers: alphanumeric and underscores
VALID_NAME_PATTERN = re.compile(r"^[\w]+$")

# More permissive for search queries
VALID_QUERY_PATTERN = re.compile(r"^[\w\s\-\.\:\,\(\)]+$")


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================


def validate_query(query: str | None) -> str:
    """
    Validate and sanitize search query.

    Args:
        query: Raw user input for search

    Returns:
        Sanitized query string

    Raises:
        ValueError: If query is empty or invalid
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    sanitized = query.strip()[:MAX_QUERY_LENGTH]
    return sanitized


def validate_class_name(name: str | None) -> str:
    """
    Validate Roblox class name.

    Args:
        name: Class name to validate

    Returns:
        Validated class name

    Raises:
        ValueError: If name is empty or invalid
    """
    if not name or not name.strip():
        raise ValueError("Class name cannot be empty")

    sanitized = name.strip()[:MAX_NAME_LENGTH]

    # Roblox class names are alphanumeric
    if not VALID_NAME_PATTERN.match(sanitized):
        raise ValueError(f"Invalid class name format: {sanitized}")

    return sanitized


def validate_member_name(name: str | None) -> str:
    """
    Validate Roblox member name (property, method, event).

    Args:
        name: Member name to validate

    Returns:
        Validated member name

    Raises:
        ValueError: If name is empty or invalid
    """
    if not name or not name.strip():
        raise ValueError("Member name cannot be empty")

    sanitized = name.strip()[:MAX_NAME_LENGTH]

    if not VALID_NAME_PATTERN.match(sanitized):
        raise ValueError(f"Invalid member name format: {sanitized}")

    return sanitized


def validate_enum_name(name: str | None) -> str:
    """
    Validate Roblox enum name.

    Args:
        name: Enum name to validate

    Returns:
        Validated enum name

    Raises:
        ValueError: If name is empty or invalid
    """
    if not name or not name.strip():
        raise ValueError("Enum name cannot be empty")

    sanitized = name.strip()[:MAX_NAME_LENGTH]

    if not VALID_NAME_PATTERN.match(sanitized):
        raise ValueError(f"Invalid enum name format: {sanitized}")

    return sanitized


def validate_topic_name(topic: str | None) -> str:
    """
    Validate Luau documentation topic name.

    Args:
        topic: Topic name to validate

    Returns:
        Validated topic name

    Raises:
        ValueError: If topic is empty or invalid
    """
    if not topic or not topic.strip():
        raise ValueError("Topic cannot be empty")

    # Topics can have hyphens (e.g., "type-checking", "control-structures")
    sanitized = topic.strip().lower()[:MAX_TOPIC_LENGTH]

    # Allow alphanumeric and hyphens
    if not re.match(r"^[\w\-]+$", sanitized):
        raise ValueError(f"Invalid topic format: {sanitized}")

    return sanitized


def validate_limit(
    limit: int | None, min_val: int = 1, max_val: int = 50, default: int = 25
) -> int:
    """
    Validate and clamp limit parameter.

    Args:
        limit: Raw limit value
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        default: Default value if limit is None

    Returns:
        Clamped limit value
    """
    if limit is None:
        return default

    return max(min_val, min(int(limit), max_val))


def validate_operation_id(operation_id: str | None) -> str:
    """
    Validate Open Cloud API operation ID.

    Args:
        operation_id: Operation ID to validate

    Returns:
        Validated operation ID

    Raises:
        ValueError: If operation_id is empty or invalid
    """
    if not operation_id or not operation_id.strip():
        raise ValueError("Operation ID cannot be empty")

    sanitized = operation_id.strip()[:MAX_NAME_LENGTH]
    return sanitized


def validate_flag_name(name: str | None) -> str:
    """
    Validate FastFlag name.

    Args:
        name: Flag name to validate

    Returns:
        Validated flag name

    Raises:
        ValueError: If name is empty or invalid
    """
    if not name or not name.strip():
        raise ValueError("Flag name cannot be empty")

    sanitized = name.strip()[:MAX_NAME_LENGTH]

    if not VALID_NAME_PATTERN.match(sanitized):
        raise ValueError(f"Invalid flag name format: {sanitized}")

    return sanitized
