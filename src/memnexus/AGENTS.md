# MemNexus - Agent Development Guide

> **Language**: English / 中文 (项目文档主要使用中文，代码注释使用英文)
> **Current Phase**: Phase 1 - Rapid Prototyping

---

## Project Overview

**MemNexus** is a local AI OS-level memory daemon that breaks down the memory silos between AI programming tools like Claude Code, Kimi CLI, and Codex.

### Core Purpose
- Enable multiple AI Agents to share context and see each other's outputs and code changes
- Orchestrate task execution: Architect → Backend → Frontend → Testing
- Provide real-time monitoring via Web dashboard
- Allow human intervention: pause, adjust, and reassign tasks at critical moments

### Key Protocols
- **ACP (Agent Client Protocol)**: Primary protocol, natively supported by Claude/Kimi
- **MCP (Model Context Protocol)**: Fallback/secondary protocol for tool/resource connections

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | FastAPI + Uvicorn | Async web server and API |
| CLI Framework | Typer + Rich | Interactive command-line interface |
| Data Validation | Pydantic v2 | Schema validation and settings management |
| Vector Database | LanceDB | Embedded vector + full-text search |
| Cache/Queue | Redis | Real-time messaging and state caching |
| Metadata Store | PostgreSQL + asyncpg | Relational data and transactions |
| RAG Pipeline | LlamaIndex | Document chunking and retrieval |
| Testing | pytest + pytest-asyncio | Unit and integration testing |
| Linting | Ruff | Code formatting and linting |
| Type Checking | mypy | Static type analysis |

---

## Project Structure

```
memnexus/
├── AGENTS.md               # This file - AI agent development guide
├── README.md               # Human-readable project documentation (中文)
├── pyproject.toml          # Project configuration (uv/ruff/pytest/mypy)
├── .gitignore              # Git ignore patterns
├── src/
│   └── memnexus/           # Main Python package
│       ├── __init__.py     # Package exports
│       ├── server.py       # FastAPI server + WebSocket endpoints
│       ├── cli.py          # Typer CLI entry point
│       ├── core/           # Core business logic
│       │   ├── config.py   # Pydantic settings management
│       │   └── session.py  # Session/Agent/Task models & manager
│       ├── agents/         # Agent implementations (EMPTY - TODO)
│       ├── memory/         # Memory/RAG system (EMPTY - TODO)
│       ├── protocols/      # ACP/MCP protocol handlers (EMPTY - TODO)
│       └── web/            # Web dashboard (EMPTY - TODO)
```

### Current Implementation Status

| Module | Status | Description |
|--------|--------|-------------|
| `core/config.py` | ✅ Implemented | Full settings with env var support |
| `core/session.py` | ✅ Implemented | Session, Agent, Task models + SessionManager |
| `server.py` | ✅ Implemented | FastAPI app with REST API + WebSocket + HTML dashboard |
| `cli.py` | ✅ Implemented | Full CLI with session/agent management commands |
| `agents/` | ✅ Implemented | Base agent classes and CLI wrapper |
| `memory/` | ✅ Implemented | LanceDB vector store + Context manager |
| `protocols/` | ⏳ Empty | ACP/MCP protocol implementations (Phase 2) |
| `web/` | ⏳ Empty | Streamlit/React dashboard components |

---

## Build and Development Commands

### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Redis server (for cache)
- PostgreSQL server (for metadata)

### Installation

```bash
# Clone and enter directory
git clone https://github.com/Leeelics/MemNexus.git
cd MemNexus

# Install dependencies with uv (recommended)
uv sync

# Or install with pip
pip install -e ".[dev]"
```

### Running the Server

```bash
# Start production server
memnexus server

# Start development server with auto-reload
memnexus server --reload --debug --port 8080

# Or directly with Python
python -m memnexus.server
```

### CLI Commands

```bash
# Show version and info
memnexus version

# Configuration
memnexus config-show

# Session management
memnexus session-list
memnexus session-create "My Project" --agents claude,kimi
memnexus session-start <session_id>
memnexus session-stop <session_id>

# Agent management
memnexus agent-list

# Web dashboard (planned)
memnexus web --port 8501
```

### Code Quality Commands

```bash
# Format code
ruff format .

# Lint code
ruff check . --fix

# Type check
mypy src/memnexus

# Run tests
pytest

# Run tests with coverage
pytest --cov=memnexus --cov-report=html

# Run specific test markers
pytest -m "not slow"        # Skip slow tests
pytest -m "unit"            # Run only unit tests
pytest -m "integration"     # Run only integration tests
```

---

## Code Style Guidelines

### Python Style

1. **Formatter**: Use `ruff` (configured in `pyproject.toml`)
   - Line length: 100 characters
   - Quote style: double quotes
   - Indent: 4 spaces

2. **Import Order**:
   ```python
   # 1. Standard library
   import json
   from typing import Dict, List, Optional
   
   # 2. Third-party
   from fastapi import FastAPI
   from pydantic import BaseModel
   
   # 3. First-party (memnexus)
   from memnexus.core.config import settings
   from memnexus.core.session import SessionManager
   ```

3. **Type Hints**: Required for all function signatures
   ```python
   async def create_session(
       name: str,
       description: str = "",
   ) -> Session:
       """Create a new session."""
       ...
   ```

4. **Docstrings**: Use Google-style docstrings
   ```python
   def function(arg1: str, arg2: int) -> bool:
       """Short description.
       
       Longer description if needed.
       
       Args:
           arg1: Description of arg1
           arg2: Description of arg2
           
       Returns:
           Description of return value
           
       Raises:
           ValueError: When invalid input
       """
   ```

5. **Async/Await**: Prefer async for I/O operations
   - Database operations: async
   - File operations: use `aiofiles`
   - HTTP requests: async clients

6. **Pydantic Models**: Use for all data structures
   ```python
   from pydantic import BaseModel, Field
   
   class AgentConfig(BaseModel):
       """Agent configuration."""
       role: AgentRole
       cli: str
       timeout: int = 300
   ```

7. **Enums**: Use for status/role constants
   ```python
   from enum import Enum
   
   class SessionStatus(str, Enum):
       CREATED = "created"
       RUNNING = "running"
       PAUSED = "paused"
   ```

### Error Handling

```python
# Use specific exceptions
try:
    session = await session_manager.get(session_id)
except SessionNotFoundError:
    raise HTTPException(status_code=404, detail="Session not found")
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Testing Instructions

### Test Structure (To be created)

```
tests/
├── __init__.py
├── conftest.py           # pytest fixtures
├── unit/
│   ├── test_config.py
│   ├── test_session.py
│   └── test_agent.py
├── integration/
│   ├── test_api.py
│   └── test_websocket.py
└── fixtures/
    └── sample_data.py
```

### Writing Tests

```python
import pytest
from memnexus.core.session import SessionManager, ExecutionStrategy

@pytest.mark.unit
async def test_create_session():
    """Test session creation."""
    manager = SessionManager()
    session = await manager.create(
        name="Test Session",
        strategy=ExecutionStrategy.SEQUENTIAL,
    )
    assert session.name == "Test Session"
    assert session.status.value == "created"

@pytest.mark.integration
async def test_api_create_session(client):
    """Test API endpoint."""
    response = await client.post("/api/v1/sessions", json={
        "name": "Test",
        "strategy": "sequential",
    })
    assert response.status_code == 200
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific module
pytest tests/unit/test_session.py

# Run with coverage
pytest --cov=memnexus --cov-report=term-missing

# Run parallel (requires pytest-xdist)
pytest -n auto
```

---

## Configuration

### Environment Variables

All configuration uses `MEMNEXUS_` prefix:

```bash
# Required
export MEMNEXUS_SECRET_KEY="your-secret-key"

# Optional (with defaults)
export MEMNEXUS_DEBUG="false"
export MEMNEXUS_ENV="development"
export MEMNEXUS_HOST="127.0.0.1"
export MEMNEXUS_PORT="8080"
export MEMNEXUS_DATA_DIR="$HOME/.memnexus"
export MEMNEXUS_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/memnexus"
export MEMNEXUS_REDIS_URL="redis://localhost:6379/0"
export MEMNEXUS_LANCEDB_URI="~/.memnexus/memory.lance"
export MEMNEXUS_AGENT_TIMEOUT="300"
export MEMNEXUS_AGENT_MAX_RETRIES="3"
```

### Local Development .env

Create `.env` file in project root:

```bash
MEMNEXUS_DEBUG=true
MEMNEXUS_ENV=development
MEMNEXUS_SECRET_KEY=dev-secret-key
MEMNEXUS_DATA_DIR=./data
```

---

## Security Considerations

### Current Status
- ⚠️ **CORS**: Currently allows all origins (`*`) - MUST configure for production
- ⚠️ **Secret Key**: Default value in config - MUST change in production
- ⚠️ **Authentication**: Not implemented yet

### Production Checklist
- [ ] Configure CORS with specific origins
- [ ] Set strong `MEMNEXUS_SECRET_KEY`
- [ ] Enable authentication/authorization
- [ ] Use HTTPS/WSS
- [ ] Validate all inputs
- [ ] Rate limiting on API endpoints
- [ ] Audit logging

---

## Key Abstractions

### Session
A collaborative workspace containing agents and tasks.

```python
class Session(BaseModel):
    id: str                    # UUID (first 8 chars)
    name: str                  # Display name
    description: str           # Optional description
    status: SessionStatus      # created/running/paused/completed/error
    strategy: ExecutionStrategy  # sequential/parallel/review/auto
    working_dir: str           # Working directory path
    agents: List[Agent]        # Assigned agents
    tasks: List[Task]          # Tasks to execute
```

### Agent
An AI assistant instance within a session.

```python
class Agent(BaseModel):
    id: str                    # UUID
    session_id: str            # Parent session
    config: AgentConfig        # Role, CLI, protocol, etc.
    status: AgentStatus        # idle/planning/coding/reviewing/waiting/error/offline
    current_task: Optional[str]  # Currently executing task ID
    pid: Optional[int]         # Process ID if running locally
```

### Agent Roles
- `architect`: System design and planning
- `backend`: Server-side implementation
- `frontend`: Client-side implementation
- `tester`: Testing and quality assurance
- `reviewer`: Code review
- `devops`: Deployment and infrastructure

### Execution Strategies
- `sequential`: One agent at a time
- `parallel`: Multiple agents simultaneously
- `review`: Execute then review cycle
- `auto`: AI decides optimal strategy

---

## API Endpoints

### Health & Info
- `GET /` - Root info
- `GET /health` - Health check
- `GET /dashboard` - HTML dashboard

### Sessions
- `GET /api/v1/sessions` - List all sessions
- `POST /api/v1/sessions` - Create session
- `GET /api/v1/sessions/{id}` - Get session
- `POST /api/v1/sessions/{id}/start` - Start session
- `POST /api/v1/sessions/{id}/pause` - Pause session
- `DELETE /api/v1/sessions/{id}` - Delete session

### Agents
- `GET /api/v1/sessions/{id}/agents` - List agents in session
- `POST /api/v1/sessions/{id}/agents` - Add agent to session

### WebSocket
- `WS /ws` - Real-time updates
  - Message types: `connect`, `subscribe`, `ping/pong`

---

## Phase 1 Features Guide

### CLI Wrapper Mode

Wrap existing CLI tools with MemNexus for context sharing:

```bash
# Wrap claude CLI in a session
memnexus wrapper sess_abc123 claude --name claude-backend

# Wrap kimi CLI
memnexus wrapper sess_abc123 kimi -n kimi-frontend -d ./frontend

# Launch agent in wrapper mode
memnexus agent-launch sess_abc123 claude --name my-agent
```

### Shared Memory System

MemNexus uses LanceDB for vector-based shared memory:

```python
from memnexus.memory.store import MemoryStore
from memnexus.memory.context import ContextManager

# Initialize memory store
store = MemoryStore()
await store.initialize()

# Create context for a session
context = ContextManager(session_id="sess_123", store=store)
await context.initialize()

# Store agent output
await context.store_agent_output(
    agent="claude",
    content="I've created the API endpoint",
    memory_type="code"
)

# Search memories
results = await context.get_context("What did claude build?")
```

### Memory CLI Commands

```bash
# Search session memory
memnexus memory-search sess_abc123 "API endpoints"

# Show memory statistics
memnexus memory-stats

# Show session-specific stats
memnexus memory-stats --session sess_abc123
```

---

## Development Roadmap

### Phase 1: Rapid Prototyping (Completed)
- [x] Project skeleton
- [x] Core models (Session, Agent, Task)
- [x] FastAPI server with REST API
- [x] WebSocket support
- [x] Basic HTML dashboard
- [x] CLI Wrapper mode (temporary solution)
- [x] Simple shared memory (LanceDB + sentence-transformers)

### Phase 2: Protocol Implementation (Current)
- [ ] ACP protocol server
- [ ] Claude Code / Kimi CLI native ACP connection
- [x] LanceDB + LlamaIndex integration (moved to Phase 1)
- [x] WebSocket real-time updates (basic implementation in Phase 1)
- [ ] Full LlamaIndex RAG pipeline
- [ ] Real-time memory sync between agents

### Phase 3: Full Product
- [ ] Multi-agent orchestrator
- [ ] Task dependency scheduling
- [ ] Human intervention system
- [ ] React frontend

---

## Common Development Tasks

### Adding a New Agent Type

1. Create file in `agents/` directory
2. Inherit from `BaseAgent` (to be created)
3. Implement required methods
4. Register in `agents/registry.py`

### Adding a New API Endpoint

1. Add route in `server.py`
2. Use proper type hints and Pydantic models
3. Add error handling
4. Update this documentation

### Adding a New CLI Command

1. Add function in `cli.py` with `@app.command()` decorator
2. Use Typer for arguments/options
3. Use Rich for output formatting
4. Follow existing command naming conventions

---

## Debugging Tips

### Enable Debug Mode
```bash
export MEMNEXUS_DEBUG=true
memnexus server
```

### Check Logs
Logs are stored in `~/.memnexus/logs/` by default.

### Database Inspection
```bash
# Redis
redis-cli

# PostgreSQL
psql postgresql://postgres:postgres@localhost:5432/memnexus
```

### LanceDB Inspection
```python
import lancedb
db = lancedb.connect("~/.memnexus/memory.lance")
print(db.table_names())
```

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [LanceDB Documentation](https://lancedb.github.io/lancedb/)
- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [ACP Protocol (Claude Code)](https://docs.anthropic.com/en/docs/claude-code)
- [MCP Protocol](https://modelcontextprotocol.io/)

---

## Contact & Contributing

- Repository: https://github.com/Leeelics/MemNexus
- Issues: https://github.com/Leeelics/MemNexus/issues
- Author: Leeelics (your.email@example.com)
- License: MIT

When contributing:
1. Follow the code style guidelines
2. Add tests for new features
3. Update this documentation
4. Ensure all tests pass before submitting PR
