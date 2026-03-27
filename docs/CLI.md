# MemNexus CLI Reference

Complete reference for the `memnexus` command-line interface.

## Installation

```bash
pip install memnexus
```

The `memnexus` command (and alias `mnx`) will be available.

## Global Options

```bash
memnexus [OPTIONS] COMMAND [ARGS]

Options:
  --help  Show help message and exit
  --version  Show version and exit
```

## Commands

### version

Show version information.

```bash
memnexus version
```

Output:
```
┌───────────── About ─────────────┐
│ MemNexus Code Memory            │
│ Version: 0.2.0                  │
│                                 │
│ Let your AI assistants remember │
└─────────────────────────────────┘
```

### init

Initialize MemNexus for a project.

```bash
memnexus init [OPTIONS] [PATH]

Arguments:
  PATH  Project path [default: current directory]

Options:
  --force, -f  Overwrite existing configuration
```

Example:
```bash
# Initialize current directory
memnexus init

# Initialize specific project
memnexus init ~/projects/my-app

# Force reinitialize
memnexus init --force
```

This creates:
- `.memnexus/` directory
- `.memnexus/config.yaml` - Project configuration
- `.memnexus/memory.lance` - Vector database (on first index)

**Embedding Configuration:**

The default config uses TF-IDF embedding (lightweight, no dependencies). For better quality, configure external API in `.memnexus/config.yaml`:

```yaml
# OpenAI (recommended for best quality)
embedding:
  method: "openai"
  api_key: "sk-..."  # Or use env var: $OPENAI_API_KEY
  model: "text-embedding-3-small"
  dim: 1536
```

### status

Show project status.

```bash
memnexus status [OPTIONS]

Options:
  --path, -p PATH  Project path [default: current directory]
```

Output:
```
┌───────────── Project Status ─────────────┐
│ Project: my-app                          │
│ Path: /home/user/projects/my-app         │
│ Git: ✓ Yes                               │
│ Git commits indexed: 42                  │
│ Code symbols indexed: 156                │
│ Total memories: 198                      │
└──────────────────────────────────────────┘
```

### index

Index project into memory.

```bash
memnexus index [OPTIONS]

Options:
  --path, -p PATH         Project path [default: current directory]
  --git / --no-git        Index Git history [default: enabled]
  --code / --no-code      Index codebase [default: disabled]
  --limit, -l INTEGER     Maximum Git commits to index [default: 1000]
  --lang TEXT             Language to index (python, javascript, typescript)
  --incremental / --full  Use incremental indexing [default: incremental]
  --reset                 Reset index state before indexing (forces full re-index)
```

Examples:
```bash
# Index Git history only (incremental)
memnexus index

# Index both Git and code
memnexus index --git --code

# Force full re-index
memnexus index --full

# Reset and re-index everything
memnexus index --reset --git --code

# Index Python code only
memnexus index --code --lang python

# Index specific project
memnexus index --path ~/projects/my-app --git --code
```

**Incremental Indexing:**
- By default, only new/modified commits and files are indexed
- Index state is stored in `.memnexus/index_state.json`
- Use `--full` to force complete re-index
- Use `--reset` to clear index state before indexing

### search

Search project memory.

```bash
memnexus search [OPTIONS] QUERY

Arguments:
  QUERY  Search query [required]

Options:
  --path, -p PATH     Project path [default: current directory]
  --limit, -n INTEGER Maximum results [default: 5]
  --git               Search Git history only
  --code              Search code only
  --type TEXT         Filter by symbol type (function, class, method)
```

Examples:
```bash
# General search
memnexus search "authentication"

# Search Git history
memnexus search "recent changes" --git

# Search code
memnexus search "def login" --code

# Search functions only
memnexus search "authenticate" --code --type function

# More results
memnexus search "user model" --limit 10
```

### reset

Reset index state to force re-indexing.

```bash
memnexus reset [OPTIONS]

Options:
  --path, -p PATH  Project path [default: current directory]
  --git            Reset Git index state
  --code           Reset code index state
  --all, -a        Reset all index state
```

Examples:
```bash
# Reset Git index state
memnexus reset --git

# Reset code index state
memnexus reset --code

# Reset everything
memnexus reset --all

# Reset specific project
memnexus reset --all --path ~/projects/my-app
```

**Use Cases:**
- After manually deleting `.memnexus/memory.lance`
- When index state becomes corrupted
- To force complete re-index from scratch

### server

Start the HTTP API server.

```bash
memnexus server [OPTIONS]

Options:
  --path, -p PATH     Project path [default: current directory]
  --host, -h TEXT     Host to bind to [default: 127.0.0.1]
  --port, -p INTEGER  Port to bind to [default: 8080]
```

Examples:
```bash
# Default server
memnexus server

# Custom port
memnexus server --port 3000

# Allow external connections
memnexus server --host 0.0.0.0
```

API endpoints:
- `GET /health` - Health check
- `GET /stats` - Project statistics
- `GET /api/v1/search` - Search memories
- `POST /api/v1/memory` - Add memory
- `POST /api/v1/git/index` - Index Git history
- `GET /api/v1/git/search` - Search Git history
- `POST /api/v1/code/index` - Index codebase
- `GET /api/v1/code/search` - Search code symbols

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MEMNEXUS_DATA_DIR` | Global data directory | `~/.memnexus` |
| `MEMNEXUS_DEBUG` | Enable debug mode | `false` |

## Examples

### Complete Workflow

```bash
# 1. Navigate to project
cd ~/projects/my-app

# 2. Initialize
memnexus init

# 3. Index everything
memnexus index --git --code

# 4. Check status
memnexus status

# 5. Search
memnexus search "login authentication"

# 6. Start server for API access
memnexus server
```

### CI/CD Integration

```bash
# In your CI pipeline
memnexus init
memnexus index --git
memnexus status
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Project not initialized |

## Getting Help

```bash
# General help
memnexus --help

# Command help
memnexus init --help
memnexus index --help
memnexus search --help
```
