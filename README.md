# MemNexus - Code Memory for AI Programming Tools

<p align="center">
  <b>English</b> | <a href="README.zh.md">简体中文</a>
</p>

> **Code Memory Layer** - Persistent memory for AI coding assistants

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.12+-green?style=for-the-badge&logo=python" alt="Python 3.12+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License"></a>
  <a href="https://github.com/Leeelics/MemNexus/releases"><img src="https://img.shields.io/github/v/release/Leeelics/MemNexus?style=for-the-badge" alt="Release"></a>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-documentation">Documentation</a> •
  <a href="#-roadmap">Roadmap</a>
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
# Install with uv (recommended)
uv tool install memnexus

# Or with pip
pip install memnexus
```

### Initialize Project

```bash
# In your project directory
cd my-project
memnexus init

# Output:
# ✓ Created .memnexus/ directory
# ✓ Generated config.yaml
# ✓ Detected Git repository
```

### Start Server

```bash
memnexus server

# Server running at http://localhost:8080
```

### Use the API

```python
import requests

# Search memory
response = requests.get(
    "http://localhost:8080/api/v1/memory/search",
    params={"q": "login authentication"}
)
print(response.json())
```

## ✨ Features

### Current (v0.1)

- **🧠 Vector Memory** - Semantic search using LanceDB
- **📊 Session Management** - Track AI tool interactions
- **🌐 HTTP API** - RESTful API for integration
- **⚡ Fast & Local** - Runs locally, no cloud required

### Coming Soon

- **🔀 Git Integration** - Index commit history and code changes
- **📁 Code-Aware RAG** - AST-based code understanding
- **🔌 Vibe Kanban Plugin** - Memory for your kanban workflows

## 📖 Documentation

- [Vision & Positioning](docs/VISION.md) - Product vision and market positioning
- [Roadmap](docs/ROADMAP.md) - Development roadmap and milestones
- [API Reference](docs/API.md) - Complete API documentation

## 🛣️ Roadmap

```
Month 1: Core Foundation
├── Week 1-2: Code cleanup, Git integration MVP
└── Week 3-4: Code-aware RAG MVP

Month 2: Integration
├── Week 5-6: Vibe Kanban plugin
└── Week 7-8: User validation & iteration

Month 3+: Ecosystem
├── Multi-tool support (Kimi, VSCode, etc.)
└── Team collaboration features
```

See [ROADMAP.md](docs/ROADMAP.md) for details.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Programming Tools                     │
│         (Claude Code, Kimi CLI, Codex, etc.)                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      MemNexus API                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │    Git      │  │    Code     │  │   Vector Memory     │  │
│  │  Extractor  │  │   Parser    │  │    (LanceDB)        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📝 License

MemNexus is licensed under the [MIT License](LICENSE).

---

<p align="center">
  <b>MemNexus</b> - Let your AI assistants remember
</p>
