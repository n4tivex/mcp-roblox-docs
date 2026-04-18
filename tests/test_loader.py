"""Tests for data loader docs normalization."""

from src.data.loader import DataLoader
from src.utils.formatter import format_member


class TestDocsMapNormalization:
    """Tests for member descriptions in api docs map."""

    def test_build_docs_map_parses_globaltype_member_keys(self, temp_cache_dir):
        """Globaltype member docs should be grouped under their class docs."""
        loader = DataLoader(cache_dir=temp_cache_dir)
        loader._api_docs = {
            "@roblox/globaltype/ProximityPrompt.MaxActivationDistance": {
                "description": "The maximum distance for prompt activation.",
            },
        }

        loader._build_docs_map()
        docs = loader.get_class_doc("ProximityPrompt")

        assert docs is not None
        assert docs["MaxActivationDistance"]["description"] == (
            "The maximum distance for prompt activation."
        )

    def test_member_description_flows_to_formatter(self, temp_cache_dir):
        """Formatted member output should include description from normalized docs."""
        loader = DataLoader(cache_dir=temp_cache_dir)
        loader._api_docs = {
            "ProximityPrompt": {"description": "A prompt object."},
            "@roblox/globaltype/ProximityPrompt.MaxActivationDistance": {
                "description": "The maximum distance for prompt activation.",
            },
        }

        loader._build_docs_map()
        docs = loader.get_class_doc("proximityprompt")
        member = {
            "MemberType": "Property",
            "Name": "MaxActivationDistance",
            "ValueType": {"Name": "float"},
            "Tags": [],
        }

        output = format_member(member, "ProximityPrompt", docs)

        assert "DESCRIPTION:" in output
        assert "The maximum distance for prompt activation." in output
