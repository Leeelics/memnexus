#!/bin/bash
# Install pre-commit hooks for MemNexus

echo "Installing pre-commit hooks..."

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "pre-commit not found. Installing with uv..."
    uvx pip install pre-commit
fi

# Install hooks
pre-commit install

echo "✅ Pre-commit hooks installed successfully!"
echo ""
echo "Hooks will run automatically on each commit."
echo "To run manually: pre-commit run --all-files"
