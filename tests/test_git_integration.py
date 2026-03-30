"""Tests for Git integration (Week 2).

These tests verify that Git history can be extracted, indexed, and searched.
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from git import Repo

from memnexus.code_memory import CodeMemory
from memnexus.memory.git import GitCommit, GitMemoryExtractor


@pytest.fixture
def temp_git_repo():
    """Create a temporary Git repository with some commits."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Initialize git repo
        repo = Repo.init(repo_path)

        # Configure git user
        config = repo.config_writer()
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")
        config.release()

        # Create some files and commits
        (repo_path / "README.md").write_text("# Test Project\n")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit: Add README")

        (repo_path / "auth.py").write_text("def login(): pass\n")
        repo.index.add(["auth.py"])
        repo.index.commit("feat(auth): Add login function")

        (repo_path / "auth.py").write_text("def login():\n    return True\n")
        repo.index.add(["auth.py"])
        repo.index.commit("fix(auth): Implement login logic")

        (repo_path / "utils.py").write_text("def helper(): pass\n")
        repo.index.add(["utils.py"])
        repo.index.commit("feat(utils): Add helper function")

        yield repo_path


@pytest.fixture
async def initialized_memory(temp_git_repo):
    """Create an initialized CodeMemory instance."""
    # Initialize memnexus
    memnexus_dir = temp_git_repo / ".memnexus"
    memnexus_dir.mkdir()

    config = memnexus_dir / "config.yaml"
    config.write_text(f"""
version: "1.0"
project:
  name: "test"
  root: "{temp_git_repo}"
memory:
  backend: "lancedb"
  path: ".memnexus/memory.lance"
""")

    memory = await CodeMemory.init(temp_git_repo)
    yield memory
    await memory.close()


class TestGitMemoryExtractor:
    """Test GitMemoryExtractor functionality."""

    def test_init_with_valid_repo(self, temp_git_repo):
        """Test extractor initialization with valid repo."""
        extractor = GitMemoryExtractor(str(temp_git_repo))
        assert extractor.is_valid()
        assert extractor.repo_path == temp_git_repo

    def test_init_with_invalid_repo(self):
        """Test extractor initialization with invalid repo."""
        with tempfile.TemporaryDirectory() as tmpdir, pytest.raises(Exception):
            GitMemoryExtractor(tmpdir)

    def test_extract_recent(self, temp_git_repo):
        """Test extracting recent commits."""
        extractor = GitMemoryExtractor(str(temp_git_repo))
        commits = extractor.extract_recent(limit=10)

        assert len(commits) == 4  # We created 4 commits

        # Check first (most recent) commit
        first = commits[0]
        assert isinstance(first, GitCommit)
        assert len(first.hash) == 8
        assert "utils" in first.message.lower()
        assert first.author == "Test User <test@example.com>"
        assert isinstance(first.timestamp, datetime)
        assert "utils.py" in first.files_changed

    def test_extract_recent_with_limit(self, temp_git_repo):
        """Test extracting with limit."""
        extractor = GitMemoryExtractor(str(temp_git_repo))
        commits = extractor.extract_recent(limit=2)

        assert len(commits) == 2

    def test_extract_file_history(self, temp_git_repo):
        """Test extracting history for specific file."""
        extractor = GitMemoryExtractor(str(temp_git_repo))
        commits = extractor.extract_file_history("auth.py")

        assert len(commits) == 2  # auth.py was modified twice

        # Check that all commits involve auth.py
        for commit in commits:
            assert any("auth.py" in f for f in commit.files_changed)

    def test_extract_by_author(self, temp_git_repo):
        """Test extracting commits by author."""
        extractor = GitMemoryExtractor(str(temp_git_repo))
        commits = extractor.extract_by_author("Test User")

        assert len(commits) == 4

    def test_extract_by_pattern(self, temp_git_repo):
        """Test extracting commits by pattern."""
        extractor = GitMemoryExtractor(str(temp_git_repo))
        commits = extractor.extract_by_pattern("auth")

        assert len(commits) == 2  # Two commits mention auth

    def test_get_repo_stats(self, temp_git_repo):
        """Test getting repo stats."""
        extractor = GitMemoryExtractor(str(temp_git_repo))
        stats = extractor.get_repo_stats()

        assert stats["total_commits"] == 4
        assert stats["active_branch"] == "master" or stats["active_branch"] == "main"
        assert len(stats["top_contributors"]) == 1
        assert stats["top_contributors"][0][0] == "Test User"


class TestCodeMemoryGitIntegration:
    """Test CodeMemory Git integration."""

    @pytest.mark.asyncio
    async def test_index_git_history(self, temp_git_repo):
        """Test indexing Git history."""
        # Setup
        memnexus_dir = temp_git_repo / ".memnexus"
        memnexus_dir.mkdir()
        config = memnexus_dir / "config.yaml"
        config.write_text("""
version: "1.0"
project:
  name: "test"
memory:
  backend: "lancedb"
""")

        memory = await CodeMemory.init(temp_git_repo)

        try:
            # Index Git history
            result = await memory.index_git_history(limit=10)

            assert result["commits_indexed"] == 4
            assert result["total_commits"] == 4
            assert len(result["errors"]) == 0

            # Check stats
            stats = memory.get_stats()
            assert stats["git_commits_indexed"] == 4
            assert stats["has_git"] is True

        finally:
            await memory.close()

    @pytest.mark.asyncio
    async def test_query_git_history(self, temp_git_repo):
        """Test querying Git history."""
        # Setup
        memnexus_dir = temp_git_repo / ".memnexus"
        memnexus_dir.mkdir()
        config = memnexus_dir / "config.yaml"
        config.write_text("""
version: "1.0"
project:
  name: "test"
memory:
  backend: "lancedb"
""")

        memory = await CodeMemory.init(temp_git_repo)

        try:
            # Index first
            await memory.index_git_history(limit=10)

            # Query
            results = await memory.query_git_history("login", limit=5)

            assert len(results) > 0
            # Should find the login-related commits
            messages = [r.message.lower() for r in results]
            assert any("login" in m for m in messages)

        finally:
            await memory.close()

    @pytest.mark.asyncio
    async def test_get_file_history(self, temp_git_repo):
        """Test getting file history."""
        # Setup
        memnexus_dir = temp_git_repo / ".memnexus"
        memnexus_dir.mkdir()
        config = memnexus_dir / "config.yaml"
        config.write_text("""
version: "1.0"
project:
  name: "test"
memory:
  backend: "lancedb"
""")

        memory = await CodeMemory.init(temp_git_repo)

        try:
            # Get file history (should auto-index if needed)
            results = await memory.get_file_history("auth.py", limit=10)

            assert len(results) >= 2  # auth.py has 2 commits

        finally:
            await memory.close()

    @pytest.mark.asyncio
    async def test_get_repo_stats(self, temp_git_repo):
        """Test getting repo stats via CodeMemory."""
        # Setup
        memnexus_dir = temp_git_repo / ".memnexus"
        memnexus_dir.mkdir()
        config = memnexus_dir / "config.yaml"
        config.write_text("""
version: "1.0"
project:
  name: "test"
memory:
  backend: "lancedb"
""")

        memory = await CodeMemory.init(temp_git_repo)

        try:
            stats = await memory.get_repo_stats()

            assert stats["total_commits"] == 4
            assert "active_branch" in stats

        finally:
            await memory.close()


class TestGitCommitDataclass:
    """Test GitCommit dataclass."""

    def test_git_commit_creation(self):
        """Test creating a GitCommit."""
        commit = GitCommit(
            hash="abc123",
            message="Test commit",
            author="Test User <test@example.com>",
            timestamp=datetime.now(),
            files_changed=["file1.py", "file2.py"],
            diff_summary="file1.py: +10/-5",
            stats={"files_changed": 2, "insertions": 10, "deletions": 5},
        )

        assert commit.hash == "abc123"
        assert commit.message == "Test commit"
        assert len(commit.files_changed) == 2
        assert commit.stats["files_changed"] == 2
