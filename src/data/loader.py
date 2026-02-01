"""
Data Loader - Lazy loading and in-memory caching of Roblox API data.

Provides efficient access to:
- Classes (with members, inheritance)
- Enums (with items)
- Documentation (descriptions, examples)
- FastFlags (FVariables)
- Luau global types
- Class metadata (categories, icons)
- Open Cloud API endpoints
- Luau language documentation

v3.0.0 Optimizations:
- Pre-compiled regex patterns at module level
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypedDict

import orjson
import yaml

logger = logging.getLogger(__name__)


# =============================================================================
# PRE-COMPILED REGEX PATTERNS (Performance optimization)
# =============================================================================
# FVariables.txt pattern: [Source] PrefixName
_FVARIABLES_PATTERN = re.compile(r"\[([^\]]+)\]\s+(\w+)")

# LuauTypes.d.luau patterns
_FUNCTION_PATTERN = re.compile(r"declare\s+function\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*(.+?))?(?:\n|$)")
_VAR_PATTERN = re.compile(r"declare\s+(\w+)\s*:\s*(.+?)(?:\n|$)")
_TYPE_PATTERN = re.compile(r"type\s+(\w+)\s*=\s*(.+?)(?:\n\n|\Z)", re.DOTALL)


# =============================================================================
# DATA TYPES
# =============================================================================


@dataclass
class FastFlag:
    """Represents a Roblox FastFlag."""

    name: str
    prefix: str  # FFlag, DFFlag, SFFlag, FInt, etc.
    source: str  # C++, Lua, etc.
    full_name: str  # Complete flag name including prefix

    @property
    def flag_type(self) -> str:
        """Get the type of flag (Flag, Int, String, Log)."""
        if "Int" in self.prefix:
            return "Integer"
        elif "String" in self.prefix:
            return "String"
        elif "Log" in self.prefix:
            return "Log"
        return "Boolean"


@dataclass
class LuauGlobal:
    """Represents a Luau global function or type."""

    name: str
    kind: str  # function, type, variable
    signature: str
    description: str = ""


@dataclass
class ClassMetadata:
    """Extra metadata for a class from ReflectionMetadata.xml."""

    name: str
    explorer_order: int = 0
    explorer_image_index: int = 0
    class_category: str = ""
    preferred_parent: str = ""
    is_browsable: bool = True
    summary: str = ""


@dataclass
class CloudEndpoint:
    """Represents an Open Cloud API endpoint."""

    path: str
    method: str
    operation_id: str
    summary: str
    description: str
    tags: list[str] = field(default_factory=list)
    parameters: list[dict[str, Any]] = field(default_factory=list)
    request_body: dict[str, Any] | None = None
    responses: dict[str, Any] = field(default_factory=dict)
    security: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DataType:
    """Represents a Roblox data type (Vector3, CFrame, Color3, etc.)."""

    name: str
    summary: str = ""
    description: str = ""
    constructors: list[dict[str, Any]] = field(default_factory=list)
    constants: list[dict[str, Any]] = field(default_factory=list)
    properties: list[dict[str, Any]] = field(default_factory=list)
    methods: list[dict[str, Any]] = field(default_factory=list)
    math_operations: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Library:
    """Represents a Luau standard library (math, string, table, etc.)."""

    name: str
    summary: str = ""
    description: str = ""
    properties: list[dict[str, Any]] = field(default_factory=list)
    functions: list[dict[str, Any]] = field(default_factory=list)


class MemberInfo(TypedDict, total=False):
    """Type definition for API member."""

    MemberType: str
    Name: str
    ValueType: dict[str, str] | None
    ReturnType: dict[str, str] | None
    Parameters: list[dict[str, Any]]
    Security: dict[str, str] | str
    Tags: list[str]
    ThreadSafety: str
    Default: Any


class ClassInfo(TypedDict, total=False):
    """Type definition for API class."""

    Name: str
    Superclass: str
    Members: list[MemberInfo]
    Tags: list[str]
    MemoryCategory: str


class EnumItem(TypedDict):
    """Type definition for enum item."""

    Name: str
    Value: int


class EnumInfo(TypedDict):
    """Type definition for enum."""

    Name: str
    Items: list[EnumItem]


class ApiDump(TypedDict):
    """Type definition for API dump structure."""

    Version: int
    Classes: list[ClassInfo]
    Enums: list[EnumInfo]


class DataLoader:
    """
    Lazy-loading data manager with in-memory caching.

    Data is loaded on first access and cached for subsequent calls.
    """

    def __init__(self, cache_dir: Path, language: str = "en-us"):
        self.cache_dir = Path(cache_dir)
        self.language = language

        # In-memory caches (lazy loaded)
        self._api_dump: ApiDump | None = None
        self._api_docs: dict[str, Any] | None = None
        self._full_api_dump: ApiDump | None = None

        # Pre-computed lookups (built after first load)
        self._class_map: dict[str, ClassInfo] | None = None
        self._enum_map: dict[str, EnumInfo] | None = None
        self._member_map: dict[str, dict[str, MemberInfo]] | None = None
        self._inheritance_map: dict[str, list[str]] | None = None
        self._docs_map: dict[str, dict[str, Any]] | None = None

        # Extended data caches
        self._fflags: list[FastFlag] | None = None
        self._fflag_map: dict[str, FastFlag] | None = None
        self._luau_globals: list[LuauGlobal] | None = None
        self._class_metadata: dict[str, ClassMetadata] | None = None
        self._cloud_endpoints: list[CloudEndpoint] | None = None
        self._cloud_endpoint_map: dict[str, CloudEndpoint] | None = None
        self._luau_docs: dict[str, str] | None = None

        # DataType and Library caches
        self._datatypes: list[DataType] | None = None
        self._datatype_map: dict[str, DataType] | None = None
        self._libraries: list[Library] | None = None
        self._library_map: dict[str, Library] | None = None

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

    def _load_json(self, path: Path) -> dict[str, Any] | None:
        """Load JSON file with error handling."""
        if not path.exists():
            logger.warning(f"File not found: {path}")
            return None
        try:
            return orjson.loads(path.read_bytes())
        except Exception as e:
            logger.error(f"Failed to load {path}: {e}")
            return None

    def get_api_dump(self) -> ApiDump | None:
        """Get API dump with lazy loading."""
        if self._api_dump is None:
            data = self._load_json(self.api_dump_path)
            if data:
                self._api_dump = data  # type: ignore
                self._build_lookups()
        return self._api_dump

    def get_api_docs(self) -> dict[str, Any] | None:
        """Get API docs with lazy loading."""
        if self._api_docs is None:
            self._api_docs = self._load_json(self.api_docs_path)
            if self._api_docs:
                self._build_docs_map()
        return self._api_docs

    def get_full_api_dump(self) -> ApiDump | None:
        """Get full API dump (with default values)."""
        if self._full_api_dump is None:
            data = self._load_json(self.full_api_dump_path)
            if data:
                self._full_api_dump = data  # type: ignore
        return self._full_api_dump

    def _build_lookups(self) -> None:
        """Build pre-computed lookup tables for fast access."""
        if self._api_dump is None:
            return

        # Build class map
        self._class_map = {}
        self._member_map = {}
        self._inheritance_map = {}

        for cls in self._api_dump.get("Classes", []):
            name = cls.get("Name", "")
            if name:
                self._class_map[name] = cls
                self._class_map[name.lower()] = cls  # Case-insensitive lookup

                # Build member map
                self._member_map[name] = {}
                for member in cls.get("Members", []):
                    member_name = member.get("Name", "")
                    if member_name:
                        self._member_map[name][member_name] = member
                        self._member_map[name][member_name.lower()] = member

        # Build inheritance map
        for cls in self._api_dump.get("Classes", []):
            name = cls.get("Name", "")
            if name:
                self._inheritance_map[name] = self._get_inheritance_chain(name)

        # Build enum map
        self._enum_map = {}
        for enum in self._api_dump.get("Enums", []):
            name = enum.get("Name", "")
            if name:
                self._enum_map[name] = enum
                self._enum_map[name.lower()] = enum

        logger.info(
            f"Built lookups: {len(self._class_map) // 2} classes, {len(self._enum_map) // 2} enums"
        )

    def _build_docs_map(self) -> None:
        """Build documentation lookup map."""
        if self._api_docs is None:
            return

        self._docs_map = {}

        # API docs structure varies, try to normalize
        for key, value in self._api_docs.items():
            if isinstance(value, dict):
                self._docs_map[key] = value
                self._docs_map[key.lower()] = value

    def _get_inheritance_chain(self, class_name: str) -> list[str]:
        """Get full inheritance chain for a class."""
        chain = []
        current = class_name
        seen = set()

        while current and current != "<<<ROOT>>>" and current not in seen:
            seen.add(current)
            chain.append(current)
            cls = self._class_map.get(current) if self._class_map else None
            if cls:
                current = cls.get("Superclass", "")
            else:
                break

        return chain

    def get_class(self, name: str) -> ClassInfo | None:
        """Get class by name (case-insensitive)."""
        self.get_api_dump()  # Ensure loaded
        if self._class_map:
            return self._class_map.get(name) or self._class_map.get(name.lower())
        return None

    def get_all_classes(self) -> list[ClassInfo]:
        """Get all classes."""
        dump = self.get_api_dump()
        return dump.get("Classes", []) if dump else []

    def get_enum(self, name: str) -> EnumInfo | None:
        """Get enum by name (case-insensitive)."""
        self.get_api_dump()  # Ensure loaded
        if self._enum_map:
            return self._enum_map.get(name) or self._enum_map.get(name.lower())
        return None

    def get_all_enums(self) -> list[EnumInfo]:
        """Get all enums."""
        dump = self.get_api_dump()
        return dump.get("Enums", []) if dump else []

    def get_member(
        self, class_name: str, member_name: str, include_inherited: bool = True
    ) -> MemberInfo | None:
        """Get a specific member from a class, optionally including inherited members."""
        self.get_api_dump()  # Ensure loaded
        if not self._member_map:
            return None

        # First check direct class members
        class_members = self._member_map.get(class_name) or self._member_map.get(
            class_name.lower(), {}
        )
        member = class_members.get(member_name) or class_members.get(member_name.lower())

        if member:
            return member

        # If not found and include_inherited, check parent classes
        if include_inherited:
            chain = self.get_inheritance(class_name)
            for parent_class in chain[1:]:  # Skip the class itself
                parent_members = self._member_map.get(parent_class, {})
                member = parent_members.get(member_name) or parent_members.get(member_name.lower())
                if member:
                    return member

        return None

    def get_class_members(
        self, class_name: str, member_type: str | None = None
    ) -> list[MemberInfo]:
        """Get all members of a class, optionally filtered by type."""
        cls = self.get_class(class_name)
        if not cls:
            return []

        members = cls.get("Members", [])
        if member_type:
            members = [m for m in members if m.get("MemberType") == member_type]

        return members

    def get_inheritance(self, class_name: str) -> list[str]:
        """Get inheritance chain for a class."""
        self.get_api_dump()  # Ensure loaded
        if self._inheritance_map:
            return self._inheritance_map.get(class_name, [])
        return self._get_inheritance_chain(class_name)

    def get_subclasses(self, class_name: str) -> list[str]:
        """Get all direct subclasses of a class."""
        dump = self.get_api_dump()
        if not dump:
            return []

        subclasses = []
        for cls in dump.get("Classes", []):
            if cls.get("Superclass") == class_name:
                subclasses.append(cls.get("Name", ""))

        return subclasses

    def get_class_doc(self, class_name: str) -> dict[str, Any] | None:
        """Get documentation for a class."""
        self.get_api_docs()  # Ensure loaded
        if self._docs_map:
            return self._docs_map.get(class_name) or self._docs_map.get(class_name.lower())
        return None

    def get_services(self) -> list[ClassInfo]:
        """Get all service classes."""
        classes = self.get_all_classes()
        return [c for c in classes if "Service" in c.get("Tags", [])]

    def get_deprecated_classes(self) -> list[ClassInfo]:
        """Get all deprecated classes."""
        classes = self.get_all_classes()
        return [c for c in classes if "Deprecated" in c.get("Tags", [])]

    def is_deprecated(self, class_name: str, member_name: str | None = None) -> bool:
        """Check if a class or member is deprecated."""
        if member_name:
            member = self.get_member(class_name, member_name)
            if member:
                return "Deprecated" in member.get("Tags", [])
            return False
        else:
            cls = self.get_class(class_name)
            if cls:
                return "Deprecated" in cls.get("Tags", [])
            return False

    def get_version(self) -> int | None:
        """Get API dump version."""
        dump = self.get_api_dump()
        return dump.get("Version") if dump else None

    def clear_cache(self) -> None:
        """Clear in-memory caches (forces reload on next access)."""
        self._api_dump = None
        self._api_docs = None
        self._full_api_dump = None
        self._class_map = None
        self._enum_map = None
        self._member_map = None
        self._inheritance_map = None
        self._docs_map = None
        # Extended data
        self._fflags = None
        self._fflag_map = None
        self._luau_globals = None
        self._class_metadata = None
        self._cloud_endpoints = None
        self._cloud_endpoint_map = None
        self._luau_docs = None
        # DataTypes and Libraries
        self._datatypes = None
        self._datatype_map = None
        self._libraries = None
        self._library_map = None
        logger.info("Cleared in-memory cache")

    def set_language(self, language: str) -> None:
        """Change documentation language."""
        from src.data.syncer import AVAILABLE_LANGUAGES

        if language in AVAILABLE_LANGUAGES:
            self.language = language
            self._api_docs = None  # Clear docs cache
            self._docs_map = None
            logger.info(f"Switched language to {language}")

    # =========================================================================
    # FASTFLAGS (FVariables)
    # =========================================================================

    def _load_fflags(self) -> None:
        """Parse FVariables.txt and build FastFlag list."""
        if not self.fvariables_path.exists():
            logger.warning("FVariables.txt not found")
            self._fflags = []
            self._fflag_map = {}
            return

        self._fflags = []
        self._fflag_map = {}

        # Known prefixes for FastFlags
        prefixes = [
            "DFFlag",
            "FFlag",
            "SFFlag",
            "FInt",
            "DFInt",
            "SFInt",
            "FString",
            "DFString",
            "SFString",
            "FLog",
            "DFLog",
            "SFLog",
        ]

        try:
            content = self.fvariables_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue

                # Use pre-compiled pattern
                match = _FVARIABLES_PATTERN.match(line)
                if match:
                    source = match.group(1)
                    full_name = match.group(2)

                    # Extract prefix and name
                    prefix = ""
                    name = full_name
                    for p in sorted(prefixes, key=len, reverse=True):
                        if full_name.startswith(p):
                            prefix = p
                            name = full_name[len(p) :]
                            break

                    flag = FastFlag(
                        name=name,
                        prefix=prefix,
                        source=source,
                        full_name=full_name,
                    )
                    self._fflags.append(flag)
                    self._fflag_map[full_name] = flag
                    self._fflag_map[full_name.lower()] = flag

            logger.info(f"Loaded {len(self._fflags)} FastFlags")
        except Exception as e:
            logger.error(f"Failed to parse FVariables.txt: {e}")
            self._fflags = []
            self._fflag_map = {}

    def get_all_fflags(self) -> list[FastFlag]:
        """Get all FastFlags."""
        if self._fflags is None:
            self._load_fflags()
        return self._fflags or []

    def get_fflag(self, name: str) -> FastFlag | None:
        """Get a specific FastFlag by name (case-insensitive)."""
        if self._fflag_map is None:
            self._load_fflags()
        if self._fflag_map:
            return self._fflag_map.get(name) or self._fflag_map.get(name.lower())
        return None

    def search_fflags(self, query: str, limit: int = 50) -> list[FastFlag]:
        """Search FastFlags by name."""
        flags = self.get_all_fflags()
        query_lower = query.lower()

        # Score and filter
        results = []
        for flag in flags:
            # Check full name and extracted name
            if query_lower in flag.full_name.lower():
                # Score: exact match > prefix match > contains
                if flag.full_name.lower() == query_lower:
                    score = 100
                elif flag.full_name.lower().startswith(query_lower):
                    score = 50
                else:
                    score = 10
                results.append((score, flag))

        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        return [flag for _, flag in results[:limit]]

    # =========================================================================
    # LUAU GLOBAL TYPES
    # =========================================================================

    def _load_luau_globals(self) -> None:
        """Parse LuauTypes.d.luau and extract global definitions."""
        if not self.luau_types_path.exists():
            logger.warning("LuauTypes.d.luau not found")
            self._luau_globals = []
            return

        self._luau_globals = []

        try:
            content = self.luau_types_path.read_text(encoding="utf-8")

            # Extract functions (using pre-compiled pattern)
            for match in _FUNCTION_PATTERN.finditer(content):
                name = match.group(1)
                params = match.group(2).strip()
                return_type = match.group(3) or "void"
                signature = f"function {name}({params}): {return_type.strip()}"
                self._luau_globals.append(
                    LuauGlobal(
                        name=name,
                        kind="function",
                        signature=signature,
                    )
                )

            # Extract variables (using pre-compiled pattern)
            for match in _VAR_PATTERN.finditer(content):
                name = match.group(1)
                type_str = match.group(2).strip()
                # Skip if already matched as function
                if any(g.name == name for g in self._luau_globals):
                    continue
                self._luau_globals.append(
                    LuauGlobal(
                        name=name,
                        kind="variable",
                        signature=f"{name}: {type_str}",
                    )
                )

            # Extract types (using pre-compiled pattern)
            for match in _TYPE_PATTERN.finditer(content):
                name = match.group(1)
                type_def = match.group(2).strip()[:200]  # Truncate long definitions
                self._luau_globals.append(
                    LuauGlobal(
                        name=name,
                        kind="type",
                        signature=f"type {name} = {type_def}",
                    )
                )

            logger.info(f"Loaded {len(self._luau_globals)} Luau globals")
        except Exception as e:
            logger.error(f"Failed to parse LuauTypes.d.luau: {e}")
            self._luau_globals = []

    def get_luau_globals(self) -> list[LuauGlobal]:
        """Get all Luau global functions and types."""
        if self._luau_globals is None:
            self._load_luau_globals()
        return self._luau_globals or []

    def get_luau_global(self, name: str) -> LuauGlobal | None:
        """Get a specific Luau global by name."""
        globals_list = self.get_luau_globals()
        name_lower = name.lower()
        for g in globals_list:
            if g.name.lower() == name_lower:
                return g
        return None

    # =========================================================================
    # CLASS METADATA (ReflectionMetadata.xml)
    # =========================================================================

    def _load_class_metadata(self) -> None:
        """Parse ReflectionMetadata.xml and extract class metadata."""
        if not self.reflection_metadata_path.exists():
            logger.warning("ReflectionMetadata.xml not found")
            self._class_metadata = {}
            return

        self._class_metadata = {}

        try:
            tree = ET.parse(self.reflection_metadata_path)
            root = tree.getroot()

            # Find all Item elements with class="ReflectionMetadataClass"
            for item in root.iter("Item"):
                if item.get("class") == "ReflectionMetadataClass":
                    props = {}
                    for prop in item.findall(".//Properties/*"):
                        prop_name = prop.get("name", "")
                        prop_value = prop.text or ""
                        props[prop_name] = prop_value

                    name = props.get("Name", "")
                    if name:
                        self._class_metadata[name] = ClassMetadata(
                            name=name,
                            explorer_order=int(props.get("ExplorerOrder", 0) or 0),
                            explorer_image_index=int(props.get("ExplorerImageIndex", 0) or 0),
                            class_category=props.get("ClassCategory", ""),
                            preferred_parent=props.get("PreferredParent", ""),
                            is_browsable=props.get("Browsable", "true").lower() == "true",
                            summary=props.get("summary", ""),
                        )

            logger.info(f"Loaded metadata for {len(self._class_metadata)} classes")
        except Exception as e:
            logger.error(f"Failed to parse ReflectionMetadata.xml: {e}")
            self._class_metadata = {}

    def get_class_metadata(self, class_name: str) -> ClassMetadata | None:
        """Get extra metadata for a class."""
        if self._class_metadata is None:
            self._load_class_metadata()
        if self._class_metadata:
            return self._class_metadata.get(class_name)
        return None

    def get_all_class_metadata(self) -> dict[str, ClassMetadata]:
        """Get all class metadata."""
        if self._class_metadata is None:
            self._load_class_metadata()
        return self._class_metadata or {}

    # =========================================================================
    # OPEN CLOUD API (OpenAPI spec)
    # =========================================================================

    def _load_cloud_api(self) -> None:
        """Parse openapi.json and extract endpoints."""
        if not self.openapi_path.exists():
            logger.warning("openapi.json not found")
            self._cloud_endpoints = []
            self._cloud_endpoint_map = {}
            return

        self._cloud_endpoints = []
        self._cloud_endpoint_map = {}

        try:
            data = self._load_json(self.openapi_path)
            if not data:
                return

            paths = data.get("paths", {})

            for path, methods in paths.items():
                if not isinstance(methods, dict):
                    continue

                for method, operation in methods.items():
                    if method.startswith("x-") or not isinstance(operation, dict):
                        continue

                    operation_id = operation.get("operationId", f"{method}_{path}")

                    endpoint = CloudEndpoint(
                        path=path,
                        method=method.upper(),
                        operation_id=operation_id,
                        summary=operation.get("summary", ""),
                        description=operation.get("description", ""),
                        tags=operation.get("tags", []),
                        parameters=operation.get("parameters", []),
                        request_body=operation.get("requestBody"),
                        responses=operation.get("responses", {}),
                        security=operation.get("security", []),
                    )

                    self._cloud_endpoints.append(endpoint)
                    self._cloud_endpoint_map[operation_id] = endpoint
                    self._cloud_endpoint_map[operation_id.lower()] = endpoint

            logger.info(f"Loaded {len(self._cloud_endpoints)} Open Cloud endpoints")
        except Exception as e:
            logger.error(f"Failed to parse openapi.json: {e}")
            self._cloud_endpoints = []
            self._cloud_endpoint_map = {}

    def get_all_cloud_endpoints(self) -> list[CloudEndpoint]:
        """Get all Open Cloud API endpoints."""
        if self._cloud_endpoints is None:
            self._load_cloud_api()
        return self._cloud_endpoints or []

    def get_cloud_endpoint(self, operation_id: str) -> CloudEndpoint | None:
        """Get a specific endpoint by operation ID."""
        if self._cloud_endpoint_map is None:
            self._load_cloud_api()
        if self._cloud_endpoint_map:
            return self._cloud_endpoint_map.get(operation_id) or self._cloud_endpoint_map.get(
                operation_id.lower()
            )
        return None

    def search_cloud_endpoints(self, query: str, limit: int = 25) -> list[CloudEndpoint]:
        """Search Open Cloud endpoints."""
        endpoints = self.get_all_cloud_endpoints()
        query_lower = query.lower()

        results = []
        for endpoint in endpoints:
            score = 0
            # Check operation ID
            if query_lower in endpoint.operation_id.lower():
                score += 50
            # Check path
            if query_lower in endpoint.path.lower():
                score += 30
            # Check summary
            if query_lower in endpoint.summary.lower():
                score += 20
            # Check tags
            for tag in endpoint.tags:
                if query_lower in tag.lower():
                    score += 15
            # Check description
            if query_lower in endpoint.description.lower():
                score += 10

            if score > 0:
                results.append((score, endpoint))

        results.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in results[:limit]]

    def get_cloud_api_tags(self) -> list[str]:
        """Get all unique tags from Open Cloud API."""
        endpoints = self.get_all_cloud_endpoints()
        tags = set()
        for ep in endpoints:
            tags.update(ep.tags)
        return sorted(tags)

    # =========================================================================
    # LUAU LANGUAGE DOCUMENTATION
    # =========================================================================

    def _load_luau_docs(self) -> None:
        """Load all Luau documentation markdown files."""
        if not self.luau_docs_dir.exists():
            logger.warning("Luau docs directory not found")
            self._luau_docs = {}
            return

        self._luau_docs = {}

        try:
            for md_file in self.luau_docs_dir.glob("*.md"):
                topic = md_file.stem
                content = md_file.read_text(encoding="utf-8")
                self._luau_docs[topic] = content
                self._luau_docs[topic.lower()] = content

            logger.info(f"Loaded {len(self._luau_docs) // 2} Luau documentation topics")
        except Exception as e:
            logger.error(f"Failed to load Luau docs: {e}")
            self._luau_docs = {}

    def get_luau_doc(self, topic: str) -> str | None:
        """Get Luau documentation for a topic."""
        if self._luau_docs is None:
            self._load_luau_docs()
        if self._luau_docs:
            return self._luau_docs.get(topic) or self._luau_docs.get(topic.lower())
        return None

    def get_luau_doc_topics(self) -> list[str]:
        """Get list of available Luau documentation topics."""
        if self._luau_docs is None:
            self._load_luau_docs()
        if self._luau_docs:
            # Return unique topics (not lowercase duplicates)
            return sorted(
                set(k for k in self._luau_docs.keys() if not k.islower() or k == k.lower())
            )
        return []

    # =========================================================================
    # ROBLOX DATATYPES (Vector3, CFrame, Color3, etc.)
    # =========================================================================

    def _load_yaml(self, path: Path) -> dict[str, Any] | None:
        """Load YAML file with error handling."""
        if not path.exists():
            return None
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Failed to load {path}: {e}")
            return None

    def _load_datatypes(self) -> None:
        """Parse datatype YAML files and build DataType list."""
        if not self.datatypes_dir.exists():
            logger.warning("datatypes directory not found")
            self._datatypes = []
            self._datatype_map = {}
            return

        self._datatypes = []
        self._datatype_map = {}

        try:
            for yaml_file in self.datatypes_dir.glob("*.yaml"):
                data = self._load_yaml(yaml_file)
                if not data:
                    continue

                name = data.get("name", yaml_file.stem)
                dt = DataType(
                    name=name,
                    summary=data.get("summary", ""),
                    description=data.get("description", ""),
                    constructors=data.get("constructors", []),
                    constants=data.get("constants", []),
                    properties=data.get("properties", []),
                    methods=data.get("methods", []),
                    math_operations=data.get("math_operations", []),
                )
                self._datatypes.append(dt)
                self._datatype_map[name] = dt
                self._datatype_map[name.lower()] = dt

            logger.info(f"Loaded {len(self._datatypes)} DataTypes")
        except Exception as e:
            logger.error(f"Failed to load datatypes: {e}")
            self._datatypes = []
            self._datatype_map = {}

    def get_all_datatypes(self) -> list[DataType]:
        """Get all Roblox DataTypes."""
        if self._datatypes is None:
            self._load_datatypes()
        return self._datatypes or []

    def get_datatype(self, name: str) -> DataType | None:
        """Get a specific DataType by name (case-insensitive)."""
        if self._datatype_map is None:
            self._load_datatypes()
        if self._datatype_map:
            return self._datatype_map.get(name) or self._datatype_map.get(name.lower())
        return None

    # =========================================================================
    # LUAU STANDARD LIBRARIES (math, string, table, etc.)
    # =========================================================================

    def _load_libraries(self) -> None:
        """Parse library YAML files and build Library list."""
        if not self.libraries_dir.exists():
            logger.warning("libraries directory not found")
            self._libraries = []
            self._library_map = {}
            return

        self._libraries = []
        self._library_map = {}

        try:
            for yaml_file in self.libraries_dir.glob("*.yaml"):
                data = self._load_yaml(yaml_file)
                if not data:
                    continue

                name = data.get("name", yaml_file.stem)
                lib = Library(
                    name=name,
                    summary=data.get("summary", ""),
                    description=data.get("description", ""),
                    properties=data.get("properties", []),
                    functions=data.get("functions", []),
                )
                self._libraries.append(lib)
                self._library_map[name] = lib
                self._library_map[name.lower()] = lib

            logger.info(f"Loaded {len(self._libraries)} Libraries")
        except Exception as e:
            logger.error(f"Failed to load libraries: {e}")
            self._libraries = []
            self._library_map = {}

    def get_all_libraries(self) -> list[Library]:
        """Get all Luau standard libraries."""
        if self._libraries is None:
            self._load_libraries()
        return self._libraries or []

    def get_library(self, name: str) -> Library | None:
        """Get a specific library by name (case-insensitive)."""
        if self._library_map is None:
            self._load_libraries()
        if self._library_map:
            return self._library_map.get(name) or self._library_map.get(name.lower())
        return None

    def get_library_function(self, library_name: str, function_name: str) -> dict[str, Any] | None:
        """Get a specific function from a library."""
        lib = self.get_library(library_name)
        if not lib:
            return None

        # Search in functions list
        fn_lower = function_name.lower()
        for func in lib.functions:
            func_name = func.get("name", "")
            # Function names are like "math.abs", so check both full and short name
            if (
                func_name.lower() == fn_lower
                or func_name.lower() == f"{library_name.lower()}.{fn_lower}"
            ):
                return func
            # Also check just the function part after the dot
            if "." in func_name and func_name.split(".", 1)[1].lower() == fn_lower:
                return func

        return None
