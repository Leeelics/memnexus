"""Git integration for code memory.

Extracts commit history and code changes from Git repositories
to build a searchable memory of project evolution.

Week 2 Implementation:
- Extract commit history with messages and diffs
- Index code changes over time
- Enable queries like "what changed in auth module recently"
"""

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from git import Repo
from git.exc import InvalidGitRepositoryError


@dataclass
class GitCommit:
    """Represents a Git commit."""

    hash: str
    message: str
    author: str
    timestamp: datetime
    files_changed: list[str]
    diff_summary: str
    stats: dict = None  # Added: insertions, deletions, files changed count


@dataclass
class FileChange:
    """Represents a change to a single file in a commit."""

    file_path: str
    change_type: str  # 'A' (added), 'M' (modified), 'D' (deleted), 'R' (renamed)
    insertions: int
    deletions: int
    diff_content: str | None = None


class GitMemoryExtractor:
    """Extracts Git history for memory indexing.

    Week 2 Implementation.

    Example:
        >>> extractor = GitMemoryExtractor("/path/to/repo")
        >>> commits = extractor.extract_recent(limit=10)
        >>> commits = extractor.extract_by_file("auth/login.py", limit=5)
        >>> history = extractor.extract_file_history("src/main.py")
    """

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self._repo: Repo | None = None
        self._init_repo()

    def _init_repo(self) -> None:
        """Initialize the Git repository connection."""
        try:
            self._repo = Repo(self.repo_path)
            if self._repo.bare:
                raise InvalidGitRepositoryError(f"Repository is bare: {self.repo_path}")
        except InvalidGitRepositoryError as e:
            raise InvalidGitRepositoryError(f"Not a valid Git repository: {self.repo_path}") from e

    def _parse_commit(self, commit) -> GitCommit:
        """Parse a Git commit object into GitCommit dataclass.

        Args:
            commit: GitPython Commit object

        Returns:
            GitCommit with extracted information
        """
        # Get changed files
        files_changed = []
        diff_summary_parts = []

        if commit.parents:
            # Compare with parent to get changes
            parent = commit.parents[0]
            diff_index = parent.diff(commit, create_patch=True)

            for diff_item in diff_index:
                # Determine file path
                if diff_item.new_file:
                    file_path = diff_item.b_path or diff_item.a_path
                    change_type = "A"
                elif diff_item.deleted_file:
                    file_path = diff_item.a_path
                    change_type = "D"
                elif diff_item.renamed:
                    file_path = f"{diff_item.a_path} -> {diff_item.b_path}"
                    change_type = "R"
                else:
                    file_path = diff_item.b_path or diff_item.a_path
                    change_type = "M"

                files_changed.append(file_path)

                # Build diff summary
                if diff_item.diff:
                    diff_text = diff_item.diff.decode("utf-8", errors="replace")
                    # Count lines
                    added = diff_text.count("\n+") - diff_text.count("\n+++")
                    removed = diff_text.count("\n-") - diff_text.count("\n---")
                    if added > 0 or removed > 0:
                        diff_summary_parts.append(f"{file_path}: +{added}/-{removed}")
        else:
            # Initial commit - list all files
            files_changed = list(commit.stats.files.keys())
            diff_summary_parts = [f"{f}: initial commit" for f in files_changed]

        # Build stats
        stats = {
            "files_changed": len(files_changed),
            "insertions": sum(1 for p in diff_summary_parts if "+" in p),
            "deletions": sum(1 for p in diff_summary_parts if "-" in p),
        }

        return GitCommit(
            hash=commit.hexsha[:8],
            message=commit.message.strip(),
            author=f"{commit.author.name} <{commit.author.email}>",
            timestamp=datetime.fromtimestamp(commit.committed_date),
            files_changed=files_changed,
            diff_summary="\n".join(diff_summary_parts) if diff_summary_parts else "No changes",
            stats=stats,
        )

    def extract_recent(self, file_path: str | None = None, limit: int = 100) -> list[GitCommit]:
        """Extract recent commits.

        Args:
            file_path: Optional file to filter commits by (relative to repo root)
            limit: Maximum number of commits to extract

        Returns:
            List of GitCommit objects, ordered from newest to oldest

        Example:
            >>> extractor = GitMemoryExtractor("/path/to/repo")
            >>> commits = extractor.extract_recent(limit=10)
            >>> commits = extractor.extract_recent("auth/login.py", limit=5)
        """
        if not self._repo:
            return []

        commits = []
        count = 0

        try:
            # Get iterator over commits
            if file_path:
                # Filter by specific file
                commit_iter = self._repo.iter_commits(paths=file_path, max_count=limit)
            else:
                # All commits
                commit_iter = self._repo.iter_commits(max_count=limit)

            for commit in commit_iter:
                if count >= limit:
                    break

                git_commit = self._parse_commit(commit)
                commits.append(git_commit)
                count += 1

        except Exception as e:
            # Log error but return what we have
            print(f"Warning: Error extracting commits: {e}")

        return commits

    def extract_file_history(self, file_path: str, limit: int = 50) -> list[GitCommit]:
        """Extract full history for a specific file.

        Args:
            file_path: Path to file (relative to repo root)
            limit: Maximum number of commits to extract

        Returns:
            List of commits affecting this file, ordered from newest to oldest

        Example:
            >>> history = extractor.extract_file_history("src/auth/login.py")
            >>> for commit in history:
            ...     print(f"{commit.hash}: {commit.message}")
        """
        return self.extract_recent(file_path=file_path, limit=limit)

    def extract_by_author(self, author: str, limit: int = 100) -> list[GitCommit]:
        """Extract commits by a specific author.

        Args:
            author: Author name or email to filter by
            limit: Maximum number of commits to extract

        Returns:
            List of commits by the author
        """
        if not self._repo:
            return []

        commits = []
        count = 0

        try:
            for commit in self._repo.iter_commits():
                if count >= limit:
                    break

                # Check if author matches (case-insensitive)
                author_str = f"{commit.author.name} <{commit.author.email}>"
                if (
                    author.lower() in author_str.lower()
                    or author.lower() in commit.author.name.lower()
                    or author.lower() in commit.author.email.lower()
                ):
                    git_commit = self._parse_commit(commit)
                    commits.append(git_commit)
                    count += 1

        except Exception as e:
            print(f"Warning: Error extracting commits by author: {e}")

        return commits

    def extract_by_pattern(self, pattern: str, limit: int = 100) -> list[GitCommit]:
        """Extract commits matching a pattern in message or files.

        Args:
            pattern: Regex pattern to search for
            limit: Maximum number of commits to extract

        Returns:
            List of matching commits
        """
        if not self._repo:
            return []

        commits = []
        count = 0
        regex = re.compile(pattern, re.IGNORECASE)

        try:
            for commit in self._repo.iter_commits():
                if count >= limit:
                    break

                # Check message
                if regex.search(commit.message):
                    git_commit = self._parse_commit(commit)
                    commits.append(git_commit)
                    count += 1
                    continue

                # Check files
                files = list(commit.stats.files.keys())
                if any(regex.search(f) for f in files):
                    git_commit = self._parse_commit(commit)
                    commits.append(git_commit)
                    count += 1

        except Exception as e:
            print(f"Warning: Error extracting commits by pattern: {e}")

        return commits

    def get_repo_stats(self) -> dict:
        """Get repository statistics.

        Returns:
            Dictionary with repo stats
        """
        if not self._repo:
            return {}

        try:
            # Count total commits
            total_commits = sum(1 for _ in self._repo.iter_commits())

            # Get active branch
            active_branch = (
                self._repo.active_branch.name
                if self._repo.head.is_detached == False
                else "detached"
            )

            # Get contributors
            contributors = {}
            for commit in self._repo.iter_commits(max_count=1000):
                author = commit.author.name
                contributors[author] = contributors.get(author, 0) + 1

            return {
                "total_commits": total_commits,
                "active_branch": active_branch,
                "top_contributors": sorted(contributors.items(), key=lambda x: x[1], reverse=True)[
                    :5
                ],
                "repo_path": str(self.repo_path),
            }
        except Exception as e:
            return {"error": str(e)}

    def is_valid(self) -> bool:
        """Check if the extractor has a valid Git repository."""
        return self._repo is not None
