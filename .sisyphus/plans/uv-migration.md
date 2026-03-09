# UV Engineering Migration Plan

> **Goal**: Convert MemNexus project to a fully uv-managed Python project
> **Priority**: High
> **Worktree**: /Users/elics/workspace/kit/MemNexus-worktrees/memory-v3

## Phase 1: pyproject.toml Migration

### Task 1.1: Migrate Dev Dependencies to Dependency Groups
Move from `[project.optional-dependencies]` to `[dependency-groups]` (uv-native way)

### Task 1.2: Add UV Scripts
Add `[tool.uv.scripts]` with one-click commands:
- dev, server - Development server
- test, test-cov - Testing
- format, lint, quality - Code quality
- benchmark - Performance benchmarks

### Task 1.3: Update UV Configuration
Add `[tool.uv]` section with default settings

### Task 1.4: Update Project Metadata
- Version: 0.1.0 → 0.2.0
- Add AI/ML classifiers
- Update description

## Phase 2: Regenerate Lock File
Remove old uv.lock, regenerate with new format

## Phase 3: Create Helper Scripts
- scripts/setup.sh - One-command setup
- scripts/quality.sh - Run all quality checks

## Phase 4: Update Documentation
Update README with uv quick start and examples

## Success Criteria
- [ ] `uv sync` works without errors
- [ ] `uv run server` starts the server
- [ ] `uv run test` runs tests
- [ ] No legacy requirements.txt files
- [ ] README updated with uv instructions
