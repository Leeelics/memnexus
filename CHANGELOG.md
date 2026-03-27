# Changelog

All notable changes to MemNexus will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [Unreleased]

### ✨ New Features

- **Global Memory** - Cross-project knowledge aggregation
  - Register multiple projects: `memnexus global-register <name>`
  - Search across all projects: `memnexus global-search <query>`
  - Sync projects to global: `memnexus global-sync`
  - List registered projects: `memnexus global-list`
  - Unregister projects: `memnexus global-unregister <name>`
  - Global config stored in `~/.memnexus/global/`
  - Project metadata (tags, description, last synced)
  - Filter search by project or across all

### 🔧 Changes

- **Dependency Cleanup** - Removed unused dependencies for faster installation
  - Removed: sqlalchemy, asyncpg, alembic, aiofiles, asyncio-mqtt, pandas
  - Removed: python-dotenv, structlog, tenacity, cryptography, python-jose, passlib
  - Removed: tree-sitter, tree-sitter-python (AST parsing used instead)
  - Removed: websockets (not used)
  - Removed: pydantic-settings (not used)
  - Moved redis to optional dependencies (`pip install memnexus[sync]`)
  - Updated sync.py as experimental/frozen feature

## [0.3.0] - 2026-03-27

### ✨ New Features

- **Incremental Indexing** - Major performance improvement for large projects
  - Git history: Only index new commits since last run
  - Code: Only index modified files (based on content hash and mtime)
  - Index state stored in `.memnexus/index_state.json`
  - New CLI flags: `--incremental/--full` and `--reset`
  - New CLI command: `memnexus reset --git/--code/--all`

- **Lightweight TF-IDF Embedding** - Zero-dependency embedding (no more zero vectors!)
  - Default: TF-IDF embedding (pure Python, no ML libraries)
  - Optional: Hash embedder (even simpler)
  - External API support: OpenAI (best quality)
  - Configurable via `embedding.method` in config.yaml

### 🔧 Technical Details

- Added `IndexStateManager` class for tracking index state
- Added `FileIndexState` and `GitIndexState` dataclasses
- Added `embedder.py` with multiple embedding strategies:
  - `TfidfEmbedder`: Lightweight, keyword-based (default)
  - `HashEmbedder`: Ultra-lightweight feature hashing
  - `ExternalApiEmbedder`: OpenAI API support (best quality)
- Modified `index_git_history()` to support `incremental` parameter
- Modified `index_codebase()` to support `incremental` parameter
- Added `reset_index()` method to `CodeMemory` class
- Updated `get_stats()` to include index state statistics
- Updated config template with embedding configuration

## [0.2.2] - 2026-03-27

### 🐛 Bug Fixes

- **CLI Entry Point**: Fixed missing `main` function in `cli.py` that caused `ImportError` when running `memnexus` command after installation via `uv tool install`
  - The `pyproject.toml` defined entry point as `memnexus.cli:main` but the function was missing
  - Added `main()` function that calls `app()` to properly expose the CLI entry point

## [0.2.1] - 2026-03-26

### 🐛 Bug Fixes

- Version bump for packaging fixes

## [0.2.0] - 2026-03-25

### 🎉 First Public Release - Code Memory for AI Programming Tools

This is the first public release of MemNexus as a **Code Memory** tool for AI programming assistants.

### ✨ New Features

#### Core Memory System
- **CodeMemory** - Main entry point for library usage
- **Vector Storage** - LanceDB-based semantic search
- **MemoryStore** - Add, search, and manage memory entries

#### Git Integration
- **GitMemoryExtractor** - Extract commit history from Git repositories
- **Commit Indexing** - Index commit messages, authors, and file changes
- **Semantic Search** - Search Git history with natural language
- **File History** - Get complete history for specific files

#### Code Parsing
- **CodeParser** - Parse Python code using AST
- **Symbol Extraction** - Extract functions, classes, and methods
- **Import Analysis** - Extract and analyze import statements
- **CodeChunker** - Create embeddable code chunks with context
- **Signature Extraction** - Capture function signatures with type annotations

#### CLI Interface
- **memnexus init** - Initialize project for memory tracking
- **memnexus index** - Index Git history and/or code
- **memnexus search** - Search project memory
- **memnexus status** - Check project indexing status
- **memnexus server** - Start HTTP API server

#### HTTP API
- `GET /health` - Health check
- `GET /stats` - Project statistics
- `GET /api/v1/search` - Search all memories
- `POST /api/v1/memory` - Add memory entry
- `POST /api/v1/git/index` - Index Git history
- `GET /api/v1/git/search` - Search Git history
- `POST /api/v1/code/index` - Index codebase
- `GET /api/v1/code/search` - Search code symbols
- `GET /api/v1/code/symbol/{name}` - Find specific symbol

#### Kimi CLI Plugin
- **Plugin Support** - Native integration with Kimi CLI 1.25.0+
- **6 Tools** - memory_search, memory_store, memory_status, memory_index, find_symbol, get_file_history
- **Slash Commands** - `/memory search`, `/memory store`, `/memory status`, etc.

### 🐛 Known Issues

- Code parsing currently only supports Python
- TypeScript/JavaScript support coming in next release
- Large repositories may require tuning batch sizes

### 📁 New Files

```
src/memnexus/
├── __init__.py              # Main exports
├── code_memory.py           # Core CodeMemory class
├── cli.py                   # CLI interface
├── server.py                # FastAPI server
├── memory/
│   ├── git.py              # Git integration
│   ├── code.py             # Code parsing
│   └── store.py            # Vector storage
└── scripts/
    └── kimi_plugin.py      # Kimi CLI plugin

~/.kimi/plugins/memnexus/
├── plugin.json             # Plugin manifest
└── SKILL.md                # Plugin documentation
```

### 📊 Statistics

- Total Lines of Code: ~5,000
- Python Files: 15
- Test Coverage: Core functionality tested
- Documentation: Complete user guides

## [0.1.0] - 2026-02-20 (Internal)

### Initial Prototype

> **Note:** This was an internal prototype with a different focus (Multi-Agent Orchestration). 
> The project was significantly refactored for the 0.2.0 release.

Original features:
- Multi-Agent Collaboration Orchestration
- ACP Protocol implementation
- LlamaIndex RAG Pipeline
- React Frontend
- Task Scheduler and Intervention System

[0.2.0]: https://github.com/Leeelics/MemNexus/releases/tag/v0.2.0
[0.1.0]: https://github.com/Leeelics/MemNexus/releases/tag/v0.1.0
