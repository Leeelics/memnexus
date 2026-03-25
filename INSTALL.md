# Installation Guide

## Requirements

- Python 3.12 or higher
- Git (for Git history indexing)
- 500MB+ free disk space (for vector database)

## Quick Install

### Using pip

```bash
pip install memnexus
```

### Using uv (recommended)

```bash
uv tool install memnexus
```

### Development Install

```bash
git clone https://github.com/Leeelics/MemNexus.git
cd MemNexus
pip install -e ".[dev]"
```

## Verify Installation

```bash
memnexus --version
# Should output: memnexus, version 0.2.0
```

## First Time Setup

### 1. Initialize a Project

```bash
cd your-project-directory
memnexus init
```

This creates a `.memnexus/` directory with:
- `config.yaml` - Project configuration
- `memory.lance` - Vector database (created on first index)

### 2. Index Your Project

```bash
# Index both Git history and code
memnexus index --git --code

# Or index separately
memnexus index --git        # Only Git history
memnexus index --code       # Only code
```

### 3. Verify Setup

```bash
memnexus status
```

Should show:
- Project path
- Git repository status
- Number of indexed commits and symbols

## Kimi CLI Plugin Setup

If you're using Kimi CLI 1.25.0+, the MemNexus plugin is automatically available after installation.

### Verify Plugin

```bash
kimi plugin list
# Should show: memnexus v0.2.0 (installed)
```

### Use in Kimi CLI

```
/memory status
/memory search "your query"
```

## Troubleshooting

### "command not found: memnexus"

Your Python scripts directory might not be in PATH.

**Fix:**
```bash
# Find where pip installed it
which python3
# Then add the bin directory to PATH
export PATH="$PATH:$(python3 -m site --user-base)/bin"
```

### "No module named 'lancedb'"

Dependencies not installed correctly.

**Fix:**
```bash
pip install --force-reinstall memnexus
```

### Git repository not detected

Make sure you're in a Git repository:

```bash
git status
# If not a git repo, initialize it:
git init
```

### Permission denied

If installing system-wide:

```bash
# Option 1: User install (recommended)
pip install --user memnexus

# Option 2: Use uv (no permission issues)
uv tool install memnexus
```

## Uninstall

```bash
pip uninstall memnexus

# Also remove project data if desired
rm -rf .memnexus/
```

## Next Steps

- Read the [Quick Start Guide](docs/QUICKSTART.md)
- Learn about [CLI Commands](docs/CLI.md)
- Explore the [API Reference](docs/API.md)
