# MemNexus Git Hooks

This directory contains Git hooks for the MemNexus project.

## Pre-push Hook

The pre-push hook automatically runs CI checks before pushing to remote, ensuring code quality and preventing broken builds.

### Installation

```bash
# Copy the hook to your local .git/hooks directory
cp hooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push

# Verify installation
ls -la .git/hooks/pre-push
```

### Checks Performed

The hook runs the following checks in order:

| Step | Command | Description | Skippable |
|------|---------|-------------|-----------|
| 1 | `make lint` + `make format-check` | Code linting and formatting | `SKIP_LINT=1` |
| 2 | `make typecheck` | Type checking with mypy | `SKIP_TYPECHECK=1` |
| 3 | `make test` | Run all tests | `SKIP_TESTS=1` |
| 4 | `scripts/check_version.py` | Version consistency | - |
| 5 | File existence check | README, CHANGELOG, LICENSE | - |
| 6 | `make build-check` | Build and package check | `SKIP_BUILD=1` |

### Usage

**Normal push (full checks):**
```bash
git push
```

**Fast push (skip build):**
```bash
SKIP_BUILD=1 git push
```

**Quick push (skip tests and build):**
```bash
SKIP_BUILD=1 SKIP_TESTS=1 git push
```

**Skip type checking (if mypy has known issues):**
```bash
SKIP_TYPECHECK=1 git push
```

**Emergency push (skip all checks - NOT recommended):**
```bash
git push --no-verify
```

### Environment Variables

| Variable | Effect |
|----------|--------|
| `SKIP_LINT=1` | Skip lint and format checks |
| `SKIP_TYPECHECK=1` | Skip mypy type checking |
| `SKIP_TESTS=1` | Skip test execution |
| `SKIP_BUILD=1` | Skip build verification |

### Troubleshooting

**Hook not running:**
- Check that `.git/hooks/pre-push` exists and is executable
- Verify with: `ls -la .git/hooks/pre-push`

**Type check failures:**
- MemNexus has some known mypy issues
- Use `SKIP_TYPECHECK=1` to skip if CI is configured to allow failures

**Build check timeout:**
- Build check can be slow
- Use `SKIP_BUILD=1` for faster pushes during development

### CI/CD Correspondence

This hook mirrors the GitHub Actions workflow in `.github/workflows/ci.yml`:

- `check` job → Steps 1 (lint + format)
- `typecheck` job → Step 2 (typecheck)
- `test` job → Step 3 (test)
- `build` job → Steps 4-6 (version, docs, build)

Running the hook locally before push reduces the chance of CI failures.
