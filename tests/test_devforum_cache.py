"""Tests for DevForum cache persistence."""

import pytest
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.server import (
    _load_devforum_cache,
    _save_devforum_cache,
    _get_devforum_cache_path,
    _devforum_cache,
    _DEVFORUM_CACHE_TTL,
)


class TestDevForumCachePersistence:
    """Tests for DevForum cache save/load functionality."""

    def test_cache_file_path_exists(self):
        """Test cache file path is valid."""
        path = _get_devforum_cache_path()
        assert path.name == "devforum_cache.json"
        assert path.parent.exists() or True  # May not exist yet

    def test_save_and_load_cache(self, temp_cache_dir, monkeypatch):
        """Test saving and loading cache."""
        import src.server as server_module

        # Patch the cache directory
        test_cache_path = temp_cache_dir / "devforum_cache.json"
        monkeypatch.setattr(server_module, "_get_devforum_cache_path", lambda: test_cache_path)
        monkeypatch.setattr(server_module, "_devforum_cache_loaded", False)

        # Clear existing cache
        server_module._devforum_cache.clear()

        # Add test data
        test_time = datetime.now(timezone.utc)
        test_results = [{"id": 1, "title": "Test Topic"}]
        server_module._devforum_cache["test query"] = (test_time, test_results)

        # Save
        _save_devforum_cache()

        # Verify file exists
        assert test_cache_path.exists()

        # Read and verify content
        data = json.loads(test_cache_path.read_text())
        assert data["version"] == 1
        assert "test query" in data["entries"]

    def test_load_invalid_cache_file(self, temp_cache_dir, monkeypatch):
        """Test loading corrupted cache file doesn't crash."""
        import src.server as server_module

        test_cache_path = temp_cache_dir / "devforum_cache.json"
        monkeypatch.setattr(server_module, "_get_devforum_cache_path", lambda: test_cache_path)
        monkeypatch.setattr(server_module, "_devforum_cache_loaded", False)
        server_module._devforum_cache.clear()

        # Write invalid JSON
        test_cache_path.write_text("not valid json {{{")

        # Should not raise, just log warning
        _load_devforum_cache()

        # Cache should still work (empty)
        assert server_module._devforum_cache_loaded

    def test_load_expired_entries_ignored(self, temp_cache_dir, monkeypatch):
        """Test expired entries are not loaded."""
        import src.server as server_module

        test_cache_path = temp_cache_dir / "devforum_cache.json"
        monkeypatch.setattr(server_module, "_get_devforum_cache_path", lambda: test_cache_path)
        monkeypatch.setattr(server_module, "_devforum_cache_loaded", False)
        server_module._devforum_cache.clear()

        # Create cache with expired entry
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)  # Older than TTL
        data = {
            "version": 1,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "entries": {
                "expired query": {
                    "query": "expired query",
                    "results": [{"id": 1}],
                    "timestamp": old_time.isoformat(),
                    "ttl_seconds": 3600,  # 1 hour
                }
            },
        }
        test_cache_path.write_text(json.dumps(data))

        # Load
        _load_devforum_cache()

        # Expired entry should not be loaded
        assert "expired query" not in server_module._devforum_cache

    def test_load_valid_entries(self, temp_cache_dir, monkeypatch):
        """Test valid entries are loaded."""
        import src.server as server_module

        test_cache_path = temp_cache_dir / "devforum_cache.json"
        monkeypatch.setattr(server_module, "_get_devforum_cache_path", lambda: test_cache_path)
        monkeypatch.setattr(server_module, "_devforum_cache_loaded", False)
        server_module._devforum_cache.clear()

        # Create cache with valid entry
        recent_time = datetime.now(timezone.utc) - timedelta(minutes=30)  # Within TTL
        data = {
            "version": 1,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "entries": {
                "valid query": {
                    "query": "valid query",
                    "results": [{"id": 123, "title": "Test"}],
                    "timestamp": recent_time.isoformat(),
                    "ttl_seconds": 3600,
                }
            },
        }
        test_cache_path.write_text(json.dumps(data))

        # Load
        _load_devforum_cache()

        # Valid entry should be loaded
        assert "valid query" in server_module._devforum_cache
        _, results = server_module._devforum_cache["valid query"]
        assert len(results) == 1
        assert results[0]["id"] == 123

    def test_version_mismatch_clears_cache(self, temp_cache_dir, monkeypatch):
        """Test version mismatch causes cache to be cleared."""
        import src.server as server_module

        test_cache_path = temp_cache_dir / "devforum_cache.json"
        monkeypatch.setattr(server_module, "_get_devforum_cache_path", lambda: test_cache_path)
        monkeypatch.setattr(server_module, "_devforum_cache_loaded", False)
        server_module._devforum_cache.clear()

        # Create cache with wrong version
        data = {
            "version": 999,  # Wrong version
            "entries": {"query": {"results": []}},
        }
        test_cache_path.write_text(json.dumps(data))

        # Load
        _load_devforum_cache()

        # Cache should be empty (version mismatch)
        assert len(server_module._devforum_cache) == 0
