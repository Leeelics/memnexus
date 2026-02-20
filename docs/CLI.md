# MemNexus CLI Reference

Complete reference for the `memnexus` command-line interface.

## Installation

After installing MemNexus, the `memnexus` command is available:

```bash
pip install -e "."
memnexus --help
```

For convenience, an alias `mnx` is also available.

## Global Options

```bash
memnexus [OPTIONS] COMMAND [ARGS]

Options:
  --help  Show help message and exit
```

## Commands

### Core Commands

#### version

Show version information.

```bash
memnexus version
```

Output:
```
┌───────────── About ─────────────┐
│ MemNexus                        │
│ Version: 0.1.0                  │
│ Data directory: ~/.memnexus     │
└─────────────────────────────────┘
```

#### config-show

Display current configuration.

```bash
memnexus config-show
```

#### server

Start the MemNexus API server.

```bash
memnexus server [OPTIONS]

Options:
  --host, -h TEXT     Host to bind to [default: 127.0.0.1]
  --port, -p INTEGER  Port to bind to [default: 8080]
  --reload            Enable auto-reload [default: False]
  --debug, -d         Enable debug mode [default: False]
```

Example:
```bash
# Production mode
memnexus server

# Development mode with auto-reload
memnexus server --reload --debug --port 8080
```

#### web

Start the web dashboard (Streamlit - planned for future).

```bash
memnexus web [OPTIONS]

Options:
  --port, -p INTEGER  Port for web dashboard [default: 8501]
```

### Session Management

#### session-list

List all sessions.

```bash
memnexus session-list
```

Output:
```
┌─────────────────────────────────────────────────────┐
│ Sessions                                            │
├──────────┬──────────────────┬──────────┬────────────┤
│ ID       │ Name             │ Status   │ Agents │ Tasks │
├──────────┼──────────────────┼──────────┼────────┼───────┤
│ sess_001 │ User Auth System │ running  │ 4      │ 12    │
│ sess_002 │ API Migration    │ paused   │ 2      │ 5     │
└──────────┴──────────────────┴──────────┴────────┴───────┘
```

#### session-create

Create a new session.

```bash
memnexus session-create [OPTIONS] NAME

Arguments:
  NAME  Session name [required]

Options:
  --description, -d TEXT       Session description
  --strategy, -s [sequential|parallel|review|auto]  Execution strategy
  --agents, -a TEXT           Comma-separated list of agents (e.g., claude,kimi)
```

Examples:
```bash
# Simple session
memnexus session-create "My Project"

# With agents
memnexus session-create "My Project" --agents claude,kimi --strategy parallel

# With description
memnexus session-create "API Development" --description "REST API for user management" --strategy sequential
```

#### session-start

Start a session.

```bash
memnexus session-start SESSION_ID
```

#### session-stop

Stop a session.

```bash
memnexus session-stop SESSION_ID
```

### Agent Management

#### agent-list

List all agents.

```bash
memnexus agent-list [OPTIONS]

Options:
  --session, -s TEXT  Filter by session ID
```

#### agent-launch

Launch an agent in wrapper mode.

```bash
memnexus agent-launch [OPTIONS] SESSION_ID CLI

Arguments:
  SESSION_ID  Session ID [required]
  CLI         CLI tool to wrap [required]

Options:
  --name, -n TEXT         Agent name (defaults to CLI)
  --dir, -d TEXT          Working directory [default: .]
```

Examples:
```bash
memnexus agent-launch sess_abc123 claude --name claude-backend
memnexus agent-launch sess_abc123 kimi -n kimi-frontend -d ./frontend
```

#### agent-connect (ACP)

Connect an agent via ACP protocol.

```bash
memnexus acp-connect [OPTIONS] SESSION_ID

Arguments:
  SESSION_ID  Session ID [required]

Options:
  --cli, -c TEXT      CLI tool to connect [default: claude]
  --name, -n TEXT     Agent name
  --dir, -d TEXT      Working directory [default: .]
```

Examples:
```bash
memnexus acp-connect sess_abc123 --cli claude
memnexus acp-connect sess_abc123 -c kimi -n kimi-agent -d ./project
```

### Memory Commands

#### memory-search

Search session memory.

```bash
memnexus memory-search [OPTIONS] SESSION_ID QUERY

Arguments:
  SESSION_ID  Session ID [required]
  QUERY       Search query [required]

Options:
  --limit, -l INTEGER  Maximum results [default: 10]
```

Examples:
```bash
memnexus memory-search sess_abc123 "API endpoints"
memnexus memory-search sess_abc123 "authentication" -l 5
```

#### memory-stats

Show memory store statistics.

```bash
memnexus memory-stats [OPTIONS]

Options:
  --session, -s TEXT  Show session-specific stats
```

### RAG Commands

#### rag-ingest

Ingest a file into RAG pipeline.

```bash
memnexus rag-ingest SESSION_ID FILE_PATH

Arguments:
  SESSION_ID  Session ID [required]
  FILE_PATH   File path to ingest [required]
```

Examples:
```bash
memnexus rag-ingest sess_abc123 README.md
memnexus rag-ingest sess_abc123 src/main.py
memnexus rag-ingest sess_abc123 docs/*.md
```

#### rag-query

Query the RAG pipeline.

```bash
memnexus rag-query [OPTIONS] SESSION_ID QUERY

Arguments:
  SESSION_ID  Session ID [required]
  QUERY       Query text [required]

Options:
  --top-k, -k INTEGER  Number of results [default: 5]
```

Examples:
```bash
memnexus rag-query sess_abc123 "What is the architecture?"
memnexus rag-query sess_abc123 "API endpoints" -k 10
```

### Sync Commands

#### sync-watch

Watch real-time memory sync for a session.

```bash
memnexus sync-watch SESSION_ID

Arguments:
  SESSION_ID  Session ID [required]
```

Example:
```bash
memnexus sync-watch sess_abc123
# Press Ctrl+C to stop
```

### Orchestration Commands

#### orchestrate

Start multi-agent orchestration.

```bash
memnexus orchestrate [OPTIONS] SESSION_ID

Arguments:
  SESSION_ID  Session ID [required]

Options:
  --strategy, -s TEXT   Execution strategy [default: sequential]
  --config, -c PATH     Task config file (YAML)
```

Examples:
```bash
# Interactive mode with default tasks
memnexus orchestrate sess_abc123 --strategy parallel

# With task config file
memnexus orchestrate sess_abc123 -c tasks.yaml
```

**Task Config File (YAML):**
```yaml
strategy: parallel
tasks:
  - id: design
    name: Design Architecture
    role: architect
    prompt: Design the system architecture
    
  - id: backend
    name: Implement Backend
    role: backend
    prompt: Implement the API
    dependencies: [design]
    
  - id: frontend
    name: Build Frontend
    role: frontend
    prompt: Create the UI
    dependencies: [design]
```

#### plan-show

Display execution plan for a session.

```bash
memnexus plan-show SESSION_ID
```

Output:
```
┌─────────────────── Execution Plan: sess_abc123 ───────────────────┐
│ Task              │ Role       │ Status │ Dependencies           │
├───────────────────┼────────────┼────────┼────────────────────────┤
│ Design Architecture│ architect  │ ready  │ None                   │
│ Implement Backend │ backend    │ pending│ design                 │
│ Build Frontend    │ frontend   │ pending│ design                 │
└───────────────────┴────────────┴────────┴────────────────────────┘

Strategy: parallel
Progress: 0.0%
```

### Intervention Commands

#### intervention-list

List interventions for a session.

```bash
memnexus intervention-list [OPTIONS] SESSION_ID

Arguments:
  SESSION_ID  Session ID [required]

Options:
  --status, -s TEXT  Filter by status (pending, waiting_for_human, approved, rejected)
```

Examples:
```bash
memnexus intervention-list sess_abc123
memnexus intervention-list sess_abc123 --status waiting_for_human
```

#### intervention-resolve

Resolve an intervention.

```bash
memnexus intervention-resolve [OPTIONS] INTERVENTION_ID

Arguments:
  INTERVENTION_ID  Intervention ID [required]

Options:
  --action, -a TEXT    Action: approve, reject, modify [required]
  --message, -m TEXT   Resolution message
```

Examples:
```bash
memnexus intervention-resolve int_abc123 -a approve
memnexus intervention-resolve int_abc123 -a reject -m "Needs changes"
memnexus intervention-resolve int_abc123 -a modify -m "Please add error handling"
```

### Wrapper Mode

#### wrapper

Start CLI in wrapper mode.

```bash
memnexus wrapper [OPTIONS] SESSION_ID CLI

Arguments:
  SESSION_ID  Session ID [required]
  CLI         CLI command to wrap [required]

Options:
  --name, -n TEXT  Agent name
```

Examples:
```bash
memnexus wrapper sess_abc123 claude
memnexus wrapper sess_abc123 kimi -n my-agent
memnexus wrapper sess_abc123 "claude --debug" -n debug-claude
```

## Environment Variables

MemNexus can be configured via environment variables:

```bash
# Required
export MEMNEXUS_SECRET_KEY="your-secret-key"

# Optional
export MEMNEXUS_DEBUG="false"
export MEMNEXUS_HOST="127.0.0.1"
export MEMNEXUS_PORT="8080"
export MEMNEXUS_DATA_DIR="$HOME/.memnexus"
export MEMNEXUS_DATABASE_URL="postgresql+asyncpg://..."
export MEMNEXUS_REDIS_URL="redis://localhost:6379/0"
export MEMNEXUS_LANCEDB_URI="~/.memnexus/memory.lance"
```

Create a `.env` file in the project root:

```bash
MEMNEXUS_DEBUG=true
MEMNEXUS_ENV=development
MEMNEXUS_SECRET_KEY=dev-secret-key
MEMNEXUS_DATA_DIR=./data
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Connection error |
| 4 | Timeout |

## Shell Completion

To enable shell completion:

### Bash
```bash
memnexus --install-completion bash
```

### Zsh
```bash
memnexus --install-completion zsh
```

### Fish
```bash
memnexus --install-completion fish
```

## Tips and Tricks

### Use aliases for common commands

Add to your `.bashrc` or `.zshrc`:

```bash
alias mn='memnexus'
alias mns='memnexus server'
alias mnl='memnexus session-list'
alias mnc='memnexus session-create'
```

### JSON output (for scripting)

Most commands support JSON output for scripting:

```bash
memnexus session-list --format json | jq '.[] | select(.status == "running")'
```

### Batch operations

```bash
# Create multiple sessions
for name in "Project A" "Project B" "Project C"; do
  memnexus session-create "$name"
done

# Connect agents to all running sessions
memnexus session-list | grep running | awk '{print $1}' | xargs -I {} memnexus agent-launch {} claude
```

## Troubleshooting

### Command not found

Ensure the virtual environment is activated or the package is installed globally.

### Permission denied

Check file permissions for the data directory:
```bash
chmod 755 ~/.memnexus
```

### Connection refused

Make sure the server is running:
```bash
memnexus server
```

## Getting Help

For each command, use `--help` for detailed information:

```bash
memnexus session-create --help
memnexus orchestrate --help
```
