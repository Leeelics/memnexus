"""Index state management for incremental indexing.

Tracks what has been indexed to enable incremental updates.
"""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class FileIndexState:
    """Index state for a single file."""

    path: str
    last_modified: float  # Unix timestamp
    content_hash: str  # MD5 hash of content
    indexed_at: str  # ISO format datetime
    symbol_count: int  # Number of symbols indexed


@dataclass
class GitIndexState:
    """Index state for Git history."""

    last_commit_hash: str
    last_commit_timestamp: str  # ISO format
    indexed_commits: set[str] = field(default_factory=set)
    total_indexed: int = 0


@dataclass
class IndexState:
    """Overall index state for a project.

    Stored in .memnexus/index_state.json
    """

    project_path: str
    version: str = "1.0"

    # Git state
    git_state: GitIndexState | None = None

    # Code state: path -> FileIndexState
    file_states: dict[str, FileIndexState] = field(default_factory=dict)

    # Metadata
    last_full_index: str | None = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert set to list for JSON
        if self.git_state and hasattr(self.git_state, "indexed_commits"):
            data["git_state"]["indexed_commits"] = list(self.git_state.indexed_commits)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "IndexState":
        """Create from dictionary."""
        # Convert list back to set
        git_state_data = data.get("git_state")
        git_state = None
        if git_state_data:
            indexed_commits = set(git_state_data.get("indexed_commits", []))
            git_state = GitIndexState(
                last_commit_hash=git_state_data["last_commit_hash"],
                last_commit_timestamp=git_state_data["last_commit_timestamp"],
                indexed_commits=indexed_commits,
                total_indexed=git_state_data.get("total_indexed", 0),
            )

        # Parse file states
        file_states = {}
        for path, state_data in data.get("file_states", {}).items():
            file_states[path] = FileIndexState(**state_data)

        return cls(
            project_path=data["project_path"],
            version=data.get("version", "1.0"),
            git_state=git_state,
            file_states=file_states,
            last_full_index=data.get("last_full_index"),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
        )


class IndexStateManager:
    """Manages index state for incremental indexing.

    Example:
        >>> manager = IndexStateManager("./my-project")
        >>> state = manager.load_state()
        >>>
        >>> # Check if file needs re-indexing
        >>> if manager.should_index_file("src/auth.py"):
        ...     # Index the file
        ...     manager.update_file_state("src/auth.py", content_hash="abc123", symbol_count=5)
    """

    def __init__(self, project_path: str | Path):
        self.project_path = Path(project_path).resolve()
        self.state_file = self.project_path / ".memnexus" / "index_state.json"
        self._state: IndexState | None = None

    def load_state(self) -> IndexState:
        """Load index state from disk or create new."""
        if self._state is not None:
            return self._state

        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    data = json.load(f)
                self._state = IndexState.from_dict(data)
                return self._state
            except Exception as e:
                print(f"Warning: Failed to load index state: {e}")

        # Create new state
        self._state = IndexState(project_path=str(self.project_path))
        return self._state

    def save_state(self) -> None:
        """Save index state to disk."""
        if self._state is None:
            return

        # Update timestamp
        self._state.updated_at = datetime.utcnow().isoformat()

        # Ensure directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Write atomically
        temp_file = self.state_file.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(self._state.to_dict(), f, indent=2)
        temp_file.rename(self.state_file)

    def should_index_file(self, file_path: str) -> bool:
        """Check if a file needs to be indexed/re-indexed.

        Returns True if:
        - File hasn't been indexed before
        - File has been modified since last index
        - File content hash has changed
        """
        state = self.load_state()
        full_path = self.project_path / file_path

        if not full_path.exists():
            return False

        # Check if we have state for this file
        if file_path not in state.file_states:
            return True

        file_state = state.file_states[file_path]

        # Check modification time
        current_mtime = full_path.stat().st_mtime
        if current_mtime > file_state.last_modified:
            # Modified, check if content actually changed
            current_hash = self._compute_file_hash(full_path)
            return current_hash != file_state.content_hash

        return False

    def update_file_state(
        self, file_path: str, symbol_count: int = 0, content_hash: str | None = None
    ) -> None:
        """Update index state for a file."""
        state = self.load_state()
        full_path = self.project_path / file_path

        if not full_path.exists():
            return

        if content_hash is None:
            content_hash = self._compute_file_hash(full_path)

        file_state = FileIndexState(
            path=file_path,
            last_modified=full_path.stat().st_mtime,
            content_hash=content_hash,
            indexed_at=datetime.utcnow().isoformat(),
            symbol_count=symbol_count,
        )

        state.file_states[file_path] = file_state
        self.save_state()

    def remove_file_state(self, file_path: str) -> None:
        """Remove a file from index state (file deleted)."""
        state = self.load_state()
        if file_path in state.file_states:
            del state.file_states[file_path]
            self.save_state()

    def get_git_state(self) -> GitIndexState | None:
        """Get current Git index state."""
        state = self.load_state()
        return state.git_state

    def update_git_state(
        self,
        last_commit_hash: str,
        last_commit_timestamp: str,
        new_commits: list[str],
        total_indexed: int,
    ) -> None:
        """Update Git index state."""
        state = self.load_state()

        if state.git_state is None:
            state.git_state = GitIndexState(
                last_commit_hash=last_commit_hash,
                last_commit_timestamp=last_commit_timestamp,
                indexed_commits=set(new_commits),
                total_indexed=total_indexed,
            )
        else:
            state.git_state.last_commit_hash = last_commit_hash
            state.git_state.last_commit_timestamp = last_commit_timestamp
            state.git_state.indexed_commits.update(new_commits)
            state.git_state.total_indexed = total_indexed

        self.save_state()

    def get_unindexed_commits(self, all_commits: list[str]) -> list[str]:
        """Get list of commits that haven't been indexed yet."""
        state = self.load_state()

        if state.git_state is None:
            return all_commits

        indexed = state.git_state.indexed_commits
        return [c for c in all_commits if c not in indexed]

    def reset_code_state(self) -> None:
        """Reset only code index state (keep Git state)."""
        state = self.load_state()
        state.file_states = {}
        state.last_full_index = None
        self.save_state()

    def reset_git_state(self) -> None:
        """Reset only Git index state."""
        state = self.load_state()
        state.git_state = None
        self.save_state()

    def reset_all(self) -> None:
        """Reset all index state (force full re-index)."""
        self._state = IndexState(project_path=str(self.project_path))
        self.save_state()

    def get_stats(self) -> dict:
        """Get index state statistics."""
        state = self.load_state()
        return {
            "files_tracked": len(state.file_states),
            "git_commits_indexed": len(state.git_state.indexed_commits) if state.git_state else 0,
            "last_updated": state.updated_at,
        }

    @staticmethod
    def _compute_file_hash(file_path: Path) -> str:
        """Compute MD5 hash of file content."""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
