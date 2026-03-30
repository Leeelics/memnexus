#!/usr/bin/env python3
"""Manual test for Git integration without full dependencies."""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import directly from git.py to avoid loading other modules
import importlib.util

spec = importlib.util.spec_from_file_location(
    "git", str(Path(__file__).parent.parent / "src" / "memnexus" / "memory" / "git.py")
)
git_module = importlib.util.module_from_spec(spec)
sys.modules["git_module"] = git_module
spec.loader.exec_module(git_module)

GitMemoryExtractor = git_module.GitMemoryExtractor
GitCommit = git_module.GitCommit

from git import Repo


def test_git_extractor():
    """Test GitMemoryExtractor with a real git repo."""

    # Create temp repo
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Init repo
        repo = Repo.init(repo_path)
        config = repo.config_writer()
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")
        config.release()

        # Create commits
        (repo_path / "README.md").write_text("# Test\n")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")

        (repo_path / "auth.py").write_text("def login(): pass\n")
        repo.index.add(["auth.py"])
        repo.index.commit("feat(auth): Add login")

        (repo_path / "auth.py").write_text("def login(): return True\n")
        repo.index.add(["auth.py"])
        repo.index.commit("fix(auth): Fix login")

        # Test extractor
        print("=" * 60)
        print("Testing GitMemoryExtractor")
        print("=" * 60)

        extractor = GitMemoryExtractor(str(repo_path))
        print(f"✓ Extractor initialized: {extractor.is_valid()}")

        # Test extract_recent
        commits = extractor.extract_recent(limit=10)
        print(f"✓ Extracted {len(commits)} commits")

        for i, commit in enumerate(commits):
            print(f"  [{i}] {commit.hash}: {commit.message[:50]}")

        # Test extract_file_history
        auth_commits = extractor.extract_file_history("auth.py")
        print(f"✓ auth.py history: {len(auth_commits)} commits")

        # Test extract_by_pattern
        auth_pattern = extractor.extract_by_pattern("auth")
        print(f"✓ Pattern 'auth': {len(auth_pattern)} commits")

        # Test stats
        stats = extractor.get_repo_stats()
        print("✓ Repo stats:")
        print(f"    - Total commits: {stats['total_commits']}")
        print(f"    - Active branch: {stats['active_branch']}")
        print(f"    - Top contributors: {stats['top_contributors']}")

        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)


if __name__ == "__main__":
    test_git_extractor()
