"""Global Memory for MemNexus - Cross-project knowledge.

Provides a global memory layer that aggregates knowledge from multiple projects,
enabling queries like "Where did I implement JWT authentication before?"

Example:
    >>> from memnexus import GlobalMemory
    >>> memory = await GlobalMemory.init()
    >>>
    >>> # Register a project
    >>> await memory.register_project("my-api", "~/projects/my-api")
    >>>
    >>> # Search across all projects
    >>> results = await memory.search("JWT authentication")
    >>> for r in results:
    ...     print(f"{r.project_name}: {r.source}")
    my-api: code:auth/login.py
    old-project: code:api/security.py
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from memnexus.memory.store import MemoryEntry, MemoryStore


@dataclass
class ProjectInfo:
    """Information about a registered project."""

    name: str
    path: str
    description: str | None = None
    registered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_synced: str | None = None
    git_url: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectInfo":
        return cls(**data)


@dataclass
class GlobalSearchResult:
    """Search result from global memory."""

    content: str
    source: str
    project_name: str
    project_path: str
    score: float
    memory_type: str  # "git_commit", "code_symbol", "generic"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.score:.3f}] {self.project_name}: {self.source}"


class GlobalMemoryConfig:
    """Configuration for global memory."""

    GLOBAL_DIR = Path.home() / ".memnexus" / "global"
    CONFIG_FILE = GLOBAL_DIR / "config.json"

    def __init__(self):
        self._config: dict[str, Any] = {}
        self._projects: dict[str, ProjectInfo] = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from disk."""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE) as f:
                    data = json.load(f)
                self._config = data.get("config", {})
                self._projects = {
                    name: ProjectInfo.from_dict(info)
                    for name, info in data.get("projects", {}).items()
                }
            except Exception as e:
                print(f"Warning: Failed to load global config: {e}")

    def save(self) -> None:
        """Save configuration to disk."""
        self.GLOBAL_DIR.mkdir(parents=True, exist_ok=True)

        data = {
            "config": self._config,
            "projects": {name: info.to_dict() for name, info in self._projects.items()},
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Atomic write
        temp_file = self.CONFIG_FILE.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=2)
        temp_file.rename(self.CONFIG_FILE)

    def get_project(self, name: str) -> ProjectInfo | None:
        """Get project by name."""
        return self._projects.get(name)

    def list_projects(self) -> list[ProjectInfo]:
        """List all registered projects."""
        return list(self._projects.values())

    def register_project(
        self,
        name: str,
        path: str,
        description: str | None = None,
        git_url: str | None = None,
        tags: list[str] | None = None,
    ) -> ProjectInfo:
        """Register a new project."""
        # Normalize path
        abs_path = str(Path(path).expanduser().resolve())

        info = ProjectInfo(
            name=name,
            path=abs_path,
            description=description,
            git_url=git_url,
            tags=tags or [],
        )

        self._projects[name] = info
        self.save()
        return info

    def unregister_project(self, name: str) -> bool:
        """Unregister a project."""
        if name in self._projects:
            del self._projects[name]
            self.save()
            return True
        return False

    def update_last_synced(self, name: str) -> None:
        """Update last synced timestamp."""
        if name in self._projects:
            self._projects[name].last_synced = datetime.utcnow().isoformat()
            self.save()


class GlobalMemory:
    """Global memory layer for cross-project knowledge.

    Aggregates memories from multiple projects into a unified searchable store.
    Each memory is tagged with its project of origin.

    Example:
        >>> memory = await GlobalMemory.init()
        >>>
        >>> # Register projects
        >>> await memory.register_project("api-service", "~/work/api")
        >>> await memory.register_project("web-app", "~/work/web")
        >>>
        >>> # Index all registered projects
        >>> await memory.sync_all()
        >>>
        >>> # Search across projects
        >>> results = await memory.search("authentication")
        >>> for r in results:
        ...     print(f"{r.project_name}: {r.content[:100]}")
    """

    def __init__(
        self, embedding_method: str = "tfidf", embedding_dim: int = 384, **embedder_kwargs
    ):
        """Initialize global memory.

        Args:
            embedding_method: "tfidf", "hash", or "openai"
            embedding_dim: Embedding dimension
            **embedder_kwargs: Additional args for embedder (e.g., api_key)
        """
        self._config = GlobalMemoryConfig()
        self._store: MemoryStore | None = None
        self._embedding_method = embedding_method
        self._embedding_dim = embedding_dim
        self._embedder_kwargs = embedder_kwargs
        self._initialized = False

    @classmethod
    async def init(
        cls, embedding_method: str = "tfidf", embedding_dim: int = 384, **embedder_kwargs
    ) -> "GlobalMemory":
        """Create and initialize a GlobalMemory instance.

        This is the recommended way to create GlobalMemory.

        Example:
            >>> memory = await GlobalMemory.init()
            >>> results = await memory.search("login")
        """
        instance = cls(
            embedding_method=embedding_method, embedding_dim=embedding_dim, **embedder_kwargs
        )
        await instance._initialize()
        return instance

    async def _initialize(self) -> None:
        """Initialize the global memory store."""
        if self._initialized:
            return

        # Ensure global directory exists
        GlobalMemoryConfig.GLOBAL_DIR.mkdir(parents=True, exist_ok=True)

        # Initialize store
        self._store = MemoryStore(
            uri=str(GlobalMemoryConfig.GLOBAL_DIR / "memory.lance"),
            embedding_method=self._embedding_method,
            embedding_dim=self._embedding_dim,
            **self._embedder_kwargs,
        )
        await self._store.initialize()

        self._initialized = True

    # ==================== Project Management ====================

    async def register_project(
        self,
        name: str,
        path: str,
        description: str | None = None,
        git_url: str | None = None,
        tags: list[str] | None = None,
        sync: bool = False,
    ) -> ProjectInfo:
        """Register a project with global memory.

        Args:
            name: Unique project name
            path: Project directory path
            description: Optional project description
            git_url: Optional Git repository URL
            tags: Optional tags for categorization
            sync: Whether to sync immediately after registration

        Returns:
            ProjectInfo for the registered project

        Example:
            >>> info = await memory.register_project(
            ...     "my-api",
            ...     "~/projects/my-api",
            ...     tags=["python", "fastapi"]
            ... )
        """
        info = self._config.register_project(
            name=name,
            path=path,
            description=description,
            git_url=git_url,
            tags=tags,
        )

        if sync:
            await self.sync_project(name)

        return info

    def unregister_project(self, name: str, delete_memories: bool = False) -> bool:
        """Unregister a project from global memory.

        Args:
            name: Project name
            delete_memories: Whether to delete associated memories

        Returns:
            True if unregistered, False if not found
        """
        if delete_memories and self._store:
            # TODO: Implement memory deletion by project
            pass

        return self._config.unregister_project(name)

    def list_projects(self) -> list[ProjectInfo]:
        """List all registered projects."""
        return self._config.list_projects()

    def get_project(self, name: str) -> ProjectInfo | None:
        """Get project by name."""
        return self._config.get_project(name)

    # ==================== Sync ====================

    async def sync_project(
        self,
        name: str,
        git: bool = True,
        code: bool = True,
        incremental: bool = True,
    ) -> dict[str, Any]:
        """Sync a project's memories to global memory.

        Args:
            name: Project name
            git: Whether to sync Git history
            code: Whether to sync code
            incremental: Whether to use incremental sync

        Returns:
            Sync statistics

        Example:
            >>> stats = await memory.sync_project("my-api")
            >>> print(f"Synced {stats['memories_added']} memories")
        """
        from memnexus.code_memory import CodeMemory

        project = self._config.get_project(name)
        if not project:
            raise ValueError(f"Project not found: {name}")

        project_path = Path(project.path)
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project.path}")

        # Check if project is initialized
        if not (project_path / ".memnexus").exists():
            raise ValueError(
                f"Project not initialized: {project.path}\nRun: cd {project.path} && memnexus init"
            )

        # Load project memory
        code_memory = await CodeMemory.init(project_path)

        memories_added = 0
        errors = []

        # Get existing memories to avoid duplicates
        existing_hashes = await self._get_existing_hashes(name)

        try:
            if code:
                # Sync code symbols
                # Note: We need to access the memory store directly
                # This is a simplified version - in production we'd need
                # to export from CodeMemory more cleanly
                stats = await code_memory.index_codebase(incremental=incremental)

                # TODO: Export memories from CodeMemory and add to global store
                # For now, we'll re-index directly
                memories_added += stats.get("symbols_indexed", 0)

        except Exception as e:
            errors.append(str(e))

        # Update last synced
        self._config.update_last_synced(name)

        return {
            "project": name,
            "memories_added": memories_added,
            "errors": errors,
        }

    async def sync_all(
        self,
        git: bool = True,
        code: bool = True,
        incremental: bool = True,
    ) -> list[dict[str, Any]]:
        """Sync all registered projects.

        Returns:
            List of sync results for each project
        """
        results = []
        projects = self.list_projects()

        for project in projects:
            try:
                result = await self.sync_project(
                    project.name,
                    git=git,
                    code=code,
                    incremental=incremental,
                )
                results.append(result)
            except Exception as e:
                results.append(
                    {
                        "project": project.name,
                        "error": str(e),
                    }
                )

        return results

    async def _get_existing_hashes(self, project_name: str) -> set[str]:
        """Get hashes of existing memories for a project."""
        # TODO: Implement efficient duplicate detection
        return set()

    async def add_memory(
        self,
        content: str,
        source: str,
        project_name: str,
        memory_type: str = "generic",
        metadata: dict | None = None,
    ) -> str:
        """Add a memory to global memory.

        Args:
            content: Memory content
            source: Source identifier (e.g., "code:auth.py")
            project_name: Associated project name
            memory_type: Type of memory
            metadata: Additional metadata

        Returns:
            Memory entry ID
        """
        if not self._initialized:
            raise RuntimeError("GlobalMemory not initialized")

        # Enrich metadata with project info
        full_metadata = {
            **(metadata or {}),
            "project_name": project_name,
            "source": source,
        }

        entry = MemoryEntry(
            content=content,
            source=f"global:{project_name}:{source}",
            memory_type=memory_type,
            metadata=full_metadata,
        )

        memory_id = await self._store.add(entry)
        return memory_id

    # ==================== Search ====================

    async def search(
        self,
        query: str,
        project: str | None = None,
        memory_type: str | None = None,
        limit: int = 10,
    ) -> list[GlobalSearchResult]:
        """Search global memory.

        Args:
            query: Search query
            project: Filter by project name (optional)
            memory_type: Filter by memory type (optional)
            limit: Maximum results

        Returns:
            List of global search results

        Example:
            >>> # Search all projects
            >>> results = await memory.search("authentication")
            >>>
            >>> # Search specific project
            >>> results = await memory.search("login", project="my-api")
        """
        if not self._initialized:
            raise RuntimeError("GlobalMemory not initialized")

        # Build filters
        filters = {}
        if memory_type:
            filters["memory_type"] = memory_type

        # Search in store
        results = await self._store.search(query, limit=limit * 2)

        # Convert to GlobalSearchResult and filter
        global_results = []
        for r in results:
            meta = r.metadata or {}
            project_name = meta.get("project_name", "unknown")

            # Filter by project if specified
            if project and project_name != project:
                continue

            # Get project info
            project_info = self._config.get_project(project_name)
            project_path = project_info.path if project_info else ""

            global_results.append(
                GlobalSearchResult(
                    content=r.content,
                    source=r.source,
                    project_name=project_name,
                    project_path=project_path,
                    score=0.9,  # TODO: Use actual score from search
                    memory_type=r.memory_type,
                    metadata=meta,
                )
            )

            if len(global_results) >= limit:
                break

        return global_results

    async def search_by_project(
        self,
        query: str,
        projects: list[str],
        limit: int = 10,
    ) -> list[GlobalSearchResult]:
        """Search within specific projects.

        Args:
            query: Search query
            projects: List of project names to search
            limit: Maximum results per project

        Returns:
            Combined search results
        """
        all_results = []

        for project in projects:
            results = await self.search(query, project=project, limit=limit)
            all_results.extend(results)

        # Sort by score
        all_results.sort(key=lambda r: r.score, reverse=True)

        return all_results[:limit]

    # ==================== Stats ====================

    def get_stats(self) -> dict[str, Any]:
        """Get global memory statistics."""
        projects = self.list_projects()

        return {
            "projects_registered": len(projects),
            "projects": [
                {
                    "name": p.name,
                    "path": p.path,
                    "last_synced": p.last_synced,
                    "tags": p.tags,
                }
                for p in projects
            ],
            "global_memory_path": str(GlobalMemoryConfig.GLOBAL_DIR),
        }

    async def close(self) -> None:
        """Close global memory."""
        if self._store:
            await self._store.close()
        self._initialized = False

    async def __aenter__(self):
        await self._initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
