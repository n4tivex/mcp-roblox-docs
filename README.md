# MCP Roblox Docs

[![PyPI version](https://badge.fury.io/py/mcp-roblox-docs.svg)](https://pypi.org/project/mcp-roblox-docs/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive MCP (Model Context Protocol) server providing complete Roblox ecosystem documentation. Query API references, FastFlags, Open Cloud REST API, Luau language docs, and DevForum - all from your AI assistant.

## Features

- **Always Up-to-Date**: Automatically syncs from Roblox's official sources
- **27 Specialized Tools**: Complete coverage of the Roblox ecosystem
- **Full-Text Search**: Search across 850+ classes, 35,000+ members, 14,000+ FastFlags, 865 Cloud API endpoints
- **DataTypes & Libraries**: 44 DataTypes (Vector3, CFrame, etc.) and 11 Luau standard libraries
- **Multi-Language**: Supports 15 languages including English, Indonesian, Japanese, Korean, Chinese
- **DevForum Integration**: Search community discussions with intelligent caching
- **Open Cloud API**: Full REST API documentation with auth, parameters, and response schemas
- **FastFlags Reference**: Search and explore 14,000+ engine flags
- **Luau Language Docs**: Complete language reference and globals
- **Zero Cost**: 100% free, no API keys required
- **Optimized**: Lazy loading, in-memory caching, DevForum result caching
- **Fast Sync**: Parallel downloads (7-10x faster), retry logic, HTTP compression

## Installation

### Quick Start (Recommended)

The easiest way to use this MCP server is via `uvx`:

```bash
uvx mcp-roblox-docs
```

No installation, no setup - it just works!

### From Source

```bash
git clone https://github.com/nhattamgithub/mcp-roblox-docs
cd mcp-roblox-docs
uv sync
uv run mcp-roblox-docs
```

## Configuration

### Claude Desktop

Add to your Claude Desktop config:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "roblox-docs": {
      "command": "uvx",
      "args": ["mcp-roblox-docs"]
    }
  }
}
```

### Cursor / Other MCP Clients

```json
{
  "mcpServers": {
    "roblox-docs": {
      "command": "uvx",
      "args": ["mcp-roblox-docs"]
    }
  }
}
```

Or if running from source:

```json
{
  "command": "uv",
  "args": ["--directory", "/path/to/mcp-roblox-docs", "run", "mcp-roblox-docs"]
}
```

## Available Tools (27 Total)

### Core API Tools

| Tool | Description |
|------|-------------|
| `roblox_search` | Full-text search across all Roblox API |
| `roblox_get_class` | Get complete class info with members, metadata, category |
| `roblox_get_member` | Get detailed member info (property/method/event) |
| `roblox_get_enum` | Get enum with all values |
| `roblox_check_deprecated` | Check deprecation status + get alternatives |
| `roblox_list_services` | List all 290+ Roblox services |

### Extended API Tools

| Tool | Description |
|------|-------------|
| `roblox_get_inheritance` | Get class hierarchy and subclasses |
| `roblox_search_devforum` | Search DevForum threads (cached) |
| `roblox_recent_changes` | Get API version info |
| `roblox_list_enums` | List all 500+ available enums |
| `roblox_sync` | Force sync data or change language |
| `roblox_health` | Get server status, stats, and diagnostics |

### FastFlags Tools

| Tool | Description |
|------|-------------|
| `roblox_search_fflags` | Search 14,000+ FastFlags by name |
| `roblox_get_fflag` | Get specific FastFlag details and type |
| `roblox_list_fflag_prefixes` | Explain FastFlag prefix types (FFlag, FInt, DFFlag, etc.) |

### Luau Globals Tools

| Tool | Description |
|------|-------------|
| `roblox_get_luau_globals` | List all Luau global functions and types |
| `roblox_get_luau_global` | Get specific global details (print, typeof, etc.) |

### Open Cloud API Tools

| Tool | Description |
|------|-------------|
| `roblox_search_cloud_api` | Search 865 REST API endpoints |
| `roblox_get_cloud_endpoint` | Get endpoint details (auth, params, responses) |
| `roblox_list_cloud_apis` | List all Open Cloud API categories |

### Luau Language Tools

| Tool | Description |
|------|-------------|
| `roblox_get_luau_topic` | Get Luau language documentation |
| `roblox_list_luau_topics` | List available Luau doc topics |

### DataType Tools

| Tool | Description |
|------|-------------|
| `roblox_get_datatype` | Get datatype documentation (Vector3, CFrame, Color3, UDim2, etc.) |
| `roblox_list_datatypes` | List all 44 available Roblox datatypes |

### Library Tools

| Tool | Description |
|------|-------------|
| `roblox_get_library` | Get Luau library documentation (math, string, table, etc.) |
| `roblox_get_library_function` | Get specific function details (math.clamp, string.split, etc.) |
| `roblox_list_libraries` | List all 11 Luau standard libraries |

## MCP Resources (v3.3.0+)

Resources provide direct URI-based access to documentation:

| URI Pattern | Description |
|-------------|-------------|
| `roblox://class/{name}` | Get class documentation (e.g., `roblox://class/TweenService`) |
| `roblox://enum/{name}` | Get enum values (e.g., `roblox://enum/EasingStyle`) |
| `roblox://datatype/{name}` | Get datatype docs (e.g., `roblox://datatype/Vector3`) |
| `roblox://library/{name}` | Get library docs (e.g., `roblox://library/math`) |
| `roblox://luau/{topic}` | Get Luau language docs (e.g., `roblox://luau/tables`) |

## MCP Prompts (v3.3.0+)

Prompts provide reusable workflow templates:

| Prompt | Description |
|--------|-------------|
| `explain-api` | Generate a detailed explanation of a Roblox API class |
| `debug-deprecation` | Help migrate from deprecated APIs with alternatives |
| `code-review` | Review Roblox Luau code for best practices |
| `learn-service` | Learn about a Roblox service with examples |

## Examples

### Search for APIs
```
User: How do I animate something smoothly?
AI: [uses roblox_search("tween animation")]
→ TweenService, TweenBase, Tween, EasingStyle...
```

### Get Class Info
```
User: Tell me about TweenService
AI: [uses roblox_get_class("TweenService")]
→ Complete class info with Create(), GetValue(), SmoothDamp() methods
   Category: Animation, Preferred Parent: game
```

### Check Deprecation
```
User: Is BodyPosition deprecated?
AI: [uses roblox_check_deprecated("BodyPosition")]
→ Yes, deprecated. Use AlignPosition (constraint-based) instead.
```

### Search FastFlags
```
User: What flags control physics?
AI: [uses roblox_search_fflags("physics")]
→ FIntPhysicsMaxSteps, DFFlagPhysicsDebug, FFlagPhysicsOptimized...
```

### Get Cloud API Endpoint
```
User: How do I publish a message to a topic?
AI: [uses roblox_search_cloud_api("publish message")]
→ POST /v1/universes/{universeId}/topics/{topic}
   Auth: API Key with messaging-service:publish scope
```

### Get Luau Globals
```
User: What built-in functions does Luau have?
AI: [uses roblox_get_luau_globals()]
→ print, warn, error, typeof, select, pairs, ipairs, next...
```

### Luau Language Docs
```
User: How do type annotations work in Luau?
AI: [uses roblox_get_luau_topic("type-annotations")]
→ Complete guide on type syntax, generics, type inference...
```

### Search DevForum
```
User: How do people optimize memory in Roblox?
AI: [uses roblox_search_devforum("memory optimization")]
→ Links to relevant community discussions (cached for 1 hour)
```

### Get DataType Info
```
User: How do I create a Vector3?
AI: [uses roblox_get_datatype("Vector3")]
→ Vector3.new(x, y, z), Vector3.one, Vector3.zero
   Properties: X, Y, Z, Magnitude, Unit
   Methods: Cross, Dot, Lerp, Angle...
```

### Get Library Function
```
User: How does math.clamp work?
AI: [uses roblox_get_library_function("math", "clamp")]
→ math.clamp(x, min, max): number
   Returns x clamped between min and max
```

## Data Sources

All data is fetched from free, public sources:

| Source | Content |
|--------|---------|
| [Roblox-Client-Tracker](https://github.com/MaximumADHD/Roblox-Client-Tracker) | Classes, members, enums, FastFlags, Luau types, metadata |
| [Roblox Creator Docs](https://github.com/Roblox/creator-docs) | Open Cloud API, Luau language documentation |
| [DevForum](https://devforum.roblox.com) | Community discussions |

### Data Stats

| Data Type | Count |
|-----------|-------|
| Classes | 850+ |
| Members | 35,000+ |
| Enums | 500+ |
| FastFlags | 14,000+ |
| Luau Globals | 87 |
| Cloud Endpoints | 865 |
| Luau Doc Topics | 20 |
| DataTypes | 44 |
| Libraries | 11 |

## Supported Languages

Switch documentation language with `roblox_sync(language="id-id")`:

- `en-us` - English (default)
- `id-id` - Indonesian
- `ja-jp` - Japanese
- `ko-kr` - Korean
- `zh-cn` - Chinese (Simplified)
- `zh-tw` - Chinese (Traditional)
- `de-de` - German
- `es-es` - Spanish
- `fr-fr` - French
- `it-it` - Italian
- `pt-br` - Portuguese (Brazil)
- `ru-ru` - Russian
- `th-th` - Thai
- `tr-tr` - Turkish
- `vi-vn` - Vietnamese

## Cache Location

Data is cached in your system's standard cache directory:

- **Windows:** `%LOCALAPPDATA%\mcp-roblox-docs\`
- **macOS:** `~/Library/Caches/mcp-roblox-docs/`
- **Linux:** `~/.cache/mcp-roblox-docs/`

Cache is automatically updated when Roblox releases new API versions.

## Development

```bash
# Clone the repository
git clone https://github.com/nhattamgithub/mcp-roblox-docs
cd mcp-roblox-docs

# Install dependencies
uv sync

# Run the server locally
uv run mcp-roblox-docs

# Test tool count
uv run python -c "from src.server import mcp; print('Tools:', len(mcp._tool_manager._tools))"

# Build for distribution
uv build

# Publish to PyPI
uv publish
```

## Changelog

### v3.3.0 (2026-01-25)
**Full MCP Primitives Implementation**
- Added MCP Resources (5 resource templates):
  - `roblox://class/{name}` - Direct access to class documentation
  - `roblox://enum/{name}` - Direct access to enum values
  - `roblox://datatype/{name}` - Direct access to datatype docs
  - `roblox://library/{name}` - Direct access to library docs
  - `roblox://luau/{topic}` - Direct access to Luau language docs
- Added MCP Prompts (4 workflow templates):
  - `explain-api` - Explain a Roblox API class in detail
  - `debug-deprecation` - Help migrate from deprecated APIs
  - `code-review` - Review Roblox Luau code
  - `learn-service` - Learn about a Roblox service
- Added 2-minute timeout for sync operations
- Now implements all 3 MCP primitives: Tools, Resources, and Prompts

### v3.2.0 (2026-01-25)
**MCP Best Practices & Quality Improvements**
- Added `roblox_health` tool for server status, stats, and diagnostics
- Wired up input validation in all 17 tools that accept user input
- Added configurable logging via `MCP_ROBLOX_DOCS_LOG_LEVEL` env var
- Added `py.typed` marker file for PEP 561 compliance
- Improved DevForum disk cache to clean up expired entries on save
- Fixed duplicate regex patterns in loader
- Updated USER_AGENT to match current version
- Now 27 tools total

### v3.1.0 (2026-01-25)
**Developer Experience & Search Improvements**
- Fuzzy search with typo tolerance (e.g., "Tweenservce" → "TweenService")
- Persistent DevForum cache (survives server restarts)
- Added `fuzzy` parameter to `roblox_search` tool (default: True)
- Fixed TypedDict type hints in formatter for better type safety
- Added pytest test suite (56 tests for validation, search, cache)
- Added dev dependencies: pytest, pytest-asyncio

### v3.0.1 (2026-01-25)
- Fixed changelog year (2025 -> 2026)

### v3.0.0 (2026-01-25)
**Performance & Reliability Release**
- Parallel downloads with semaphore (7-10x faster sync)
- Retry logic with exponential backoff (3 attempts)
- HTTP compression support (gzip, deflate)
- Pre-compiled regex patterns (faster parsing)
- DataTypes/Libraries now searchable via `roblox_search`
- DevForum rate limiting (prevents 429 errors)
- Input validation module for security

### v2.1.0 (2026-01-25)
- Added DataTypes documentation (44 types: Vector3, CFrame, Color3, UDim2, TweenInfo, etc.)
- Added Luau Libraries documentation (11 libraries: math, string, table, task, etc.)
- Added 5 new tools: `roblox_get_datatype`, `roblox_list_datatypes`, `roblox_get_library`, `roblox_get_library_function`, `roblox_list_libraries`
- Expanded from 21 to 26 tools

### v2.0.0 (2026-01-25)
- Added FastFlags support (14,000+ flags from FVariables.txt)
- Added Luau globals (87 built-in functions/types)
- Added Open Cloud REST API (865 endpoints from openapi.json)
- Added Luau language documentation (20 topics)
- Added class metadata (categories, icons, preferred parents)
- Added DevForum caching (1 hour TTL)
- Enhanced deprecation alternatives (40+ class, 30+ member mappings)
- Expanded from 11 to 21 tools

### v1.0.1
- Initial stable release
- Core API documentation tools
- DevForum search integration
- Multi-language support

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

- [Roblox-Client-Tracker](https://github.com/MaximumADHD/Roblox-Client-Tracker) by MaximumADHD
- [Roblox Creator Docs](https://github.com/Roblox/creator-docs) by Roblox
- [MCP Protocol](https://modelcontextprotocol.io/) by Anthropic
