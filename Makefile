.PHONY: install dev test format lint clean build publish

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Development
dev: install-dev
	@echo "MemNexus development environment ready"
	@echo "Run 'memnexus init' to initialize a project"

# Testing
test:
	pytest tests/ -v

# Code quality
format:
	ruff format src/ tests/

lint:
	ruff check src/ tests/

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build package (using uv)
build: clean
	uv build

# Release to PyPI (requires UV_PUBLISH_TOKEN)
publish: build
	uv publish

# Dry run publish (test without uploading)
publish-dry-run: build
	uv publish --dry-run
