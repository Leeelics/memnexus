"""File watcher for real-time indexing.

Uses watchfiles to monitor project files and automatically update index.
"""

import asyncio
from pathlib import Path
from typing import Any, Callable

from watchfiles import Change, DefaultFilter, watch

from memnexus.code_memory import CodeMemory


class FileWatcher:
    """Watch project files for changes and trigger incremental indexing.

    Example:
        >>> watcher = FileWatcher("./my-project")
        >>> await watcher.start()
        >>> # Files are now being watched
        >>> await watcher.stop()
    """

    def __init__(
        self,
        project_path: str | Path,
        callback: Callable[[list[tuple[Change, str]], CodeMemory], Any] | None = None,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ):
        """Initialize file watcher.

        Args:
            project_path: Path to project directory
            callback: Optional callback for change events
            include_patterns: File patterns to include (e.g., ["*.py", "*.js"])
            exclude_patterns: File patterns to exclude
        """
        self.project_path = Path(project_path).resolve()
        self.callback = callback
        self.include_patterns = include_patterns or ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"]
        self.exclude_patterns = exclude_patterns or [
            "*.pyc",
            "__pycache__/*",
            "node_modules/*",
            ".git/*",
            ".venv/*",
            "*.egg-info/*",
            "build/*",
            "dist/*",
            ".pytest_cache/*",
            ".mypy_cache/*",
        ]
        self._stop_event = asyncio.Event()
        self._watch_task: asyncio.Task | None = None
        self._memory: CodeMemory | None = None

    async def _get_memory(self) -> CodeMemory:
        """Get or initialize CodeMemory instance."""
        if self._memory is None:
            self._memory = await CodeMemory.init(self.project_path)
        return self._memory

    async def _handle_changes(self, changes: set[tuple[Change, str]]) -> None:
        """Process file changes.

        Args:
            changes: Set of (change_type, file_path) tuples
        """
        if not changes:
            return

        # Filter relevant changes
        relevant_changes = []
        for change_type, path_str in changes:
            path = Path(path_str)

            # Skip directories
            if path.is_dir():
                continue

            # Check exclude patterns
            if self._matches_patterns(path, self.exclude_patterns):
                continue

            # Check include patterns
            if not self._matches_patterns(path, self.include_patterns):
                continue

            relevant_changes.append((change_type, path_str))

        if not relevant_changes:
            return

        # Call custom callback if provided
        if self.callback:
            try:
                memory = await self._get_memory()
                await self.callback(relevant_changes, memory)
                return
            except Exception as e:
                print(f"Callback error: {e}")

        # Default: incremental index
        await self._default_handler(relevant_changes)

    def _matches_patterns(self, path: Path, patterns: list[str]) -> bool:
        """Check if path matches any of the glob patterns."""
        for pattern in patterns:
            if path.match(pattern):
                return True
            # Also check parent directories
            for parent in path.parents:
                if (parent / path.name).match(pattern):
                    return True
        return False

    async def _default_handler(self, changes: list[tuple[Change, str]]) -> None:
        """Default change handler - incremental indexing."""
        added = []
        modified = []
        deleted = []

        for change_type, path_str in changes:
            if change_type == Change.added:
                added.append(path_str)
            elif change_type == Change.modified:
                modified.append(path_str)
            elif change_type == Change.deleted:
                deleted.append(path_str)

        print(f"\n[FileWatcher] Detected changes:")
        if added:
            print(f"  Added: {len(added)} files")
        if modified:
            print(f"  Modified: {len(modified)} files")
        if deleted:
            print(f"  Deleted: {len(deleted)} files")

        # Index new and modified files
        files_to_index = added + modified
        if files_to_index:
            try:
                memory = await self._get_memory()
                # Use incremental indexing
                result = await memory.index_codebase(
                    file_paths=files_to_index,
                    incremental=True,
                )
                print(f"  Indexed: {result.get('files_processed', 0)} files")
            except Exception as e:
                print(f"  Indexing error: {e}")

    async def _watch_loop(self) -> None:
        """Main watch loop."""
        # Create custom filter
        watch_filter = DefaultFilter(
            ignore_entity_patterns=self.exclude_patterns,
        )

        try:
            for changes in watch(
                self.project_path,
                watch_filter=watch_filter,
                stop_event=self._stop_event,
                recursive=True,
            ):
                await self._handle_changes(changes)
        except Exception as e:
            print(f"Watch error: {e}")

    async def start(self) -> None:
        """Start watching files."""
        if self._watch_task is not None:
            return

        print(f"[FileWatcher] Starting watch on {self.project_path}")
        print(f"  Include: {', '.join(self.include_patterns)}")
        print(f"  Press Ctrl+C to stop\n")

        self._stop_event.clear()
        self._watch_task = asyncio.create_task(self._watch_loop())

        # Wait for task to complete (or be cancelled)
        try:
            await self._watch_task
        except asyncio.CancelledError:
            pass

    async def stop(self) -> None:
        """Stop watching files."""
        print("\n[FileWatcher] Stopping...")
        self._stop_event.set()

        if self._watch_task and not self._watch_task.done():
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass

        self._watch_task = None
        print("[FileWatcher] Stopped")

    async def __aenter__(self) -> "FileWatcher":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()
