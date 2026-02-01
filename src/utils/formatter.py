"""
Output Formatter - Formats API data for readable output.

Provides consistent, well-formatted output for all tools.

v3.1.0: Fixed type hints to use TypedDict types from loader
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.data.loader import (
        FastFlag,
        LuauGlobal,
        ClassMetadata,
        CloudEndpoint,
        DataType,
        Library,
        ClassInfo,
        MemberInfo,
        EnumInfo,
    )


def format_class(
    cls: "ClassInfo",
    docs: dict[str, Any] | None = None,
    include_members: bool = True,
    member_limit: int = 50,
) -> str:
    """Format a class for display."""
    name = cls.get("Name", "Unknown")
    superclass = cls.get("Superclass", "")
    tags = cls.get("Tags", [])
    members = cls.get("Members", [])

    lines = []

    # Header
    lines.append(f"CLASS: {name}")
    if superclass and superclass != "<<<ROOT>>>":
        lines.append(f"Inherits: {superclass}")

    # Tags
    if tags:
        tag_str = ", ".join(tags)
        lines.append(f"Tags: {tag_str}")

    # Description from docs
    if docs:
        desc = docs.get("description", "")
        if desc:
            lines.append("")
            lines.append("DESCRIPTION:")
            # Wrap description
            words = desc.split()
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 > 80:
                    lines.append(current_line)
                    current_line = word
                else:
                    current_line = f"{current_line} {word}".strip()
            if current_line:
                lines.append(current_line)

    if include_members and members:
        # Group members by type
        properties = [m for m in members if m.get("MemberType") == "Property"]
        methods = [m for m in members if m.get("MemberType") in ("Method", "Function")]
        events = [m for m in members if m.get("MemberType") == "Event"]
        callbacks = [m for m in members if m.get("MemberType") == "Callback"]

        if properties:
            lines.append("")
            lines.append(f"PROPERTIES ({len(properties)}):")
            for prop in properties[:member_limit]:
                lines.append(format_property(prop))

        if methods:
            lines.append("")
            lines.append(f"METHODS ({len(methods)}):")
            for method in methods[:member_limit]:
                lines.append(format_method(method))

        if events:
            lines.append("")
            lines.append(f"EVENTS ({len(events)}):")
            for event in events[:member_limit]:
                lines.append(format_event(event))

        if callbacks:
            lines.append("")
            lines.append(f"CALLBACKS ({len(callbacks)}):")
            for callback in callbacks[:member_limit]:
                lines.append(format_callback(callback))

    # Documentation link
    lines.append("")
    lines.append(f"DOCS: https://create.roblox.com/docs/reference/engine/classes/{name}")

    return "\n".join(lines)


def format_property(prop: "MemberInfo") -> str:
    """Format a property member."""
    name = prop.get("Name", "Unknown")
    value_type = prop.get("ValueType", {})
    type_name = (
        value_type.get("Name", "unknown") if isinstance(value_type, dict) else str(value_type)
    )
    tags = prop.get("Tags", [])

    tag_str = ""
    if tags:
        important_tags = [
            t for t in tags if t in ["ReadOnly", "Deprecated", "NotReplicated", "Hidden"]
        ]
        if important_tags:
            tag_str = f" [{', '.join(important_tags)}]"

    security = prop.get("Security", {})
    if isinstance(security, dict):
        read_sec = security.get("Read", "None")
        write_sec = security.get("Write", "None")
        if read_sec != "None" or write_sec != "None":
            tag_str += f" (Security: R={read_sec}, W={write_sec})"

    return f"  {name}: {type_name}{tag_str}"


def format_method(method: "MemberInfo") -> str:
    """Format a method member."""
    name = method.get("Name", "Unknown")
    params = method.get("Parameters", [])
    return_type = method.get("ReturnType", {})
    return_name = return_type.get("Name", "void") if isinstance(return_type, dict) else "void"
    tags = method.get("Tags", [])

    # Format parameters
    param_parts = []
    for p in params:
        p_name = p.get("Name", "arg")
        p_type = p.get("Type", {})
        p_type_name = p_type.get("Name", "any") if isinstance(p_type, dict) else "any"
        param_parts.append(f"{p_name}: {p_type_name}")

    param_str = ", ".join(param_parts)

    tag_str = ""
    if "Deprecated" in tags:
        tag_str = " [Deprecated]"
    if "Yields" in tags:
        tag_str += " [Yields]"

    return f"  {name}({param_str}) -> {return_name}{tag_str}"


def format_event(event: "MemberInfo") -> str:
    """Format an event member."""
    name = event.get("Name", "Unknown")
    params = event.get("Parameters", [])
    tags = event.get("Tags", [])

    # Format parameters
    param_parts = []
    for p in params:
        p_name = p.get("Name", "arg")
        p_type = p.get("Type", {})
        p_type_name = p_type.get("Name", "any") if isinstance(p_type, dict) else "any"
        param_parts.append(f"{p_name}: {p_type_name}")

    param_str = ", ".join(param_parts) if param_parts else ""

    tag_str = ""
    if "Deprecated" in tags:
        tag_str = " [Deprecated]"

    return f"  {name}({param_str}){tag_str}"


def format_callback(callback: "MemberInfo") -> str:
    """Format a callback member."""
    name = callback.get("Name", "Unknown")
    params = callback.get("Parameters", [])
    return_type = callback.get("ReturnType", {})
    return_name = return_type.get("Name", "void") if isinstance(return_type, dict) else "void"

    param_parts = []
    for p in params:
        p_name = p.get("Name", "arg")
        p_type = p.get("Type", {})
        p_type_name = p_type.get("Name", "any") if isinstance(p_type, dict) else "any"
        param_parts.append(f"{p_name}: {p_type_name}")

    param_str = ", ".join(param_parts)

    return f"  {name}({param_str}) -> {return_name}"


def format_enum(enum: "EnumInfo") -> str:
    """Format an enum for display."""
    name = enum.get("Name", "Unknown")
    items = enum.get("Items", [])

    lines = []
    lines.append(f"ENUM: {name}")
    lines.append(f"Values ({len(items)} items):")
    lines.append("")

    # Sort by value
    sorted_items = sorted(items, key=lambda x: x.get("Value", 0))

    for item in sorted_items:
        item_name = item.get("Name", "Unknown")
        item_value = item.get("Value", 0)
        lines.append(f"  {item_name} = {item_value}")

    lines.append("")
    lines.append(f"DOCS: https://create.roblox.com/docs/reference/engine/enums/{name}")

    return "\n".join(lines)


def format_member(member: "MemberInfo", class_name: str, docs: dict[str, Any] | None = None) -> str:
    """Format a single member with full details."""
    name = member.get("Name", "Unknown")
    member_type = member.get("MemberType", "Unknown")
    tags = member.get("Tags", [])
    security = member.get("Security", {})

    lines = []

    # Header
    lines.append(f"{member_type.upper()}: {class_name}.{name}")

    # Tags
    if tags:
        lines.append(f"Tags: {', '.join(tags)}")

    # Type-specific details
    if member_type == "Property":
        value_type = member.get("ValueType", {})
        type_name = (
            value_type.get("Name", "unknown") if isinstance(value_type, dict) else str(value_type)
        )
        lines.append(f"Type: {type_name}")

        if isinstance(security, dict):
            lines.append(f"Read: {security.get('Read', 'None')}")
            lines.append(f"Write: {security.get('Write', 'None')}")

        default = member.get("Default")
        if default is not None:
            lines.append(f"Default: {default}")

    elif member_type in ("Method", "Function"):
        params = member.get("Parameters", [])
        return_type = member.get("ReturnType", {})
        return_name = return_type.get("Name", "void") if isinstance(return_type, dict) else "void"

        lines.append(f"Returns: {return_name}")

        if params:
            lines.append("Parameters:")
            for p in params:
                p_name = p.get("Name", "arg")
                p_type = p.get("Type", {})
                p_type_name = p_type.get("Name", "any") if isinstance(p_type, dict) else "any"
                p_default = p.get("Default")
                default_str = f" = {p_default}" if p_default is not None else ""
                lines.append(f"  {p_name}: {p_type_name}{default_str}")

        if "Yields" in tags:
            lines.append("Note: This method yields (async)")

    elif member_type == "Event":
        params = member.get("Parameters", [])
        if params:
            lines.append("Event Parameters:")
            for p in params:
                p_name = p.get("Name", "arg")
                p_type = p.get("Type", {})
                p_type_name = p_type.get("Name", "any") if isinstance(p_type, dict) else "any"
                lines.append(f"  {p_name}: {p_type_name}")

    # Description from docs
    if docs:
        desc = docs.get(name, {}).get("description", "")
        if desc:
            lines.append("")
            lines.append("DESCRIPTION:")
            lines.append(desc[:500])

    # Deprecation warning
    if "Deprecated" in tags:
        lines.append("")
        lines.append("WARNING: This member is deprecated!")

    lines.append("")
    lines.append(
        f"DOCS: https://create.roblox.com/docs/reference/engine/classes/{class_name}#{name}"
    )

    return "\n".join(lines)


def format_deprecation(
    name: str,
    is_class: bool,
    is_deprecated: bool,
    class_name: str | None = None,
    tags: list[str] | None = None,
    alternatives: list[str] | None = None,
) -> str:
    """Format deprecation status."""
    lines = []

    if is_class:
        full_name = name
    else:
        full_name = f"{class_name}.{name}" if class_name else name

    if is_deprecated:
        lines.append(f"DEPRECATED: {full_name}")
        lines.append("")
        lines.append("Status: This API is deprecated and should not be used in new code.")

        if alternatives:
            lines.append("")
            lines.append("Recommended Alternatives:")
            for alt in alternatives:
                lines.append(f"  - {alt}")

        if tags:
            other_tags = [t for t in tags if t != "Deprecated"]
            if other_tags:
                lines.append(f"Other Tags: {', '.join(other_tags)}")
    else:
        lines.append(f"NOT DEPRECATED: {full_name}")
        lines.append("")
        lines.append("Status: This API is current and safe to use.")

        if tags:
            lines.append(f"Tags: {', '.join(tags)}")

    return "\n".join(lines)


def format_search_results(results: list[Any], query: str) -> str:
    """Format search results."""
    if not results:
        return f"No results found for '{query}'"

    lines = []
    lines.append(f"Search results for '{query}' ({len(results)} found):")
    lines.append("")

    for i, result in enumerate(results, 1):
        type_icon = {"class": "[C]", "member": "[M]", "enum": "[E]"}.get(result.type, "[?]")

        if result.class_name:
            name = f"{result.class_name}.{result.name}"
        else:
            name = result.name

        tag_str = ""
        if result.tags:
            important = [t for t in result.tags if t in ["Deprecated", "Service", "NotCreatable"]]
            if important:
                tag_str = f" [{', '.join(important)}]"

        lines.append(f"{i:2}. {type_icon} {name}{tag_str}")
        lines.append(f"      {result.description}")

    return "\n".join(lines)


def format_inheritance(class_name: str, chain: list[str], subclasses: list[str]) -> str:
    """Format class inheritance hierarchy."""
    lines = []

    lines.append(f"INHERITANCE: {class_name}")
    lines.append("")

    # Ancestors
    lines.append("Inheritance Chain (ancestors):")
    for i, ancestor in enumerate(chain):
        indent = "  " * i
        arrow = "-> " if i > 0 else ""
        marker = " <-- (this class)" if ancestor == class_name else ""
        lines.append(f"{indent}{arrow}{ancestor}{marker}")

    # Subclasses
    if subclasses:
        lines.append("")
        lines.append(f"Direct Subclasses ({len(subclasses)}):")
        for sub in sorted(subclasses)[:30]:
            lines.append(f"  - {sub}")
        if len(subclasses) > 30:
            lines.append(f"  ... and {len(subclasses) - 30} more")

    return "\n".join(lines)


def format_services(services: list["ClassInfo"]) -> str:
    """Format list of services."""
    lines = []

    lines.append(f"ROBLOX SERVICES ({len(services)} total)")
    lines.append("")
    lines.append("Services are singleton objects that provide core functionality:")
    lines.append("")

    for service in sorted(services, key=lambda s: s.get("Name", "")):
        name = service.get("Name", "Unknown")
        tags = service.get("Tags", [])

        tag_str = ""
        if "Deprecated" in tags:
            tag_str = " [Deprecated]"
        elif "NotCreatable" in tags:
            tag_str = " [Singleton]"

        lines.append(f"  - {name}{tag_str}")

    lines.append("")
    lines.append("Access services with: game:GetService('ServiceName')")

    return "\n".join(lines)


# =============================================================================
# EXTENDED DATA FORMATTERS
# =============================================================================


def format_fflag(flag: "FastFlag") -> str:
    """Format a single FastFlag for display."""
    lines = []

    lines.append(f"FASTFLAG: {flag.full_name}")
    lines.append("")
    lines.append(f"Prefix: {flag.prefix}")
    lines.append(f"Name: {flag.name}")
    lines.append(f"Type: {flag.flag_type}")
    lines.append(f"Source: {flag.source}")
    lines.append("")

    # Explain prefixes
    prefix_desc = {
        "FFlag": "Feature Flag (boolean, client-side)",
        "DFFlag": "Dynamic Feature Flag (boolean, can change at runtime)",
        "SFFlag": "Sync Feature Flag (boolean, synchronized)",
        "FInt": "Feature Integer (numeric value)",
        "DFInt": "Dynamic Feature Integer",
        "SFInt": "Sync Feature Integer",
        "FString": "Feature String (text value)",
        "DFString": "Dynamic Feature String",
        "FLog": "Feature Log (logging control)",
        "DFLog": "Dynamic Feature Log",
    }

    if flag.prefix in prefix_desc:
        lines.append(f"Prefix meaning: {prefix_desc[flag.prefix]}")

    lines.append("")
    lines.append("Note: FastFlags are internal Roblox settings. Use at your own risk.")
    lines.append('To use in Studio: game:SetFastFlagForTesting("FlagName", value)')

    return "\n".join(lines)


def format_fflag_search_results(flags: list["FastFlag"], query: str) -> str:
    """Format FastFlag search results."""
    if not flags:
        return f"No FastFlags found matching '{query}'"

    lines = []
    lines.append(f"FastFlag search results for '{query}' ({len(flags)} found):")
    lines.append("")

    # Group by prefix
    by_prefix: dict[str, list["FastFlag"]] = {}
    for flag in flags:
        prefix = flag.prefix or "Unknown"
        if prefix not in by_prefix:
            by_prefix[prefix] = []
        by_prefix[prefix].append(flag)

    for prefix in sorted(by_prefix.keys()):
        prefix_flags = by_prefix[prefix]
        lines.append(f"{prefix} ({len(prefix_flags)}):")
        for flag in prefix_flags[:20]:  # Limit per prefix
            lines.append(f"  - {flag.full_name}")
        if len(prefix_flags) > 20:
            lines.append(f"  ... and {len(prefix_flags) - 20} more")
        lines.append("")

    lines.append("Use roblox_get_fflag('FlagName') for details.")

    return "\n".join(lines)


def format_luau_globals(globals_list: list["LuauGlobal"], filter_kind: str | None = None) -> str:
    """Format Luau globals list."""
    if filter_kind:
        globals_list = [g for g in globals_list if g.kind == filter_kind]

    if not globals_list:
        return "No Luau globals found."

    lines = []
    lines.append(f"LUAU GLOBALS ({len(globals_list)} total)")
    lines.append("")

    # Group by kind
    by_kind: dict[str, list["LuauGlobal"]] = {}
    for g in globals_list:
        if g.kind not in by_kind:
            by_kind[g.kind] = []
        by_kind[g.kind].append(g)

    for kind in ["function", "variable", "type"]:
        if kind not in by_kind:
            continue
        items = by_kind[kind]
        kind_title = kind.upper() + "S"
        lines.append(f"{kind_title} ({len(items)}):")
        for item in items:
            lines.append(f"  {item.signature}")
        lines.append("")

    return "\n".join(lines)


def format_luau_global(global_item: "LuauGlobal") -> str:
    """Format a single Luau global."""
    lines = []

    kind_title = global_item.kind.upper()
    lines.append(f"LUAU {kind_title}: {global_item.name}")
    lines.append("")
    lines.append(f"Signature: {global_item.signature}")

    if global_item.description:
        lines.append("")
        lines.append("Description:")
        lines.append(global_item.description)

    return "\n".join(lines)


def format_class_with_metadata(
    cls: "ClassInfo",
    docs: dict[str, Any] | None = None,
    metadata: "ClassMetadata | None" = None,
    include_members: bool = True,
    member_limit: int = 50,
) -> str:
    """Format a class with extra metadata."""
    name = cls.get("Name", "Unknown")
    superclass = cls.get("Superclass", "")
    tags = cls.get("Tags", [])
    members = cls.get("Members", [])

    lines = []

    # Header
    lines.append(f"CLASS: {name}")
    if superclass and superclass != "<<<ROOT>>>":
        lines.append(f"Inherits: {superclass}")

    # Tags
    if tags:
        tag_str = ", ".join(tags)
        lines.append(f"Tags: {tag_str}")

    # Metadata
    if metadata:
        if metadata.class_category:
            lines.append(f"Category: {metadata.class_category}")
        if metadata.preferred_parent:
            lines.append(f"Preferred Parent: {metadata.preferred_parent}")
        if metadata.explorer_image_index:
            lines.append(f"Explorer Icon Index: {metadata.explorer_image_index}")
        if metadata.summary:
            lines.append(f"Summary: {metadata.summary}")

    # Description from docs
    if docs:
        desc = docs.get("description", "")
        if desc:
            lines.append("")
            lines.append("DESCRIPTION:")
            words = desc.split()
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 > 80:
                    lines.append(current_line)
                    current_line = word
                else:
                    current_line = f"{current_line} {word}".strip()
            if current_line:
                lines.append(current_line)

    if include_members and members:
        properties = [m for m in members if m.get("MemberType") == "Property"]
        methods = [m for m in members if m.get("MemberType") in ("Method", "Function")]
        events = [m for m in members if m.get("MemberType") == "Event"]
        callbacks = [m for m in members if m.get("MemberType") == "Callback"]

        if properties:
            lines.append("")
            lines.append(f"PROPERTIES ({len(properties)}):")
            for prop in properties[:member_limit]:
                lines.append(format_property(prop))

        if methods:
            lines.append("")
            lines.append(f"METHODS ({len(methods)}):")
            for method in methods[:member_limit]:
                lines.append(format_method(method))

        if events:
            lines.append("")
            lines.append(f"EVENTS ({len(events)}):")
            for event in events[:member_limit]:
                lines.append(format_event(event))

        if callbacks:
            lines.append("")
            lines.append(f"CALLBACKS ({len(callbacks)}):")
            for callback in callbacks[:member_limit]:
                lines.append(format_callback(callback))

    lines.append("")
    lines.append(f"DOCS: https://create.roblox.com/docs/reference/engine/classes/{name}")

    return "\n".join(lines)


def format_cloud_endpoint(endpoint: "CloudEndpoint") -> str:
    """Format a single Open Cloud API endpoint."""
    lines = []

    lines.append(f"OPEN CLOUD ENDPOINT: {endpoint.method} {endpoint.path}")
    lines.append("")

    if endpoint.summary:
        lines.append(f"Summary: {endpoint.summary}")

    if endpoint.tags:
        lines.append(f"Tags: {', '.join(endpoint.tags)}")

    lines.append(f"Operation ID: {endpoint.operation_id}")

    if endpoint.description:
        lines.append("")
        lines.append("DESCRIPTION:")
        # Truncate long descriptions
        desc = endpoint.description[:500]
        if len(endpoint.description) > 500:
            desc += "..."
        lines.append(desc)

    # Parameters
    if endpoint.parameters:
        lines.append("")
        lines.append("PARAMETERS:")
        for param in endpoint.parameters:
            name = param.get("name", "?")
            location = param.get("in", "?")
            required = param.get("required", False)
            schema = param.get("schema", {})
            param_type = schema.get("type", "any") if isinstance(schema, dict) else "any"
            req_str = " (required)" if required else ""
            lines.append(f"  {name}: {param_type} [{location}]{req_str}")

    # Request body
    if endpoint.request_body:
        lines.append("")
        lines.append("REQUEST BODY:")
        content = endpoint.request_body.get("content", {})
        for content_type, schema_info in content.items():
            lines.append(f"  Content-Type: {content_type}")
            if "schema" in schema_info:
                schema = schema_info["schema"]
                if "$ref" in schema:
                    ref = schema["$ref"].split("/")[-1]
                    lines.append(f"  Schema: {ref}")

    # Responses
    if endpoint.responses:
        lines.append("")
        lines.append("RESPONSES:")
        for code, response in endpoint.responses.items():
            desc = response.get("description", "") if isinstance(response, dict) else ""
            lines.append(f"  {code}: {desc}")

    # Security
    if endpoint.security:
        lines.append("")
        lines.append("AUTHENTICATION REQUIRED")

    lines.append("")
    lines.append("DOCS: https://create.roblox.com/docs/cloud/reference")

    return "\n".join(lines)


def format_cloud_search_results(endpoints: list["CloudEndpoint"], query: str) -> str:
    """Format Open Cloud API search results."""
    if not endpoints:
        return f"No Open Cloud endpoints found matching '{query}'"

    lines = []
    lines.append(f"Open Cloud API search results for '{query}' ({len(endpoints)} found):")
    lines.append("")

    # Group by tag
    by_tag: dict[str, list["CloudEndpoint"]] = {}
    for ep in endpoints:
        tag = ep.tags[0] if ep.tags else "Other"
        if tag not in by_tag:
            by_tag[tag] = []
        by_tag[tag].append(ep)

    for tag in sorted(by_tag.keys()):
        tag_endpoints = by_tag[tag]
        lines.append(f"{tag} ({len(tag_endpoints)}):")
        for ep in tag_endpoints[:10]:
            lines.append(f"  {ep.method:6} {ep.path}")
            if ep.summary:
                lines.append(f"         {ep.summary[:60]}")
        if len(tag_endpoints) > 10:
            lines.append(f"  ... and {len(tag_endpoints) - 10} more")
        lines.append("")

    lines.append("Use roblox_get_cloud_endpoint('operationId') for details.")

    return "\n".join(lines)


def format_luau_doc(topic: str, content: str) -> str:
    """Format Luau documentation topic."""
    lines = []

    lines.append(f"LUAU DOCUMENTATION: {topic}")
    lines.append("=" * 50)
    lines.append("")

    # The content is markdown, return as-is for readability
    lines.append(content)

    lines.append("")
    lines.append(f"DOCS: https://create.roblox.com/docs/luau/{topic}")

    return "\n".join(lines)


# =============================================================================
# DATATYPE FORMATTERS
# =============================================================================


def format_datatype(dt: "DataType") -> str:
    """Format a single DataType for display."""
    lines = []

    lines.append(f"DATATYPE: {dt.name}")
    lines.append("")

    if dt.summary:
        lines.append(f"Summary: {dt.summary.strip()}")

    if dt.description:
        lines.append("")
        lines.append("DESCRIPTION:")
        # Truncate very long descriptions
        desc = dt.description.strip()[:1000]
        if len(dt.description) > 1000:
            desc += "..."
        lines.append(desc)

    # Constructors
    if dt.constructors:
        lines.append("")
        lines.append(f"CONSTRUCTORS ({len(dt.constructors)}):")
        for ctor in dt.constructors:
            name = ctor.get("name", "Unknown")
            summary = ctor.get("summary", "")
            params = ctor.get("parameters", [])

            # Format parameters
            param_parts = []
            for p in params:
                p_name = p.get("name", "arg")
                p_type = p.get("type", "any")
                p_default = p.get("default")
                if p_default is not None:
                    param_parts.append(f"{p_name}: {p_type} = {p_default}")
                else:
                    param_parts.append(f"{p_name}: {p_type}")

            param_str = ", ".join(param_parts)
            lines.append(f"  {name}({param_str})")
            if summary:
                lines.append(f"    {summary.strip()[:80]}")

    # Constants
    if dt.constants:
        lines.append("")
        lines.append(f"CONSTANTS ({len(dt.constants)}):")
        for const in dt.constants:
            name = const.get("name", "Unknown")
            const_type = const.get("type", "")
            summary = const.get("summary", "")
            lines.append(f"  {name}: {const_type}")
            if summary:
                lines.append(f"    {summary.strip()[:80]}")

    # Properties
    if dt.properties:
        lines.append("")
        lines.append(f"PROPERTIES ({len(dt.properties)}):")
        for prop in dt.properties:
            name = prop.get("name", "Unknown")
            prop_type = prop.get("type", "any")
            summary = prop.get("summary", "")
            lines.append(f"  {name}: {prop_type}")
            if summary:
                lines.append(f"    {summary.strip()[:80]}")

    # Methods
    if dt.methods:
        lines.append("")
        lines.append(f"METHODS ({len(dt.methods)}):")
        for method in dt.methods:
            name = method.get("name", "Unknown")
            summary = method.get("summary", "")
            params = method.get("parameters", [])
            returns = method.get("returns", [])

            # Format parameters
            param_parts = []
            for p in params:
                p_name = p.get("name", "arg")
                p_type = p.get("type", "any")
                param_parts.append(f"{p_name}: {p_type}")

            param_str = ", ".join(param_parts)

            # Format returns
            return_str = "void"
            if returns:
                return_types = [r.get("type", "any") for r in returns]
                return_str = ", ".join(return_types)

            lines.append(f"  {name}({param_str}) -> {return_str}")
            if summary:
                lines.append(f"    {summary.strip()[:80]}")

    # Math operations
    if dt.math_operations:
        lines.append("")
        lines.append(f"MATH OPERATIONS ({len(dt.math_operations)}):")
        for op in dt.math_operations:
            operation = op.get("operation", "?")
            type_a = op.get("type_a", "?")
            type_b = op.get("type_b", "?")
            return_type = op.get("return_type", "?")
            lines.append(f"  {type_a} {operation} {type_b} -> {return_type}")

    lines.append("")
    lines.append(f"DOCS: https://create.roblox.com/docs/reference/engine/datatypes/{dt.name}")

    return "\n".join(lines)


def format_datatype_list(datatypes: list["DataType"]) -> str:
    """Format list of DataTypes."""
    if not datatypes:
        return "No DataTypes found."

    lines = []
    lines.append(f"ROBLOX DATATYPES ({len(datatypes)} total)")
    lines.append("")
    lines.append("DataTypes are fundamental value types used throughout the Roblox API:")
    lines.append("")

    # Sort alphabetically
    for dt in sorted(datatypes, key=lambda d: d.name):
        summary = dt.summary.strip()[:60] if dt.summary else ""
        if summary and not summary.endswith("."):
            summary = summary.split(".")[0]
        lines.append(f"  - {dt.name}")
        if summary:
            lines.append(f"      {summary}")

    lines.append("")
    lines.append("Use roblox_get_datatype('Name') for details.")

    return "\n".join(lines)


# =============================================================================
# LIBRARY FORMATTERS
# =============================================================================


def format_library(lib: "Library") -> str:
    """Format a single Library for display."""
    lines = []

    lines.append(f"LIBRARY: {lib.name}")
    lines.append("")

    if lib.summary:
        lines.append(f"Summary: {lib.summary.strip()}")

    if lib.description:
        lines.append("")
        lines.append("DESCRIPTION:")
        desc = lib.description.strip()[:1000]
        if len(lib.description) > 1000:
            desc += "..."
        lines.append(desc)

    # Properties/Constants
    if lib.properties:
        lines.append("")
        lines.append(f"PROPERTIES/CONSTANTS ({len(lib.properties)}):")
        for prop in lib.properties:
            name = prop.get("name", "Unknown")
            prop_type = prop.get("type", "any")
            summary = prop.get("summary", "")
            lines.append(f"  {name}: {prop_type}")
            if summary:
                lines.append(f"    {summary.strip()[:80]}")

    # Functions
    if lib.functions:
        lines.append("")
        lines.append(f"FUNCTIONS ({len(lib.functions)}):")
        for func in lib.functions:
            name = func.get("name", "Unknown")
            summary = func.get("summary", "")
            params = func.get("parameters", [])
            returns = func.get("returns", [])

            # Format parameters
            param_parts = []
            for p in params:
                p_name = p.get("name", "arg")
                p_type = p.get("type", "any")
                param_parts.append(f"{p_name}: {p_type}")

            param_str = ", ".join(param_parts)

            # Format returns
            return_str = "void"
            if returns:
                return_types = [r.get("type", "any") for r in returns]
                return_str = ", ".join(return_types)

            lines.append(f"  {name}({param_str}) -> {return_str}")
            if summary:
                lines.append(f"    {summary.strip()[:80]}")

    lines.append("")
    lines.append(f"DOCS: https://create.roblox.com/docs/reference/engine/libraries/{lib.name}")

    return "\n".join(lines)


def format_library_function(lib: "Library", func_name: str) -> str:
    """Format a specific library function."""
    lines = []

    # Find the function
    func = None
    fn_lower = func_name.lower()
    for f in lib.functions:
        name = f.get("name", "")
        if name.lower() == fn_lower or name.lower() == f"{lib.name.lower()}.{fn_lower}":
            func = f
            break
        if "." in name and name.split(".", 1)[1].lower() == fn_lower:
            func = f
            break

    if not func:
        return f"Function '{func_name}' not found in library '{lib.name}'"

    name = func.get("name", "Unknown")
    summary = func.get("summary", "")
    description = func.get("description", "")
    params = func.get("parameters", [])
    returns = func.get("returns", [])

    lines.append(f"FUNCTION: {name}")
    lines.append("")

    if summary:
        lines.append(f"Summary: {summary.strip()}")

    # Parameters
    if params:
        lines.append("")
        lines.append("PARAMETERS:")
        for p in params:
            p_name = p.get("name", "arg")
            p_type = p.get("type", "any")
            p_default = p.get("default")
            p_summary = p.get("summary", "")

            default_str = f" = {p_default}" if p_default is not None else ""
            lines.append(f"  {p_name}: {p_type}{default_str}")
            if p_summary:
                lines.append(f"    {p_summary.strip()}")

    # Returns
    if returns:
        lines.append("")
        lines.append("RETURNS:")
        for r in returns:
            r_type = r.get("type", "any")
            r_summary = r.get("summary", "")
            lines.append(f"  {r_type}")
            if r_summary:
                lines.append(f"    {r_summary.strip()}")

    # Full description
    if description:
        lines.append("")
        lines.append("DESCRIPTION:")
        lines.append(description.strip()[:1500])

    lines.append("")
    lines.append(f"DOCS: https://create.roblox.com/docs/reference/engine/libraries/{lib.name}")

    return "\n".join(lines)


def format_library_list(libraries: list["Library"]) -> str:
    """Format list of Libraries."""
    if not libraries:
        return "No Libraries found."

    lines = []
    lines.append(f"LUAU STANDARD LIBRARIES ({len(libraries)} total)")
    lines.append("")
    lines.append("These libraries provide built-in functions for common operations:")
    lines.append("")

    for lib in sorted(libraries, key=lambda l: l.name):
        func_count = len(lib.functions)
        prop_count = len(lib.properties)
        summary = lib.summary.strip()[:60] if lib.summary else ""

        lines.append(f"  - {lib.name} ({func_count} functions, {prop_count} properties)")
        if summary:
            lines.append(f"      {summary}")

    lines.append("")
    lines.append("Use roblox_get_library('name') for details.")
    lines.append(
        "Use roblox_get_library_function('library', 'function') for specific function docs."
    )

    return "\n".join(lines)
