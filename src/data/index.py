"""
Search Index - Full-text search across Roblox API.

Builds an inverted index for fast text search with simple scoring.

v3.0.0: Added support for DataTypes and Libraries in search
v3.1.0: Added fuzzy search with difflib for typo tolerance
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.data.loader import DataType, Library, ClassInfo, EnumInfo

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result."""

    type: str  # "class", "member", "enum", "datatype", "library"
    name: str
    class_name: str | None  # For members
    description: str
    score: float
    tags: list[str] = field(default_factory=list)
    member_type: str | None = None  # For members: Property, Method, Event, Callback


@dataclass
class SearchIndex:
    """
    Inverted index for full-text search.

    Index structure:
    - token -> [(type, name, class_name, score_boost), ...]
    """

    def __init__(self):
        self._index: dict[str, list[tuple[str, str, str | None, float]]] = defaultdict(list)
        self._class_data: dict[str, "ClassInfo"] = {}
        self._enum_data: dict[str, "EnumInfo"] = {}
        self._docs_data: dict[str, dict[str, Any]] = {}
        self._datatype_data: dict[str, "DataType"] = {}  # v3.0.0: DataType storage
        self._library_data: dict[str, "Library"] = {}  # v3.0.0: Library storage
        self._built = False

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into searchable terms."""
        if not text:
            return []

        # Split camelCase and PascalCase
        text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)

        # Split on non-alphanumeric
        tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())

        return tokens

    def _add_to_index(
        self,
        tokens: list[str],
        type_: str,
        name: str,
        class_name: str | None = None,
        score_boost: float = 1.0,
    ) -> None:
        """Add tokens to the inverted index."""
        for token in tokens:
            if len(token) >= 2:  # Skip very short tokens
                self._index[token].append((type_, name, class_name, score_boost))

    def build(
        self,
        classes: "list[ClassInfo]",
        enums: "list[EnumInfo]",
        docs: dict[str, Any] | None = None,
        datatypes: "list[DataType] | None" = None,
        libraries: "list[Library] | None" = None,
    ) -> None:
        """Build the search index from API data."""
        logger.info("Building search index...")

        self._index.clear()
        self._class_data.clear()
        self._enum_data.clear()
        self._datatype_data.clear()
        self._library_data.clear()
        self._docs_data = docs or {}

        # Index classes
        for cls in classes:
            name = cls.get("Name", "")
            if not name:
                continue

            self._class_data[name] = cls

            # Index class name (high boost)
            tokens = self._tokenize(name)
            self._add_to_index(tokens, "class", name, score_boost=3.0)

            # Index class description from docs
            if docs and name in docs:
                desc = docs.get(name, {}).get("description", "")
                if desc:
                    desc_tokens = self._tokenize(desc)
                    self._add_to_index(desc_tokens, "class", name, score_boost=1.0)

            # Index members
            for member in cls.get("Members", []):
                member_name = member.get("Name", "")
                if not member_name:
                    continue

                # Index member name (medium boost)
                member_tokens = self._tokenize(member_name)
                self._add_to_index(member_tokens, "member", member_name, name, score_boost=2.0)

                # Index by member type
                member_type = member.get("MemberType", "")
                if member_type:
                    self._add_to_index(
                        [member_type.lower()], "member", member_name, name, score_boost=1.5
                    )

        # Index enums
        for enum in enums:
            name = enum.get("Name", "")
            if not name:
                continue

            self._enum_data[name] = enum

            # Index enum name (high boost)
            tokens = self._tokenize(name)
            self._add_to_index(tokens, "enum", name, score_boost=3.0)

            # Index enum items
            for item in enum.get("Items", []):
                item_name = item.get("Name", "")
                if item_name:
                    item_tokens = self._tokenize(item_name)
                    self._add_to_index(item_tokens, "enum", name, score_boost=1.5)

        # Index datatypes (v3.0.0)
        if datatypes:
            for dt in datatypes:
                name = dt.name
                self._datatype_data[name] = dt

                # Index datatype name (high boost)
                tokens = self._tokenize(name)
                self._add_to_index(tokens, "datatype", name, score_boost=3.0)

                # Index summary
                if dt.summary:
                    summary_tokens = self._tokenize(dt.summary)
                    self._add_to_index(summary_tokens, "datatype", name, score_boost=1.0)

                # Index constructors
                for ctor in dt.constructors:
                    ctor_name = ctor.get("name", "")
                    if ctor_name:
                        ctor_tokens = self._tokenize(ctor_name)
                        self._add_to_index(ctor_tokens, "datatype", name, score_boost=1.5)

                # Index methods
                for method in dt.methods:
                    method_name = method.get("name", "")
                    if method_name:
                        method_tokens = self._tokenize(method_name)
                        self._add_to_index(method_tokens, "datatype", name, score_boost=1.5)

        # Index libraries (v3.0.0)
        if libraries:
            for lib in libraries:
                name = lib.name
                self._library_data[name] = lib

                # Index library name (high boost)
                tokens = self._tokenize(name)
                self._add_to_index(tokens, "library", name, score_boost=3.0)

                # Index summary
                if lib.summary:
                    summary_tokens = self._tokenize(lib.summary)
                    self._add_to_index(summary_tokens, "library", name, score_boost=1.0)

                # Index functions
                for func in lib.functions:
                    func_name = func.get("name", "")
                    if func_name:
                        # Functions are like "math.abs", extract just the function part
                        short_name = func_name.split(".")[-1] if "." in func_name else func_name
                        func_tokens = self._tokenize(short_name)
                        self._add_to_index(func_tokens, "library", name, score_boost=1.5)

        self._built = True
        logger.info(
            f"Index built: {len(self._index)} unique tokens, "
            f"{len(self._class_data)} classes, {len(self._enum_data)} enums, "
            f"{len(self._datatype_data)} datatypes, {len(self._library_data)} libraries"
        )

    def search(self, query: str, limit: int = 25) -> list[SearchResult]:
        """
        Search the index for matching results.

        Returns results sorted by relevance score.
        """
        if not self._built:
            logger.warning("Search index not built yet")
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return []

        # Accumulate scores
        scores: dict[tuple[str, str, str | None], float] = defaultdict(float)

        for token in tokens:
            # Exact match
            if token in self._index:
                for type_, name, class_name, boost in self._index[token]:
                    key = (type_, name, class_name)
                    scores[key] += boost * 2.0

            # Prefix match
            for indexed_token, entries in self._index.items():
                if indexed_token.startswith(token) and indexed_token != token:
                    for type_, name, class_name, boost in entries:
                        key = (type_, name, class_name)
                        scores[key] += boost * 0.5

        # Sort by score and build results
        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]

        results = []
        seen = set()  # Dedupe

        for (type_, name, class_name), score in sorted_items:
            key = (type_, name, class_name)
            if key in seen:
                continue
            seen.add(key)

            result = self._build_result(type_, name, class_name, score)
            if result:
                results.append(result)

        return results

    def _build_result(
        self, type_: str, name: str, class_name: str | None, score: float
    ) -> SearchResult | None:
        """Build a SearchResult from index data."""
        if type_ == "class":
            cls = self._class_data.get(name)
            if not cls:
                return None

            # Get description from docs
            desc = ""
            if name in self._docs_data:
                desc = self._docs_data[name].get("description", "")[:200]

            return SearchResult(
                type="class",
                name=name,
                class_name=None,
                description=desc or f"Class: {name}",
                score=score,
                tags=cls.get("Tags", []),
            )

        elif type_ == "member":
            if not class_name:
                return None
            cls = self._class_data.get(class_name)
            if not cls:
                return None

            # Find the member
            member = None
            for m in cls.get("Members", []):
                if m.get("Name") == name:
                    member = m
                    break

            if not member:
                return None

            member_type = member.get("MemberType", "")

            # Build description
            if member_type == "Property":
                value_type_obj = member.get("ValueType")
                value_type = value_type_obj.get("Name", "unknown") if value_type_obj else "unknown"
                desc = f"Property: {value_type}"
            elif member_type in ("Method", "Function"):
                params = member.get("Parameters", [])
                param_str = ", ".join(p.get("Name", "") for p in params)
                return_type_obj = member.get("ReturnType")
                return_type = return_type_obj.get("Name", "void") if return_type_obj else "void"
                desc = f"Method({param_str}) -> {return_type}"
            elif member_type == "Event":
                params = member.get("Parameters", [])
                param_str = ", ".join(p.get("Name", "") for p in params)
                desc = f"Event({param_str})"
            elif member_type == "Callback":
                desc = "Callback"
            else:
                desc = member_type or "Unknown"

            return SearchResult(
                type="member",
                name=name,
                class_name=class_name,
                description=desc,
                score=score,
                tags=member.get("Tags", []),
                member_type=member_type,
            )

        elif type_ == "enum":
            enum = self._enum_data.get(name)
            if not enum:
                return None

            item_count = len(enum.get("Items", []))

            return SearchResult(
                type="enum",
                name=name,
                class_name=None,
                description=f"Enum with {item_count} values",
                score=score,
                tags=[],
            )

        elif type_ == "datatype":
            dt = self._datatype_data.get(name)
            if not dt:
                return None

            desc = dt.summary[:200] if dt.summary else f"DataType: {name}"
            method_count = len(dt.methods)
            ctor_count = len(dt.constructors)

            return SearchResult(
                type="datatype",
                name=name,
                class_name=None,
                description=f"{desc} ({ctor_count} constructors, {method_count} methods)",
                score=score,
                tags=[],
            )

        elif type_ == "library":
            lib = self._library_data.get(name)
            if not lib:
                return None

            desc = lib.summary[:200] if lib.summary else f"Library: {name}"
            func_count = len(lib.functions)

            return SearchResult(
                type="library",
                name=name,
                class_name=None,
                description=f"{desc} ({func_count} functions)",
                score=score,
                tags=[],
            )

        return None

    def is_built(self) -> bool:
        """Check if index has been built."""
        return self._built

    def get_stats(self) -> dict[str, int]:
        """Get index statistics."""
        return {
            "unique_tokens": len(self._index),
            "classes": len(self._class_data),
            "enums": len(self._enum_data),
            "datatypes": len(self._datatype_data),
            "libraries": len(self._library_data),
            "total_entries": sum(len(v) for v in self._index.values()),
        }

    def _fuzzy_match(self, query: str, target: str, threshold: float = 0.6) -> float:
        """
        Calculate fuzzy match score between query and target.

        Uses SequenceMatcher for similarity ratio.
        Returns the ratio if above threshold, else 0.

        Args:
            query: Search query (lowercase)
            target: Target string to match against (lowercase)
            threshold: Minimum similarity ratio (0.0 to 1.0)

        Returns:
            Similarity ratio if >= threshold, else 0.0
        """
        ratio = SequenceMatcher(None, query, target).ratio()
        return ratio if ratio >= threshold else 0.0

    def fuzzy_search(
        self,
        query: str,
        limit: int = 25,
        threshold: float = 0.6,
    ) -> list[SearchResult]:
        """
        Search the index with fuzzy matching for typo tolerance.

        This is slower than regular search but more forgiving of typos.
        Uses difflib.SequenceMatcher for string similarity.

        Args:
            query: Search query (e.g., "Tweenservice" instead of "TweenService")
            limit: Maximum results to return
            threshold: Minimum similarity ratio (0.0 to 1.0, default 0.6)

        Returns:
            List of SearchResults sorted by fuzzy match score.
        """
        if not self._built:
            logger.warning("Search index not built yet")
            return []

        query_lower = query.lower().strip()
        if not query_lower:
            return []

        # Accumulate fuzzy scores
        scores: dict[tuple[str, str, str | None], float] = defaultdict(float)

        # Check against all indexed tokens
        for indexed_token, entries in self._index.items():
            fuzzy_score = self._fuzzy_match(query_lower, indexed_token, threshold)
            if fuzzy_score > 0:
                for type_, name, class_name, boost in entries:
                    key = (type_, name, class_name)
                    # Weight by both fuzzy score and index boost
                    scores[key] += fuzzy_score * boost

        # Also do direct name matching for classes/enums/datatypes/libraries
        # This catches cases where the query matches the full name
        for name in self._class_data.keys():
            score = self._fuzzy_match(query_lower, name.lower(), threshold)
            if score > 0:
                key = ("class", name, None)
                scores[key] = max(scores[key], score * 3.0)  # High boost for name match

        for name in self._enum_data.keys():
            score = self._fuzzy_match(query_lower, name.lower(), threshold)
            if score > 0:
                key = ("enum", name, None)
                scores[key] = max(scores[key], score * 3.0)

        for name in self._datatype_data.keys():
            score = self._fuzzy_match(query_lower, name.lower(), threshold)
            if score > 0:
                key = ("datatype", name, None)
                scores[key] = max(scores[key], score * 3.0)

        for name in self._library_data.keys():
            score = self._fuzzy_match(query_lower, name.lower(), threshold)
            if score > 0:
                key = ("library", name, None)
                scores[key] = max(scores[key], score * 3.0)

        # Sort by score and build results
        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]

        results = []
        seen = set()

        for (type_, name, class_name), score in sorted_items:
            key = (type_, name, class_name)
            if key in seen:
                continue
            seen.add(key)

            result = self._build_result(type_, name, class_name, score)
            if result:
                results.append(result)

        return results

    def search_with_fuzzy_fallback(
        self,
        query: str,
        limit: int = 25,
        fuzzy_threshold: float = 0.6,
    ) -> tuple[list[SearchResult], bool]:
        """
        Search with automatic fuzzy fallback if no exact results found.

        First tries exact/prefix matching. If no results, falls back to fuzzy search.

        Args:
            query: Search query
            limit: Maximum results to return
            fuzzy_threshold: Threshold for fuzzy matching fallback

        Returns:
            Tuple of (results, used_fuzzy) where used_fuzzy indicates if fuzzy was used.
        """
        # Try exact search first
        results = self.search(query, limit=limit)

        if results:
            return (results, False)

        # Fall back to fuzzy search
        fuzzy_results = self.fuzzy_search(query, limit=limit, threshold=fuzzy_threshold)
        return (fuzzy_results, True)
