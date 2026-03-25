# Getting Started with MemNexus

This guide will help you set up MemNexus and start using code memory for your AI programming tools.

## Prerequisites

- Python 3.12 or higher
- Git (for Git history indexing)
- (Optional) Kimi CLI 1.25.0+ for plugin support

## Installation

### Option 1: Using pip (Recommended)

```bash
pip install memnexus
```

### Option 2: Using uv

```bash
uv tool install memnexus
```

### Option 3: Development Install

```bash
git clone https://github.com/Leeelics/MemNexus.git
cd MemNexus
pip install -e ".[dev]"
```

## Quick Start

### 1. Verify Installation

```bash
memnexus --version
# Output: memnexus, version 0.2.0
```

### 2. Initialize a Project

```bash
cd your-project-directory
memnexus init
```

This creates a `.memnexus/` directory with:
- `config.yaml` - Project configuration
- `memory.lance` - Vector database (created on first index)

### 3. Index Your Project

```bash
# Index both Git history and code
memnexus index --git --code

# Or index separately
memnexus index --git        # Git history only
memnexus index --code       # Code only
```

### 4. Search Memory

```bash
memnexus search "authentication"
memnexus search "login function" --code
memnexus search "recent changes" --git
```

### 5. Check Status

```bash
memnexus status
```

## Using with Kimi CLI

If you have Kimi CLI 1.25.0+, the MemNexus plugin is automatically available.

### Available Commands

```
/memory search "your query"     # Search project memory
/memory store "important note"  # Store information
/memory status                  # Check indexing status
/memory index                   # Index project
/memory find function_name      # Find code symbol
/memory history src/file.py     # Get file history
```

### Example Session

```
You: /memory search "how does auth work?"

Kimi: Based on project memory:

1. [Code] AuthController.login (auth.py:24)
   def login(self, username: str, password: str) -> User:
   """Authenticate user..."""

2. [Git] Commit a1b2c3d - "feat(auth): Add JWT authentication"
   Date: 2024-03-20

3. [Memory] Decision: "Use JWT instead of sessions"
   Tags: auth, architecture
```

## Using the Python Library

```python
import asyncio
from memnexus import CodeMemory

async def main():
    # Initialize
    memory = await CodeMemory.init("./my-project")
    
    # Index
    await memory.index_git_history()
    await memory.index_codebase()
    
    # Search
    results = await memory.search("authentication")
    for r in results:
        print(f"{r.source}: {r.content[:100]}")

asyncio.run(main())
```

## Using the HTTP API

Start the server:

```bash
memnexus server
# Server running at http://localhost:8080
```

Query the API:

```bash
# Search
curl "http://localhost:8080/api/v1/search?query=login"

# Index Git
curl -X POST "http://localhost:8080/api/v1/git/index"

# Index code
curl -X POST "http://localhost:8080/api/v1/code/index"
```

## Next Steps

- Read the [CLI Guide](CLI.md) for detailed command reference
- Check the [API Documentation](API.md) for HTTP API details
- See [VISION.md](VISION.md) for product positioning
- View [ROADMAP.md](ROADMAP.md) for future plans

## Troubleshooting

### "Project not initialized"

Run `memnexus init` in your project directory.

### "No results found"

Make sure you've indexed the project:
```bash
memnexus index --git --code
```

### Git repository not detected

Ensure you're in a Git repository:
```bash
git status
```

## Getting Help

- GitHub Issues: https://github.com/Leeelics/MemNexus/issues
- Documentation: See `docs/` directory
