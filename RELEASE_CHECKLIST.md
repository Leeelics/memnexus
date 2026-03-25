# PyPI Release Checklist

## Pre-Release Checks

### 1. Version Update
- [ ] `pyproject.toml` version updated
- [ ] `src/memnexus/__init__.py` __version__ updated (if exists)
- [ ] README.md version badge updated (if applicable)

### 2. Documentation
- [ ] README.md updated with current features
- [ ] CHANGELOG.md created with version history
- [ ] INSTALL.md created with installation instructions

### 3. Code Quality
- [ ] All tests pass
- [ ] No linting errors (ruff)

### 4. Build Verification
- [ ] Clean dist/ directory (`make clean`)
- [ ] Build successful (`uv build`)
- [ ] Wheel contains all necessary files
- [ ] Version in wheel is correct

### 5. Git State
- [ ] All changes committed
- [ ] Git tag created (e.g., v0.2.0)
- [ ] No uncommitted changes

## PyPI Account Setup (One-time)

### 1. Create PyPI Account
1. Go to https://pypi.org/
2. Register for an account
3. Enable 2FA (recommended)

### 2. Create API Token
1. Go to https://pypi.org/manage/account/token/
2. Create token with scope: "Entire account (all projects)"
3. Save token securely (will only be shown once)

## Release Steps

### Step 1: Final Verification
```bash
# Run tests
pytest

# Build package
uv build

# Check build
ls -la dist/
# Should show:
# - memnexus-0.2.0-py3-none-any.whl
# - memnexus-0.2.0.tar.gz
```

### Step 2: Upload to PyPI using uv

**Option A: Using environment variable (Recommended)**
```bash
# Set token as environment variable
export UV_PUBLISH_TOKEN="pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Publish
uv publish
```

**Option B: Using command line argument**
```bash
uv publish --token "pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### Step 3: Verify Release
```bash
# Wait a few minutes for PyPI to update

# Check PyPI page
open https://pypi.org/project/memnexus/0.2.0/

# Test installation
pip install memnexus==0.2.0

# Verify version
memnexus --version
# Should show: memnexus, version 0.2.0
```

### Step 4: Post-Release
- [ ] Push git tag to remote: `git push origin v0.2.0`
- [ ] Create GitHub Release (optional)
- [ ] Announce on social media (optional)

## Quick Release Command

```bash
# One-liner for future releases
pytest && uv build && uv publish
```

## Troubleshooting

### Build Errors
```bash
# Clean build artifacts
make clean

# Rebuild
uv build
```

### Upload Errors
```bash
# Dry run to check without uploading
uv publish --dry-run
```

### Authentication Errors
```bash
# Verify token is set correctly
echo $UV_PUBLISH_TOKEN

# Or use --token flag directly
uv publish --token "your-token-here"
```

### Version Conflicts
```bash
# If version already exists on PyPI, you cannot re-upload
# Must increment version number in pyproject.toml
```
