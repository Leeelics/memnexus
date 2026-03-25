# Installation Guide

Detailed installation instructions for MemNexus.

For a quick start, see [README.md](../README.md) or [Getting Started Guide](docs/GETTING_STARTED.md).

## Requirements

- Python 3.12 or higher
- Git (for Git history indexing)
- 500MB+ free disk space (for vector database)

## Install Methods

### Option 1: pip (Recommended)

```bash
pip install memnexus
```

### Option 2: uv

```bash
uv tool install memnexus
```

### Option 3: Development Install

```bash
git clone https://github.com/Leeelics/MemNexus.git
cd MemNexus
pip install -e ".[dev]"
```

## Verify Installation

```bash
memnexus --version
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

- [Getting Started Guide](docs/GETTING_STARTED.md) - Complete tutorial
- [CLI Reference](docs/CLI.md) - Command reference
- [API Documentation](docs/API.md) - HTTP API docs
