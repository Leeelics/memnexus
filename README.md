# MemNexus - Multi-Agent Collaboration System

<p align="center">
  <b>English</b> | <a href="README.zh.md">简体中文</a>
</p>

> **Multi-Agent Collaboration Orchestration System** - Breaking down memory silos between AI programming tools

<p align="center">
  <a href="#-project-overview"><img src="https://img.shields.io/badge/Phase-3%20Complete-blue?style=for-the-badge" alt="Phase 3 Complete"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.12+-green?style=for-the-badge&logo=python" alt="Python 3.12+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License"></a>
  <a href="https://github.com/Leeelics/MemNexus/releases"><img src="https://img.shields.io/github/v/release/Leeelics/MemNexus?style=for-the-badge" alt="Release"></a>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-documentation">Documentation</a> •
  <a href="#-api-reference">API</a> •
  <a href="#-license">License</a>
</p>

## 🎯 Project Overview

MemNexus is a local AI OS-level memory daemon designed to connect AI programming tools like Claude Code, Kimi CLI, and Codex, enabling:

- **Context Sharing** - Multiple agents share memory and see each other's outputs and code changes
- **Task Orchestration** - Architect → Backend → Frontend → Testing automation workflow
- **Real-time Monitoring** - Web Dashboard for viewing task status in real-time
- **Human Intervention** - Pause, adjust, and reassign tasks at critical points

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MemNexus Core                          │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   Session    │    Agent     │    Task      │    Memory      │
│  (Workspace) │ (AI Instance)│  (Task Unit) │   (Storage)    │
└──────────────┴──────────────┴──────────────┴────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌──────────┐
   │  ACP    │          │  RAG    │          │  React   │
   │ Protocol│          │ Pipeline│          │ Frontend │
   └─────────┘          └─────────┘          └──────────┘
```

## 🚀 Quick Start

### Installation

MemNexus uses [uv](https://github.com/astral-sh/uv) for fast, reliable Python package management.

```bash
# Clone repository
git clone https://github.com/Leeelics/MemNexus.git
cd MemNexus

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (recommended)
uv sync

# Or activate the virtual environment
source .venv/bin/activate

# Alternative: Using pip
pip install -e ".[dev]"
```

### Start Services

```bash
# Start backend service
memnexus server

# Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Create Your First Session

```bash
# Create session
memnexus session-create "My First Project"

# Connect an agent
memnexus acp-connect <session_id> --cli claude --name claude-backend
```

## 📖 Documentation

- [Getting Started](docs/GETTING_STARTED.md) - Step-by-step setup guide
- [Architecture Overview](docs/ARCHITECTURE.md) - System design and architecture
- [API Reference](docs/API.md) - Complete API documentation
- [CLI Guide](docs/CLI.md) - Command-line interface reference
- [Development Guide](docs/DEVELOPMENT.md) - Contributing and development
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- [ACP Protocol](docs/PROTOCOL_ACP.md) - ACP protocol specification
- [MCP Protocol](docs/PROTOCOL_MCP.md) - MCP protocol specification

## 📖 Usage Guide

### Phase 1: Basic Features

```bash
# CLI Wrapper mode
memnexus wrapper <session_id> <cli> [--name <name>]
memnexus agent-launch <session_id> <cli>

# Memory operations
memnexus memory-search <session_id> "query"
memnexus memory-stats
```

### Phase 2: Protocol & RAG

```bash
# ACP protocol connection
memnexus acp-connect <session_id> --cli claude
memnexus acp-connect <session_id> -c kimi -n kimi-agent

# RAG document processing
memnexus rag-ingest <session_id> <file_path>
memnexus rag-query <session_id> "query" -k 10

# Real-time sync monitoring
memnexus sync-watch <session_id>
```

### Phase 3: Orchestration & Intervention

```bash
# Multi-agent orchestration
memnexus orchestrate <session_id> --strategy parallel
memnexus plan-show <session_id>

# Human intervention
memnexus intervention-list <session_id>
memnexus intervention-resolve <id> -a approve
```

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | FastAPI + Uvicorn | Async web server and API |
| CLI Framework | Typer + Rich | Interactive command-line interface |
| Vector Database | LanceDB | Embedded vector + full-text search |
| RAG Pipeline | LlamaIndex | Document chunking and retrieval |
| Frontend | React + TypeScript + Tailwind | Modern web interface |
| State Management | Zustand | Frontend state management |
| Protocol | ACP (JSON-RPC) | Agent communication protocol |

## 📁 Project Structure

```
MemNexus/
├── src/memnexus/          # Python backend (6,352 lines)
│   ├── agents/            # Agent implementations
│   ├── core/              # Core functionality (Config, Session)
│   ├── memory/            # Memory system (Store, RAG, Sync)
│   ├── orchestrator/      # Orchestration system (Engine, Scheduler, Intervention)
│   ├── protocols/         # Protocol implementations (ACP)
│   ├── cli.py             # CLI entry point
│   └── server.py          # FastAPI server
├── frontend/              # React frontend
│   └── src/
│       ├── components/    # Reusable components
│       ├── pages/         # Page components
│       ├── services/      # API services
│       └── store/         # State management
├── docs/                  # Documentation
├── README.md              # This file
├── README.zh.md           # Chinese version
├── CHANGELOG.md           # Change log
├── CONTRIBUTING.md        # Contribution guide
├── SECURITY.md            # Security policy
└── pyproject.toml         # Project configuration
```

## 🔌 API Reference

### Sessions
- `GET /api/v1/sessions` - List all sessions
- `POST /api/v1/sessions` - Create session
- `GET /api/v1/sessions/{id}` - Get session details

### Agents
- `POST /api/v1/sessions/{id}/agents/connect` - ACP connection
- `POST /api/v1/sessions/{id}/agents/launch` - Launch agent

### Memory & RAG
- `GET /api/v1/sessions/{id}/memory` - Query memory
- `POST /api/v1/sessions/{id}/rag/query` - RAG query

### Orchestration
- `POST /api/v1/sessions/{id}/plan` - Create execution plan
- `POST /api/v1/sessions/{id}/execute` - Execute plan
- `GET /api/v1/sessions/{id}/interventions` - Get intervention list

### WebSocket
- `WS /ws` - Real-time updates
- `WS /ws/sync/{session_id}` - Memory sync

See [API.md](docs/API.md) for complete documentation.

## 📊 Development Phases

- ✅ **Phase 1** - Rapid Prototyping (CLI Wrapper + Shared Memory)
- ✅ **Phase 2** - Protocol Implementation (ACP + RAG + Real-time Sync)
- ✅ **Phase 3** - Full Product (Orchestrator + Intervention + React Frontend)

## 🤝 Contributing

1. Fork the project
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📝 License

MemNexus is licensed under the [MIT License](LICENSE).

```
MIT License

Copyright (c) 2026 Leeelics

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Why MIT License?

We chose the MIT License because it:
- ✅ Allows free use for personal and commercial projects
- ✅ Permits modification and distribution
- ✅ Provides liability protection
- ✅ Is simple and widely understood

## 📚 Documentation Index

- [Getting Started](docs/GETTING_STARTED.md) - Step-by-step setup guide
- [Architecture Overview](docs/ARCHITECTURE.md) - System design and architecture
- [API Reference](docs/API.md) - Complete API documentation
- [CLI Guide](docs/CLI.md) - Command-line interface reference
- [Development Guide](docs/DEVELOPMENT.md) - Contributing and development
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- [ACP Protocol](docs/PROTOCOL_ACP.md) - ACP protocol specification
- [MCP Protocol](docs/PROTOCOL_MCP.md) - MCP protocol specification

## 👤 Author

**Leeelics** - [GitHub](https://github.com/Leeelics)

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [LlamaIndex](https://www.llamaindex.ai/) - RAG framework
- [LanceDB](https://lancedb.github.io/lancedb/) - Vector database
- [React](https://react.dev/) - Frontend framework
- [Astral](https://astral.sh/) - uv package manager

---

<p align="center">
  <b>MemNexus</b> - Let multiple AI assistants collaborate and break memory silos
</p>

<p align="center">
  <a href="https://github.com/Leeelics/MemNexus">⭐ Star us on GitHub</a> •
  <a href="README.zh.md">🇨🇳 中文文档</a>
</p>
