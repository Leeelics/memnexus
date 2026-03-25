# MemNexus - Code Memory for AI Programming Tools

<p align="center">
  <b>English</b> | <a href="README.zh.md">简体中文</a>
</p>

> **Code Memory Layer** - Persistent memory for AI coding assistants

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.12+-green?style=for-the-badge&logo=python" alt="Python 3.12+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License"></a>
  <a href="https://github.com/Leeelics/MemNexus/releases"><img src="https://img.shields.io/github/v/release/Leeelics/MemNexus?style=for-the-badge" alt="Release"></a>
  <a href="https://pypi.org/project/memnexus/"><img src="https://img.shields.io/pypi/v/memnexus?style=for-the-badge" alt="PyPI"></a>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-kimi-cli-plugin">Kimi Plugin</a> •
  <a href="#-documentation">Documentation</a>
</p>

## 🎯 Overview

MemNexus provides **persistent memory** for AI programming tools like Claude Code, Kimi CLI, and Codex.

When you switch between AI tools or start a new session, MemNexus remembers:
- What you built and why
- Code changes and their history
- Project context and decisions

**Problem it solves:**
> "Yesterday I used Claude to build a login feature. Today I'm using Kimi to optimize it. 
> Do I have to explain the entire project structure again?"
> 
> **With MemNexus: No.** Your AI assistants remember.

## 🚀 Quick Start

### Installation

```bash
# Install with pip
pip install memnexus

# Or with uv (recommended)
uv tool install memnexus
```

### Initialize Project

```bash
# In your project directory
cd my-project
memnexus init

# Index your project
memnexus index --git --code
```

### Use with Kimi CLI

MemNexus provides a Kimi CLI plugin for seamless integration:

```bash
# The plugin is automatically available after installation
# Use these commands in Kimi CLI:

/memory search "login implementation"     # Search project memory
/memory store "Use Redis for caching"     # Store important decisions
/memory status                            # Check indexing status
/memory find authenticate_user            # Find specific function
```

### Use as Library

```python
import asyncio
from memnexus import CodeMemory

async def main():
    # Initialize
    memory = await CodeMemory.init("./my-project")
    
    # Index project
    await memory.index_git_history()
    await memory.index_codebase()
    
    # Search
    results = await memory.search("authentication")
    for r in results:
        print(f"{r.source}: {r.content[:100]}")

asyncio.run(main())
```

### Use the HTTP API

```bash
# Start server
memnexus server

# In another terminal
curl "http://localhost:8080/api/v1/search?query=login"
```

## ✨ Features

### Core Features

- **🧠 Vector Memory** - Semantic search using LanceDB
- **📜 Git Integration** - Index and search commit history
- **📁 Code-Aware RAG** - Parse and understand code structure
- **🔌 Kimi CLI Plugin** - Native integration with Kimi CLI 1.25.0+
- **⚡ Fast & Local** - Runs locally, no cloud required
- **🌐 HTTP API** - RESTful API for custom integrations

### Supported Languages

- Python (fully supported)
- JavaScript/TypeScript (coming soon)
- Rust, Go (planned)

## 🔌 Kimi CLI Plugin

MemNexus provides first-class integration with Kimi CLI through its plugin system.

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/memory search <query>` | Search project memory | `/memory search "auth implementation"` |
| `/memory store <content>` | Store important info | `/memory store "Use JWT" --category decision` |
| `/memory status` | Check project status | `/memory status` |
| `/memory index` | Index project | `/memory index --git --code` |
| `/memory find <symbol>` | Find code symbol | `/memory find authenticate_user` |
| `/memory history <file>` | Get file history | `/memory history src/auth.py` |

### Example Session

```
You: /memory search "how does authentication work?"

Kimi: Based on project memory, I found:

1. [Code] AuthController.authenticate_user (auth.py:24)
   def authenticate_user(self, username: str, password: str) -> Optional[dict]:
   """Authenticate user with credentials..."""

2. [Git] Commit a1b2c3d - "feat(auth): Add JWT authentication"
   Author: John Doe | Date: 2024-03-20
   
3. [Memory] Decision: "Use JWT instead of sessions for stateless auth"
   Category: architecture | Tags: auth, jwt

You: /memory store "Need to add rate limiting to auth endpoints" --category todo --tags auth security

Kimi: ✅ Stored in memory (ID: abc123)
```

## 📖 Documentation

- [Vision & Positioning](docs/VISION.md) - Product vision and market positioning
- [Roadmap](docs/ROADMAP.md) - Development roadmap and milestones
- [API Reference](docs/API.md) - Complete API documentation
- [CLI Guide](docs/CLI.md) - Command-line usage
- [Kimi Plugin Guide](docs/KIMI_PLUGIN.md) - Kimi CLI plugin documentation

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Programming Tools                     │
│         (Claude Code, Kimi CLI, Codex, etc.)                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌─────────────────┐
│  Kimi Plugin │   │   HTTP API   │   │  Python Library │
└──────┬───────┘   └──────┬───────┘   └────────┬────────┘
       │                  │                    │
       └──────────────────┼────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      MemNexus Core                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │    Git      │  │    Code     │  │   Vector Memory     │  │
│  │  Extractor  │  │   Parser    │  │    (LanceDB)        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🛣️ Roadmap

### Phase 1: Core (Completed ✅)
- ✅ Git history indexing
- ✅ Code parsing and indexing
- ✅ Vector search
- ✅ Kimi CLI plugin

### Phase 2: Integration (In Progress)
- 🔄 VSCode extension
- 🔄 Claude Code integration
- 🔄 More language support

### Phase 3: Ecosystem (Planned)
- 📋 Team collaboration
- 📋 Cloud sync (optional)
- 📋 Advanced code intelligence

See [ROADMAP.md](docs/ROADMAP.md) for details.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📝 License

MemNexus is licensed under the [MIT License](LICENSE).

---

<p align="center">
  <b>MemNexus</b> - Let your AI assistants remember
</p>
