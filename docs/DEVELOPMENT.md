# MemNexus Development Guide

## Development Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/Leeelics/MemNexus.git
cd MemNexus
```

### 2. Install Dependencies

**Using uv (Recommended):**

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

**Using pip:**

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 3. Start Development Server

```bash
# Start API server
memnexus server

# Or with hot reload
memnexus server --reload
```

### 4. Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_week2_complete.py

# Run with verbose output
pytest -v
```

## Project Structure

```
src/memnexus/
├── __init__.py              # Package exports
├── code_memory.py           # Core CodeMemory class
├── cli.py                   # CLI interface
├── server.py                # FastAPI server
└── memory/                  # Memory system
    ├── store.py             # LanceDB vector storage
    ├── git.py               # Git integration
    └── code.py              # Code parsing
```

## Code Style

We use:
- **ruff** for linting and formatting
- **mypy** for type checking
- Line length: 100 characters

### Before Committing

```bash
# Format code
ruff format .

# Check linting
ruff check . --fix

# Type check
mypy src/memnexus
```

## Adding New Features

### Adding a New CLI Command

Edit `src/memnexus/cli.py`:

```python
@app.command()
def my_command(
    arg: str = typer.Argument(..., help="Argument description"),
):
    """Command description."""
    # Implementation
```

### Adding a New API Endpoint

Edit `src/memnexus/server.py`:

```python
@app.get("/api/v1/my-endpoint")
async def my_endpoint(param: str) -> Dict:
    """Endpoint description."""
    return {"result": "value"}
```

### Adding Code Parser Support for New Language

Edit `src/memnexus/memory/code.py`:

1. Add language detection in `_detect_language()`
2. Implement parser method (e.g., `_parse_typescript_file()`)
3. Update `parse_file()` to route to new parser

## Testing

### Writing Tests

Place tests in `tests/` directory:

```python
# tests/test_feature.py
def test_my_feature():
    result = my_function()
    assert result == expected
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=memnexus --cov-report=html

# Run specific marker
pytest -m "not slow"
```

## Building and Publishing

### Build Package

```bash
python -m build
```

### Check Package

```bash
twine check dist/*
```

### Upload to PyPI

```bash
twine upload dist/*
```

## Documentation

- Update `README.md` for user-facing changes
- Update `CHANGELOG.md` with your changes
- Update relevant docs in `docs/` directory
- Add docstrings to new functions and classes

## Commit Messages

Follow conventional commits:

```
feat: add new feature
fix: fix a bug
docs: update documentation
refactor: refactor code
test: add tests
chore: maintenance tasks
```

## Getting Help

- GitHub Issues: https://github.com/Leeelics/MemNexus/issues
- Discussions: https://github.com/Leeelics/MemNexus/discussions
