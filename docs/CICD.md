# CI/CD Configuration Guide

This document describes the GitHub Actions CI/CD workflows for MemNexus.

## Workflows Overview

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| **CI** | `.github/workflows/ci.yml` | Push/PR to main | Run tests, lint, check build |
| **PR Check** | `.github/workflows/pr-check.yml` | Pull requests | Comprehensive PR checks |
| **Release** | `.github/workflows/release.yml` | Tag push (v*) | Build and publish to PyPI |

## CI Workflow

Runs on every push to `main`/`develop` and pull requests to `main`.

### Jobs

1. **test-python** (Python 3.12, 3.13)
   - Install dependencies with uv
   - Run ruff linting and formatting checks
   - Run mypy type checking
   - Run pytest tests

2. **check-build**
   - Build package with `uv build`
   - Check package with `twine check`
   - Upload artifacts

3. **check-docs**
   - Verify README.md, CHANGELOG.md, LICENSE exist
   - Check version consistency between pyproject.toml and __init__.py

## PR Check Workflow

Runs on pull requests to `main` for comprehensive checks.

### Jobs

1. **lint-and-format**
   - Code formatting (ruff)
   - Linting (ruff)
   - Type checking (mypy)

2. **test** (Multi-platform)
   - Ubuntu, macOS, Windows
   - Python 3.12, 3.13
   - Full test suite

3. **check-security**
   - Bandit security scan
   - Upload security report

4. **check-dependencies**
   - Verify lock file is up to date

## Release Workflow

Triggered when pushing tags matching `v*` (e.g., `v0.3.0`).

### Jobs

1. **build**
   - Run full test suite
   - Build package
   - Upload artifacts

2. **publish-pypi**
   - Download build artifacts
   - Publish to PyPI using `uv publish`
   - Requires `PYPI_API_TOKEN` secret

3. **create-github-release**
   - Create GitHub Release with changelog
   - Attach build artifacts
   - Mark as prerelease if tag contains alpha/beta/rc

## Setup Instructions

### 1. Enable GitHub Actions

Ensure GitHub Actions is enabled in your repository settings:
- Settings → Actions → General → Allow all actions and reusable workflows

### 2. Configure PyPI Publishing

For automatic PyPI publishing, you need to set up a PyPI API token:

#### Option A: Use PyPI Trusted Publishing (Recommended)

1. Go to [PyPI](https://pypi.org/manage/account/publishing/)
2. Add a new pending publisher:
   - **PyPI Project Name**: `memnexus`
   - **Owner**: `Leeelics`
   - **Repository name**: `MemNexus`
   - **Workflow name**: `release.yml`
   - **Environment name**: `pypi`

3. No secrets needed! GitHub Actions will use OIDC to authenticate.

#### Option B: Use API Token (Alternative)

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/token/)
2. Create an API token with scope for `memnexus`
3. Add it to GitHub Secrets:
   - Settings → Secrets and variables → Actions
   - New repository secret: `PYPI_API_TOKEN`

### 3. Required Secrets

| Secret | Required For | How to Get |
|--------|--------------|------------|
| `PYPI_API_TOKEN` | PyPI publishing | PyPI Account → API Tokens |

### 4. Required Permissions

Ensure the workflow has these permissions:

```yaml
permissions:
  contents: write      # For creating releases
  id-token: write      # For PyPI trusted publishing
```

## Manual Release Process

While CI/CD automates releases, you can also release manually:

### Using GitHub Web Interface

1. Go to Releases → Draft a new release
2. Choose tag: `v0.3.0` (create new)
3. Fill in release notes
4. Publish release
5. Release workflow will trigger automatically

### Using Command Line

```bash
# 1. Update version in pyproject.toml and __init__.py
# 2. Update CHANGELOG.md
# 3. Commit and push
git add -A
git commit -m "release: v0.3.0"
git push origin main

# 4. Create and push tag
git tag -a v0.3.0 -m "Release v0.3.0"
git push origin v0.3.0

# 5. Release workflow will trigger automatically
```

## Troubleshooting

### CI Fails on Lint

```bash
# Fix formatting locally
uv run ruff format src/memnexus

# Fix linting issues
uv run ruff check src/memnexus --fix
```

### CI Fails on Type Check

```bash
# Run mypy locally
uv run mypy src/memnexus
```

### Version Mismatch Error

Ensure version is consistent:
- `pyproject.toml`: `version = "0.3.0"`
- `src/memnexus/__init__.py`: `__version__ = "0.3.0"`

### PyPI Publishing Fails

1. Check `PYPI_API_TOKEN` is set correctly
2. Verify token has correct scope (project-specific or account-wide)
3. Check if version already exists on PyPI (can't overwrite)

## Best Practices

1. **Always use PRs for changes** - Don't push directly to main
2. **Wait for CI to pass** - Before merging PRs
3. **Use semantic versioning** - vMAJOR.MINOR.PATCH
4. **Update CHANGELOG.md** - Before creating releases
5. **Test locally first** - Run `uv run pytest` before pushing

## Future Improvements

- [ ] Add automated changelog generation
- [ ] Add code coverage reporting
- [ ] Add benchmark tests
- [ ] Add Docker image building
- [ ] Add documentation website deployment
