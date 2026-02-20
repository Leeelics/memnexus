# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-02-20

### Added
- Initial project structure
- FastAPI server with WebSocket support
- Session management (create, list, get, delete)
- Agent management (add, list)
- CLI commands (server, web, session, agent, config)
- Configuration management with Pydantic Settings
- Documentation (README, PRD, Architecture, Protocol specs)
- Test suite with pytest

### Features
- Support for multiple CLI agents (Claude, Kimi, Codex)
- ACP (Agent Client Protocol) support
- MCP (Model Context Protocol) support (planned)
- Web dashboard (basic HTML)
- Real-time WebSocket updates

### Technical
- Python 3.12+ support
- uv for dependency management
- LanceDB for vector storage
- LlamaIndex for RAG pipeline
- FastAPI + WebSocket for API

[Unreleased]: https://github.com/Leeelics/MemNexus/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Leeelics/MemNexus/releases/tag/v0.1.0
