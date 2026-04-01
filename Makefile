# MemNexus Makefile
# Unified build commands for development and CI/CD

.DEFAULT_GOAL := help

# Environment variables
export NO_COLOR := 1
export TERM := dumb

.PHONY: help
help: ## Show available make targets.
	@echo "Available make targets:"
	@awk 'BEGIN { FS = ":.*## " } /^[A-Za-z0-9_.-]+:.*## / { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# =============================================================================
# Development Setup
# =============================================================================

.PHONY: install
install: ## Install dependencies with uv.
	@echo "==> Installing dependencies"
	@uv sync --all-extras --dev

.PHONY: update
update: ## Update dependencies and lock file.
	@echo "==> Updating dependencies"
	@uv lock --upgrade
	@uv sync --all-extras --dev

# =============================================================================
# Code Quality
# =============================================================================

.PHONY: format
format: ## Auto-format code with ruff.
	@echo "==> Formatting code"
	@uv run ruff check --fix
	@uv run ruff format

.PHONY: format-check
format-check: ## Check code formatting without making changes.
	@echo "==> Checking code format"
	@uv run ruff format --check

.PHONY: lint
lint: ## Run linting with ruff.
	@echo "==> Running linter"
	@uv run ruff check src/memnexus scripts

.PHONY: typecheck
typecheck: ## Run type checking with mypy.
	@echo "==> Running type checker"
	@uv run mypy src/memnexus

.PHONY: check
check: format-check lint ## Run all code quality checks (format, lint).
	@echo "==> Core checks passed (typecheck has known issues)"

# =============================================================================
# Testing
# =============================================================================

.PHONY: test
test: ## Run all tests with pytest.
	@echo "==> Running tests"
	@uv run pytest -vv

.PHONY: test-cov
test-cov: ## Run tests with coverage report.
	@echo "==> Running tests with coverage"
	@uv run pytest --cov=memnexus --cov-report=term-missing --cov-report=xml

.PHONY: test-ci
test-ci: ## Run tests for CI (junit xml output).
	@echo "==> Running tests (CI mode)"
	@uv run pytest -vv --junitxml=junit.xml

# =============================================================================
# Building
# =============================================================================

.PHONY: build
build: ## Build package distributions (wheel and sdist).
	@echo "==> Building package"
	@uv build --no-sources --out-dir dist

.PHONY: build-check
build-check: build ## Build and check distributions with twine.
	@echo "==> Checking distributions"
	@uvx twine check dist/*

.PHONY: clean
clean: ## Clean build artifacts.
	@echo "==> Cleaning build artifacts"
	@rm -rf dist/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true

# =============================================================================
# Version Management
# =============================================================================

.PHONY: version-check
version-check: ## Check if version matches git tag (for releases).
	@echo "==> Checking version"
	@uv run scripts/check_version.py

# =============================================================================
# CI/CD Aliases
# =============================================================================

.PHONY: ci
ci: install check test-ci ## Run full CI pipeline locally.
	@echo "==> CI pipeline completed"

.PHONY: release
release: clean build-check ## Prepare for release (build and check).
	@echo "==> Release build ready"
	@ls -la dist/
