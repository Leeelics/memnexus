#!/usr/bin/env python3
"""
Version checker for MemNexus.

Checks if the version in pyproject.toml matches the git tag (for releases).
Also verifies version consistency across the codebase.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


def get_git_tag() -> str | None:
    """Get the current git tag if on a tag."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_version_from_pyproject(pyproject_path: Path = Path("pyproject.toml")) -> str:
    """Extract version from pyproject.toml."""
    if not pyproject_path.exists():
        print(f"❌ pyproject.toml not found at {pyproject_path}")
        sys.exit(1)

    content = pyproject_path.read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        print("❌ Could not find version in pyproject.toml")
        sys.exit(1)

    return match.group(1)


def get_version_from_init(src_dir: Path = Path("src/memnexus")) -> str | None:
    """Extract version from __init__.py if it exists."""
    init_file = src_dir / "__init__.py"
    if not init_file.exists():
        return None

    content = init_file.read_text()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)
    return None


def check_version(expected_version: str | None = None) -> bool:
    """Check version consistency."""
    pyproject_version = get_version_from_pyproject()
    init_version = get_version_from_init()
    git_tag = expected_version or get_git_tag()

    print(f"📦 pyproject.toml version: {pyproject_version}")

    if init_version:
        print(f"🐍 __init__.py version:   {init_version}")
        if init_version != pyproject_version:
            print(
                f"❌ Version mismatch: __init__.py ({init_version}) != pyproject.toml ({pyproject_version})"
            )
            return False

    if git_tag:
        # Remove 'v' prefix from git tag if present
        tag_version = git_tag.lstrip("v")
        print(f"🏷️  Git tag:               {git_tag}")

        if tag_version != pyproject_version:
            print(
                f"❌ Version mismatch: git tag ({tag_version}) != pyproject.toml ({pyproject_version})"
            )
            return False
    else:
        print("🏷️  Git tag:               (not on a tag)")

    print(f"✅ Version check passed: {pyproject_version}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Check MemNexus version consistency")
    parser.add_argument(
        "--expected-version",
        type=str,
        default=None,
        help="Expected version to check against (e.g., from CI environment)",
    )
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=Path("pyproject.toml"),
        help="Path to pyproject.toml",
    )

    args = parser.parse_args()

    # Get expected version from environment variable if set
    expected = args.expected_version or os.environ.get("GITHUB_REF_NAME")

    success = check_version(expected)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
