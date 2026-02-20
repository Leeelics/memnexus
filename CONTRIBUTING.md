# Contributing to MemNexus

Thank you for your interest in contributing to MemNexus! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code:
- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Respect different viewpoints

## How to Contribute

### Reporting Bugs

Before creating a bug report, please:
1. Check if the issue already exists
2. Ensure you're using the latest version
3. Collect relevant logs and error messages

When reporting bugs, include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs or error messages

### Suggesting Features

Feature requests are welcome! Please:
- Check if the feature has already been suggested
- Provide clear use cases
- Explain why this feature would be useful

### Pull Requests

1. Fork the repository
2. Create a new branch from `main`
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 18+ (for frontend)
- Git

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/memnexus.git
cd memnexus

# Install Python dependencies (using uv recommended)
uv sync
source .venv/bin/activate

# Or using pip
pip install -e ".[dev]"

# Install frontend dependencies
cd frontend
npm install
cd ..

# Run tests
pytest

# Start development server
memnexus server --reload
cd frontend && npm run dev
```

## Code Style

### Python

We use:
- **ruff** for linting and formatting
- **mypy** for type checking
- Line length: 100 characters
- Follow PEP 8 with some modifications

Before committing:
```bash
# Format code
ruff format .

# Check linting
ruff check . --fix

# Type check
mypy src/memnexus
```

### Frontend

- **TypeScript** for type safety
- **Tailwind CSS** for styling
- Follow React best practices

```bash
cd frontend
npm run lint
npm run build
```

## Testing

### Python Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=memnexus --cov-report=html

# Run specific test file
pytest tests/test_session.py

# Run with markers
pytest -m "not slow"
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Documentation

- Update README.md if changing user-facing features
- Update CHANGELOG.md with your changes
- Add docstrings to new functions and classes
- Update relevant docs in the `docs/` folder

## Commit Messages

Follow conventional commits:

```
feat: add new orchestration strategy
fix: resolve memory sync issue
docs: update API documentation
refactor: simplify task scheduler
test: add tests for intervention system
chore: update dependencies
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

## Project Structure

```
memnexus/
├── src/memnexus/        # Main Python package
│   ├── agents/          # Agent implementations
│   ├── core/            # Core functionality
│   ├── memory/          # Memory system
│   ├── orchestrator/    # Task orchestration
│   ├── protocols/       # Protocol implementations
│   ├── cli.py           # CLI entry point
│   └── server.py        # FastAPI server
├── frontend/            # React frontend
├── docs/                # Documentation
├── tests/               # Test files
└── pyproject.toml       # Project configuration
```

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag: `git tag v0.x.x`
4. Push tag: `git push origin v0.x.x`
5. Create GitHub release

## Questions?

- Open an issue for questions
- Join discussions in GitHub Discussions
- Check existing documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to MemNexus! 🚀
