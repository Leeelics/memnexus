# Getting Started with MemNexus

This guide will help you set up MemNexus and create your first multi-agent session.

## Prerequisites

- Python 3.12 or higher
- Node.js 18+ (for frontend)
- One or more AI CLI tools installed:
  - [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
  - [Kimi CLI](https://www.moonshot.cn/)
  - Or other compatible tools

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Leeelics/MemNexus.git
cd MemNexus
```

### 2. Install Python Dependencies

MemNexus uses [uv](https://github.com/astral-sh/uv) for package management.

**Option 1: Using uv (Recommended)**
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

**Option 2: Using pip**
```bash
pip install -e ".[dev]"
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
```

## Quick Start

### Step 1: Start the Backend

```bash
# From project root
memnexus server
```

The API server will start at `http://localhost:8080`.

### Step 2: Start the Frontend

In a new terminal:
```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`.

### Step 3: Create Your First Session

Using the CLI:
```bash
memnexus session-create "My First Project"
```

Or using the web UI, navigate to the Sessions page and click "New Session".

### Step 4: Connect an Agent

#### Option A: Wrapper Mode (Basic)
```bash
memnexus wrapper <session_id> claude --name claude-architect
```

#### Option B: ACP Protocol (Recommended)
```bash
memnexus acp-connect <session_id> --cli claude --name claude-backend
```

### Step 5: Verify Connection

Check agent status:
```bash
memnexus agent-list
```

Or view in the web dashboard.

## Your First Orchestration

### 1. Define Tasks

Create a task configuration file `tasks.yaml`:

```yaml
session_id: your_session_id
strategy: parallel
tasks:
  - id: design
    name: Design Architecture
    role: architect
    prompt: Design a REST API for a todo list application
    
  - id: backend
    name: Implement Backend
    role: backend
    prompt: Implement the backend API based on the architecture design
    dependencies: [design]
    
  - id: frontend
    name: Build Frontend
    role: frontend
    prompt: Create a React frontend for the todo app
    dependencies: [design]
    
  - id: test
    name: Write Tests
    role: tester
    prompt: Write integration tests for the todo app
    dependencies: [backend, frontend]
```

### 2. Start Orchestration

```bash
memnexus orchestrate <session_id> --strategy parallel
```

### 3. Monitor Progress

- Web UI: Navigate to the Orchestration page
- CLI: `memnexus plan-show <session_id>`

### 4. Handle Interventions

If agents request human input:
```bash
# List pending interventions
memnexus intervention-list <session_id>

# Resolve an intervention
memnexus intervention-resolve <intervention_id> --action approve
```

## Using Memory and RAG

### Ingest Documents

```bash
# Ingest a single file
memnexus rag-ingest <session_id> README.md

# Ingest all project files
find . -name "*.md" -o -name "*.py" | xargs -I {} memnexus rag-ingest <session_id> {}
```

### Query Knowledge Base

```bash
memnexus rag-query <session_id> "What is the API architecture?"
```

### Search Shared Memory

```bash
memnexus memory-search <session_id> "authentication implementation"
```

## Web UI Walkthrough

### Dashboard
- View system status and statistics
- See recent sessions and activity
- Monitor memory usage

### Sessions
- Create and manage sessions
- View session details and connected agents
- Control session state (start, pause, stop)

### Orchestration
- Visual task flow diagram
- Real-time execution progress
- Task status and logs

### Interventions
- Review pending human interventions
- Approve, reject, or request changes
- View intervention history

### Memory
- Search shared memory
- Browse agent outputs
- View conversation history

## Next Steps

- Read the [Architecture Overview](ARCHITECTURE.md)
- Explore [API Reference](API.md)
- Learn about [ACP Protocol](PROTOCOL_ACP.md)
- Check [CLI Guide](CLI.md) for more commands

## Troubleshooting

### Common Issues

**Port already in use**
```bash
# Change backend port
memnexus server --port 8081
```

**Frontend can't connect to API**
```bash
# Update Vite proxy config in frontend/vite.config.ts
```

**Agent connection fails**
- Ensure the CLI tool is installed and in PATH
- Check agent compatibility
- Try wrapper mode as fallback

## Getting Help

- 📖 [Documentation](https://github.com/Leeelics/MemNexus/tree/main/docs)
- 🐛 [Issue Tracker](https://github.com/Leeelics/MemNexus/issues)
- 💬 [Discussions](https://github.com/Leeelics/MemNexus/discussions)

---

Happy coding with MemNexus! 🚀
