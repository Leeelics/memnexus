# MemNexus Release Checklist

## Pre-Release Checklist

### Code Quality
- [x] All tests passing
- [x] Code formatted with ruff
- [x] Type checking with mypy
- [x] No linting errors

### Documentation
- [x] README.md updated with current features
- [x] CHANGELOG.md updated with release notes
- [x] INSTALL.md created
- [x] CONTRIBUTING.md exists
- [x] LICENSE file present

### Configuration
- [x] pyproject.toml version updated
- [x] pyproject.toml description accurate
- [x] pyproject.toml classifiers correct
- [x] pyproject.toml dependencies complete

### Build
- [x] Package builds successfully: `python -m build`
- [ ] Package installs locally: `pip install dist/*.whl`
- [ ] CLI works after install: `memnexus --version`

## Release Steps

### 1. Version Bump

```bash
# Update version in pyproject.toml
version = "0.2.0"
```

### 2. Final Checks

```bash
# Run tests
pytest

# Build package
python -m build

# Check package
twine check dist/*
```

### 3. Create Git Tag

```bash
# Commit all changes
git add -A
git commit -m "Release v0.2.0"

# Create tag
git tag -a v0.2.0 -m "Release version 0.2.0"

# Push
git push origin feature/code-memory
git push origin v0.2.0
```

### 4. Publish to PyPI

```bash
# Upload to PyPI
twine upload dist/*

# Or test first on TestPyPI
twine upload --repository testpypi dist/*
```

### 5. Verify Installation

```bash
# In a fresh environment
pip install memnexus

# Verify
memnexus --version
memnexus init --help
```

### 6. Post-Release

- [ ] Create GitHub Release
- [ ] Update documentation site
- [ ] Announce on social media
- [ ] Update Kimi plugin registry (if applicable)

## PyPI Account Setup

### First Time Setup

1. Create PyPI account: https://pypi.org/account/register/
2. Enable 2FA
3. Create API token: https://pypi.org/manage/account/token/
4. Configure ~/.pypirc:

```ini
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcCJD...
```

### TestPyPI (Optional but Recommended)

```ini
[testpypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcCJD...
```

## Rollback Plan

If issues are found after release:

1. **Yank the version** on PyPI (keeps it installable but warns)
2. **Fix the issue** in a new commit
3. **Release patch version** (e.g., 0.2.1)

## Current Release: v0.2.0

### What's New
- Core CodeMemory functionality
- Git history indexing and search
- Code parsing (Python) and indexing
- CLI interface (init, index, search, status, server)
- HTTP API
- Kimi CLI plugin integration

### Known Limitations
- Code parsing only supports Python
- No Windows-specific testing
- Requires Python 3.12+

### Breaking Changes
None (first public release)

---

**Release Manager:** Leeelics  
**Release Date:** 2026-03-25  
**Status:** Ready for release
