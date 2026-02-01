"""Pytest fixtures for mcp-roblox-docs tests."""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for testing."""
    temp_dir = tempfile.mkdtemp(prefix="mcp-roblox-docs-test-")
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_class_data():
    """Sample class data for testing."""
    return [
        {
            "Name": "Part",
            "Superclass": "BasePart",
            "Members": [
                {
                    "MemberType": "Property",
                    "Name": "Anchored",
                    "ValueType": {"Name": "bool"},
                    "Tags": [],
                },
                {
                    "MemberType": "Method",
                    "Name": "Resize",
                    "Parameters": [
                        {"Name": "normalId", "Type": {"Name": "NormalId"}},
                        {"Name": "deltaAmount", "Type": {"Name": "int"}},
                    ],
                    "ReturnType": {"Name": "bool"},
                    "Tags": [],
                },
                {
                    "MemberType": "Event",
                    "Name": "Touched",
                    "Parameters": [{"Name": "otherPart", "Type": {"Name": "BasePart"}}],
                    "Tags": [],
                },
            ],
            "Tags": [],
        },
        {
            "Name": "TweenService",
            "Superclass": "Instance",
            "Members": [
                {
                    "MemberType": "Method",
                    "Name": "Create",
                    "Parameters": [
                        {"Name": "instance", "Type": {"Name": "Instance"}},
                        {"Name": "tweenInfo", "Type": {"Name": "TweenInfo"}},
                        {"Name": "propertyTable", "Type": {"Name": "Dictionary"}},
                    ],
                    "ReturnType": {"Name": "Tween"},
                    "Tags": [],
                },
            ],
            "Tags": ["Service", "NotCreatable"],
        },
    ]


@pytest.fixture
def sample_enum_data():
    """Sample enum data for testing."""
    return [
        {
            "Name": "Material",
            "Items": [
                {"Name": "Plastic", "Value": 256},
                {"Name": "Wood", "Value": 512},
                {"Name": "Slate", "Value": 800},
            ],
        },
        {
            "Name": "EasingStyle",
            "Items": [
                {"Name": "Linear", "Value": 0},
                {"Name": "Sine", "Value": 1},
                {"Name": "Quad", "Value": 2},
            ],
        },
    ]


@pytest.fixture
def sample_docs_data():
    """Sample documentation data for testing."""
    return {
        "Part": {"description": "A part is a fundamental building block."},
        "TweenService": {"description": "Service for creating tweens."},
    }
