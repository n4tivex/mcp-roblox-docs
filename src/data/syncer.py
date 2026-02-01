"""
Data Syncer - Downloads and updates Roblox API data from GitHub sources.

Data Sources (all FREE):
- API-Dump.json: Complete API structure (classes, members, enums)
- Full-API-Dump.json: Same with default values
- api-docs/{lang}.json: Human-readable descriptions (15 languages)
- FVariables.txt: FastFlags (DFFlag, FFlag, SFFlag, etc.)
- LuauTypes.d.luau: Roblox Luau type definitions
- ReflectionMetadata.xml: Extra class metadata (categories, icons)
- openapi.json: Roblox Open Cloud REST API specification
- Luau language docs: Language reference markdown files

v3.0.0 Performance Optimizations:
- Parallel downloads with semaphore (10 concurrent)
- Retry logic with exponential backoff (3 attempts)
- HTTP compression (gzip, deflate)
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import orjson

logger = logging.getLogger(__name__)

# =============================================================================
# PERFORMANCE CONSTANTS
# =============================================================================
DOWNLOAD_CONCURRENCY = 10  # Max parallel downloads
MAX_RETRIES = 3  # Number of retry attempts
RETRY_DELAY = 1.0  # Base delay in seconds (doubles each retry)
USER_AGENT = "mcp-roblox-docs/3.1.0"

# GitHub raw URLs for Roblox Client Tracker
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/MaximumADHD/Roblox-Client-Tracker/roblox"

# GitHub raw URLs for Roblox Creator Docs
CREATOR_DOCS_BASE = "https://raw.githubusercontent.com/Roblox/creator-docs/main/content/en-us"

SOURCES = {
    # Core API data (MaximumADHD)
    "api_dump": f"{GITHUB_RAW_BASE}/API-Dump.json",
    "full_api_dump": f"{GITHUB_RAW_BASE}/Full-API-Dump.json",
    "version": f"{GITHUB_RAW_BASE}/version.txt",
    "version_guid": f"{GITHUB_RAW_BASE}/version-guid.txt",
    # Extended data (MaximumADHD)
    "fvariables": f"{GITHUB_RAW_BASE}/FVariables.txt",
    "luau_types": f"{GITHUB_RAW_BASE}/LuauTypes.d.luau",
    "reflection_metadata": f"{GITHUB_RAW_BASE}/ReflectionMetadata.xml",
    # Open Cloud API (Roblox Creator Docs)
    "openapi": f"{CREATOR_DOCS_BASE}/reference/cloud/openapi.json",
}

# Roblox Data Types (from creator-docs)
DATATYPE_FILES = [
    "Axes",
    "BrickColor",
    "CFrame",
    "CatalogSearchParams",
    "Color3",
    "ColorSequence",
    "ColorSequenceKeypoint",
    "Content",
    "DateTime",
    "DockWidgetPluginGuiInfo",
    "Enum",
    "EnumItem",
    "Enums",
    "Faces",
    "FloatCurveKey",
    "Font",
    "Instance",
    "NumberRange",
    "NumberSequence",
    "NumberSequenceKeypoint",
    "OverlapParams",
    "Path2DControlPoint",
    "PathWaypoint",
    "PhysicalProperties",
    "RBXScriptConnection",
    "RBXScriptSignal",
    "Random",
    "Ray",
    "RaycastParams",
    "RaycastResult",
    "Rect",
    "Region3",
    "Region3int16",
    "RotationCurveKey",
    "Secret",
    "SharedTable",
    "TweenInfo",
    "UDim",
    "UDim2",
    "ValueCurveKey",
    "Vector2",
    "Vector2int16",
    "Vector3",
    "Vector3int16",
]

# Luau Libraries (from creator-docs)
LIBRARY_FILES = [
    "bit32",
    "buffer",
    "coroutine",
    "debug",
    "math",
    "os",
    "string",
    "table",
    "task",
    "utf8",
    "vector",
]

DATATYPE_BASE = f"{CREATOR_DOCS_BASE}/reference/engine/datatypes"
LIBRARY_BASE = f"{CREATOR_DOCS_BASE}/reference/engine/libraries"

# Luau language documentation topics
LUAU_DOCS_TOPICS = [
    "booleans",
    "comments",
    "control-structures",
    "enums",
    "functions",
    "metatables",
    "native-code-gen",
    "nil",
    "numbers",
    "operators",
    "queues",
    "scope",
    "stacks",
    "strings",
    "tables",
    "tuples",
    "type-checking",
    "type-coercion",
    "userdata",
    "variables",
]

# Language codes available in api-docs
AVAILABLE_LANGUAGES = [
    "en-us",
    "de-de",
    "es-es",
    "fr-fr",
    "id-id",
    "it-it",
    "ja-jp",
    "ko-kr",
    "pl-pl",
    "pt-br",
    "th-th",
    "tr-tr",
    "vi-vn",
    "zh-cn",
    "zh-tw",
]


def get_api_docs_url(lang: str = "en-us") -> str:
    """Get the URL for API docs in a specific language."""
    if lang not in AVAILABLE_LANGUAGES:
        lang = "en-us"
    return f"{GITHUB_RAW_BASE}/api-docs/{lang}.json"


def get_luau_doc_url(topic: str) -> str:
    """Get the URL for a Luau language documentation topic."""
    return f"{CREATOR_DOCS_BASE}/luau/{topic}.md"


class DataSyncer:
    """Handles downloading and caching of Roblox API data."""

    def __init__(self, cache_dir: Path, language: str = "en-us"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.language = language if language in AVAILABLE_LANGUAGES else "en-us"
        self.meta_path = self.cache_dir / "meta.json"
        self._client: httpx.AsyncClient | None = None

    @property
    def api_dump_path(self) -> Path:
        return self.cache_dir / "api-dump.json"

    @property
    def api_docs_path(self) -> Path:
        return self.cache_dir / f"api-docs-{self.language}.json"

    @property
    def full_api_dump_path(self) -> Path:
        return self.cache_dir / "full-api-dump.json"

    @property
    def fvariables_path(self) -> Path:
        return self.cache_dir / "fvariables.txt"

    @property
    def luau_types_path(self) -> Path:
        return self.cache_dir / "luau-types.d.luau"

    @property
    def reflection_metadata_path(self) -> Path:
        return self.cache_dir / "reflection-metadata.xml"

    @property
    def openapi_path(self) -> Path:
        return self.cache_dir / "openapi.json"

    @property
    def luau_docs_dir(self) -> Path:
        return self.cache_dir / "luau-docs"

    @property
    def datatypes_dir(self) -> Path:
        return self.cache_dir / "datatypes"

    @property
    def libraries_dir(self) -> Path:
        return self.cache_dir / "libraries"

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with compression support."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0),
                follow_redirects=True,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept-Encoding": "gzip, deflate",  # HTTP compression
                },
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _load_meta(self) -> dict[str, Any]:
        """Load sync metadata."""
        if self.meta_path.exists():
            try:
                return orjson.loads(self.meta_path.read_bytes())
            except Exception:
                pass
        return {}

    def _save_meta(self, meta: dict[str, Any]) -> None:
        """Save sync metadata."""
        self.meta_path.write_bytes(orjson.dumps(meta, option=orjson.OPT_INDENT_2))

    async def get_remote_version(self) -> str | None:
        """Fetch current Roblox version from GitHub."""
        try:
            client = await self._get_client()
            response = await client.get(SOURCES["version"])
            response.raise_for_status()
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Failed to fetch remote version: {e}")
            return None

    def get_local_version(self) -> str | None:
        """Get locally cached version."""
        meta = self._load_meta()
        return meta.get("version")

    async def needs_sync(self, force: bool = False) -> bool:
        """Check if data needs to be synced."""
        if force:
            return True

        # Check if cache exists
        if not self.api_dump_path.exists():
            logger.info("No cached data found, sync required")
            return True

        meta = self._load_meta()

        # Check sync age
        last_sync = meta.get("last_sync")
        if last_sync:
            last_sync_time = datetime.fromisoformat(last_sync)
            age_hours = (datetime.now(timezone.utc) - last_sync_time).total_seconds() / 3600
            if age_hours > 24:
                logger.info(f"Cache is {age_hours:.1f} hours old, checking for updates")
                # Check version
                remote_version = await self.get_remote_version()
                local_version = meta.get("version")
                if remote_version and remote_version != local_version:
                    logger.info(f"New version available: {remote_version} (was: {local_version})")
                    return True

        return False

    async def _download_file(self, url: str, dest: Path) -> bool:
        """Download a file from URL to destination with retry logic."""
        for attempt in range(MAX_RETRIES):
            try:
                client = await self._get_client()
                if attempt == 0:
                    logger.info(f"Downloading {url}")
                else:
                    logger.info(f"Retry {attempt}/{MAX_RETRIES - 1} for {url}")

                response = await client.get(url)
                response.raise_for_status()
                dest.write_bytes(response.content)
                logger.info(f"Saved to {dest} ({len(response.content):,} bytes)")
                return True
            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.ConnectError) as e:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (2**attempt)  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"Download failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Failed after {MAX_RETRIES} attempts: {url} - {e}")
                    return False
            except Exception as e:
                logger.error(f"Unexpected error downloading {url}: {e}")
                return False
        return False

    async def sync(self, force: bool = False) -> bool:
        """
        Sync data from remote sources.

        Returns True if sync was successful.
        """
        if not await self.needs_sync(force):
            logger.info("Data is up to date, skipping sync")
            return True

        logger.info("Starting data sync...")
        success = True

        # Download API dump (required)
        if not await self._download_file(SOURCES["api_dump"], self.api_dump_path):
            success = False

        # Download API docs for current language
        docs_url = get_api_docs_url(self.language)
        if not await self._download_file(docs_url, self.api_docs_path):
            logger.warning(f"Failed to download docs for {self.language}, trying en-us")
            if self.language != "en-us":
                docs_url = get_api_docs_url("en-us")
                await self._download_file(docs_url, self.cache_dir / "api-docs-en-us.json")

        # Download full API dump (optional, for default values)
        await self._download_file(SOURCES["full_api_dump"], self.full_api_dump_path)

        # Download extended data sources (all optional, don't fail sync if missing)
        # FVariables (FastFlags)
        await self._download_file(SOURCES["fvariables"], self.fvariables_path)

        # LuauTypes
        await self._download_file(SOURCES["luau_types"], self.luau_types_path)

        # ReflectionMetadata
        await self._download_file(SOURCES["reflection_metadata"], self.reflection_metadata_path)

        # Open Cloud API spec
        await self._download_file(SOURCES["openapi"], self.openapi_path)

        # Luau language documentation
        await self._sync_luau_docs()

        # Data types and libraries (YAML files from creator-docs)
        await self._sync_datatypes()
        await self._sync_libraries()

        # Get version info
        remote_version = await self.get_remote_version()

        # Update metadata
        meta = {
            "version": remote_version,
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "language": self.language,
            "sources": list(SOURCES.keys()) + ["luau_docs"],
        }
        self._save_meta(meta)

        await self.close()

        if success:
            logger.info(f"Sync complete! Version: {remote_version}")
        else:
            logger.warning("Sync completed with some errors")

        return success

    async def _sync_luau_docs(self) -> None:
        """Download Luau language documentation markdown files (parallel)."""
        self.luau_docs_dir.mkdir(parents=True, exist_ok=True)
        semaphore = asyncio.Semaphore(DOWNLOAD_CONCURRENCY)

        async def download_with_limit(topic: str) -> bool:
            async with semaphore:
                url = get_luau_doc_url(topic)
                dest = self.luau_docs_dir / f"{topic}.md"
                return await self._download_file(url, dest)

        await asyncio.gather(*[download_with_limit(topic) for topic in LUAU_DOCS_TOPICS])

    async def _sync_datatypes(self) -> None:
        """Download Roblox datatype YAML files from creator-docs (parallel)."""
        self.datatypes_dir.mkdir(parents=True, exist_ok=True)
        semaphore = asyncio.Semaphore(DOWNLOAD_CONCURRENCY)

        async def download_with_limit(datatype: str) -> bool:
            async with semaphore:
                url = f"{DATATYPE_BASE}/{datatype}.yaml"
                dest = self.datatypes_dir / f"{datatype}.yaml"
                return await self._download_file(url, dest)

        await asyncio.gather(*[download_with_limit(dt) for dt in DATATYPE_FILES])

    async def _sync_libraries(self) -> None:
        """Download Luau library YAML files from creator-docs (parallel)."""
        self.libraries_dir.mkdir(parents=True, exist_ok=True)
        semaphore = asyncio.Semaphore(DOWNLOAD_CONCURRENCY)

        async def download_with_limit(library: str) -> bool:
            async with semaphore:
                url = f"{LIBRARY_BASE}/{library}.yaml"
                dest = self.libraries_dir / f"{library}.yaml"
                return await self._download_file(url, dest)

        await asyncio.gather(*[download_with_limit(lib) for lib in LIBRARY_FILES])

    async def sync_language(self, lang: str) -> bool:
        """Download API docs for a specific language."""
        if lang not in AVAILABLE_LANGUAGES:
            logger.error(f"Unknown language: {lang}")
            return False

        dest = self.cache_dir / f"api-docs-{lang}.json"
        url = get_api_docs_url(lang)
        return await self._download_file(url, dest)

    def get_available_languages(self) -> list[str]:
        """Get list of available language codes."""
        return AVAILABLE_LANGUAGES.copy()

    def get_cached_languages(self) -> list[str]:
        """Get list of languages that are already cached."""
        cached = []
        for lang in AVAILABLE_LANGUAGES:
            if (self.cache_dir / f"api-docs-{lang}.json").exists():
                cached.append(lang)
        return cached

    def get_luau_topics(self) -> list[str]:
        """Get list of available Luau documentation topics."""
        return LUAU_DOCS_TOPICS.copy()

    def get_cached_luau_topics(self) -> list[str]:
        """Get list of cached Luau documentation topics."""
        if not self.luau_docs_dir.exists():
            return []
        return [f.stem for f in self.luau_docs_dir.glob("*.md") if f.stem in LUAU_DOCS_TOPICS]


async def main():
    """CLI entry point for manual sync."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    cache_dir = Path(__file__).parent.parent.parent / "cache"
    syncer = DataSyncer(cache_dir, language="en-us")

    # Full sync with all data sources
    await syncer.sync(force=True)

    # Also download Indonesian for multi-language support
    await syncer.sync_language("id-id")

    print(f"\nSync complete! Cache directory: {cache_dir}")
    print(f"Files downloaded:")
    print(f"  - API Dump: {syncer.api_dump_path.exists()}")
    print(f"  - Full API Dump: {syncer.full_api_dump_path.exists()}")
    print(f"  - FVariables: {syncer.fvariables_path.exists()}")
    print(f"  - Luau Types: {syncer.luau_types_path.exists()}")
    print(f"  - Reflection Metadata: {syncer.reflection_metadata_path.exists()}")
    print(f"  - OpenAPI: {syncer.openapi_path.exists()}")
    print(f"  - Luau Docs: {len(syncer.get_cached_luau_topics())} topics")


if __name__ == "__main__":
    asyncio.run(main())
