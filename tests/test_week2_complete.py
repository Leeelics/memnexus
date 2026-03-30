#!/usr/bin/env python3
"""
Week 2 Completion Test - Git Integration

This script verifies that Week 2 Git integration is working correctly.
It tests the GitMemoryExtractor and validates the implementation without
requiring full LanceDB dependencies.
"""

import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Test imports
try:
    from git import Repo

    print("✓ GitPython imported successfully")
except ImportError as e:
    print(f"✗ Failed to import GitPython: {e}")
    sys.exit(1)

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


def create_test_repo(tmpdir: Path) -> Path:
    """Create a test Git repository with sample commits."""
    repo_path = Path(tmpdir)

    # Init repo
    repo = Repo.init(repo_path)
    config = repo.config_writer()
    config.set_value("user", "name", "Test Developer")
    config.set_value("user", "email", "dev@example.com")
    config.release()

    # Create commits simulating a real project
    commits_data = [
        ("README.md", "# MyProject\n\nA Python web application.", "Initial commit: Project setup"),
        (
            "auth.py",
            "def login(username, password):\n    pass\n",
            "feat(auth): Add login placeholder",
        ),
        (
            "auth.py",
            "def login(username, password):\n    # TODO: implement\n    return True\n",
            "feat(auth): Basic login implementation",
        ),
        (
            "models.py",
            "class User:\n    def __init__(self, name):\n        self.name = name\n",
            "feat(models): Add User model",
        ),
        (
            "auth.py",
            "def login(username, password):\n    user = User.find(username)\n    return user.verify(password)\n",
            "fix(auth): Use User model for authentication",
        ),
    ]

    for filename, content, message in commits_data:
        file_path = repo_path / filename
        file_path.write_text(content)
        repo.index.add([filename])
        repo.index.commit(message)

    return repo_path


def test_week2_implementation():
    """Run all Week 2 tests."""

    print("=" * 70)
    print("WEEK 2: Git Integration Test")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = create_test_repo(Path(tmpdir))
        print(f"✓ Created test repository at: {repo_path}")

        # Test 1: GitMemoryExtractor initialization
        print("\n[Test 1] GitMemoryExtractor Initialization")
        print("-" * 40)
        try:
            extractor = GitMemoryExtractor(str(repo_path))
            assert extractor.is_valid(), "Extractor should be valid"
            print("✓ Extractor initialized successfully")
            print(f"  Repo path: {extractor.repo_path}")
        except Exception as e:
            print(f"✗ Failed: {e}")
            return False

        # Test 2: Extract recent commits
        print("\n[Test 2] Extract Recent Commits")
        print("-" * 40)
        try:
            commits = extractor.extract_recent(limit=10)
            assert len(commits) == 5, f"Expected 5 commits, got {len(commits)}"
            print(f"✓ Extracted {len(commits)} commits")

            for i, commit in enumerate(commits):
                assert isinstance(commit, GitCommit), f"Commit {i} should be GitCommit"
                assert len(commit.hash) == 8, f"Hash should be 8 chars, got {len(commit.hash)}"
                assert commit.author == "Test Developer <dev@example.com>"
                assert isinstance(commit.timestamp, datetime)
                print(f"  [{i}] {commit.hash}: {commit.message[:50]}")
        except Exception as e:
            print(f"✗ Failed: {e}")
            return False

        # Test 3: Extract file history
        print("\n[Test 3] Extract File History (auth.py)")
        print("-" * 40)
        try:
            auth_commits = extractor.extract_file_history("auth.py")
            assert len(auth_commits) == 3, (
                f"Expected 3 commits for auth.py, got {len(auth_commits)}"
            )
            print(f"✓ Found {len(auth_commits)} commits for auth.py")

            for commit in auth_commits:
                assert any("auth.py" in f for f in commit.files_changed)
                print(f"  - {commit.hash}: {commit.message}")
        except Exception as e:
            print(f"✗ Failed: {e}")
            return False

        # Test 4: Search by pattern
        print("\n[Test 4] Search by Pattern ('auth' or 'login')")
        print("-" * 40)
        try:
            auth_commits = extractor.extract_by_pattern("auth")
            assert len(auth_commits) >= 3, "Expected at least 3 commits matching 'auth'"
            print(f"✓ Found {len(auth_commits)} commits matching 'auth'")

            login_commits = extractor.extract_by_pattern("login")
            assert len(login_commits) >= 2, "Expected at least 2 commits matching 'login'"
            print(f"✓ Found {len(login_commits)} commits matching 'login'")
        except Exception as e:
            print(f"✗ Failed: {e}")
            return False

        # Test 5: Search by author
        print("\n[Test 5] Search by Author")
        print("-" * 40)
        try:
            dev_commits = extractor.extract_by_author("Test Developer")
            assert len(dev_commits) == 5, "Expected 5 commits by Test Developer"
            print(f"✓ Found {len(dev_commits)} commits by 'Test Developer'")

            email_commits = extractor.extract_by_author("dev@example.com")
            assert len(email_commits) == 5, "Expected 5 commits by email"
            print(f"✓ Found {len(email_commits)} commits by email")
        except Exception as e:
            print(f"✗ Failed: {e}")
            return False

        # Test 6: Repository stats
        print("\n[Test 6] Repository Statistics")
        print("-" * 40)
        try:
            stats = extractor.get_repo_stats()
            assert stats["total_commits"] == 5, "Expected 5 total commits"
            assert stats["active_branch"] in ["master", "main"]
            assert len(stats["top_contributors"]) == 1
            assert stats["top_contributors"][0][0] == "Test Developer"
            assert stats["top_contributors"][0][1] == 5

            print("✓ Repository stats:")
            print(f"  - Total commits: {stats['total_commits']}")
            print(f"  - Active branch: {stats['active_branch']}")
            print(
                f"  - Top contributor: {stats['top_contributors'][0][0]} ({stats['top_contributors'][0][1]} commits)"
            )
        except Exception as e:
            print(f"✗ Failed: {e}")
            return False

        # Test 7: GitCommit data structure
        print("\n[Test 7] GitCommit Data Structure")
        print("-" * 40)
        try:
            commit = commits[0]
            assert hasattr(commit, "hash")
            assert hasattr(commit, "message")
            assert hasattr(commit, "author")
            assert hasattr(commit, "timestamp")
            assert hasattr(commit, "files_changed")
            assert hasattr(commit, "diff_summary")
            assert hasattr(commit, "stats")

            print("✓ GitCommit has all required fields")
            print(f"  - hash: {commit.hash}")
            print(f"  - message: {commit.message[:40]}...")
            print(f"  - author: {commit.author}")
            print(f"  - timestamp: {commit.timestamp}")
            print(f"  - files_changed: {commit.files_changed}")
            print(f"  - stats: {commit.stats}")
        except Exception as e:
            print(f"✗ Failed: {e}")
            return False

    print("\n" + "=" * 70)
    print("✅ ALL WEEK 2 TESTS PASSED!")
    print("=" * 70)
    print("\nWeek 2 Deliverables:")
    print("  ✓ GitMemoryExtractor class implemented")
    print("  ✓ extract_recent() - Extract recent commits")
    print("  ✓ extract_file_history() - Get file-specific history")
    print("  ✓ extract_by_pattern() - Search commit messages/files")
    print("  ✓ extract_by_author() - Filter by author")
    print("  ✓ get_repo_stats() - Repository statistics")
    print("  ✓ GitCommit dataclass with full metadata")

    return True


if __name__ == "__main__":
    success = test_week2_implementation()
    sys.exit(0 if success else 1)
