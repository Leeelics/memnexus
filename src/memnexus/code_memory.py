"""MemNexus Code Memory - Main entry point.

This is the primary interface for using MemNexus as a library.

Example:
    >>> from memnexus import CodeMemory
    >>> memory = await CodeMemory.init("./my-project")
    >>> await memory.index_git_history()
    >>> results = await memory.search("login authentication")
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from memnexus.memory.store import MemoryEntry, MemoryStore
from memnexus.memory.git import GitCommit, GitMemoryExtractor
from memnexus.memory.code import CodeSymbol, CodeMemoryExtractor


@dataclass
class SearchResult:
    """Search result from code memory."""
    content: str
    source: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"[{self.score:.3f}] {self.source}: {self.content[:100]}..."


@dataclass
class GitSearchResult:
    """Git-specific search result."""
    commit_hash: str
    message: str
    author: str
    date: datetime
    files_changed: List[str]
    relevance_score: float
    diff_summary: str


class CodeMemory:
    """Main entry point for MemNexus Code Memory.
    
    This class provides a unified interface for:
    - Git history indexing and search
    - Code structure indexing and search
    - General memory storage and retrieval
    
    Usage:
        >>> memory = await CodeMemory.init("./my-project")
        >>> await memory.index_git_history(limit=100)
        >>> results = await memory.search("What changed in auth module?")
    
    Args:
        project_path: Path to the project directory
        config: Optional configuration dictionary
    """
    
    def __init__(self, project_path: Union[str, Path], config: Optional[Dict] = None):
        self.project_path = Path(project_path).resolve()
        self.config = config or self._load_config()
        
        # Core components
        self._memory_store: Optional[MemoryStore] = None
        self._git_extractor: Optional[GitMemoryExtractor] = None
        self._code_extractor: Optional[CodeMemoryExtractor] = None
        
        # State
        self._initialized = False
        self._stats = {
            "git_commits_indexed": 0,
            "code_symbols_indexed": 0,
            "total_memories": 0,
        }
    
    @classmethod
    async def init(cls, project_path: Union[str, Path] = ".") -> "CodeMemory":
        """Initialize CodeMemory for a project.
        
        This is the recommended way to create a CodeMemory instance.
        
        Args:
            project_path: Path to project directory (default: current directory)
            
        Returns:
            Initialized CodeMemory instance
            
        Raises:
            RuntimeError: If project is not initialized (run `memnexus init` first)
        """
        instance = cls(project_path)
        await instance._initialize()
        return instance
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from .memnexus/config.yaml."""
        config_path = self.project_path / ".memnexus" / "config.yaml"
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        return {}
    
    async def _initialize(self) -> None:
        """Initialize all components."""
        if self._initialized:
            return
        
        # Check if project is initialized
        memnexus_dir = self.project_path / ".memnexus"
        if not memnexus_dir.exists():
            raise RuntimeError(
                f"Project not initialized: {self.project_path}\n"
                f"Run: memnexus init"
            )
        
        # Initialize memory store
        self._memory_store = MemoryStore(
            uri=str(memnexus_dir / "memory.lance")
        )
        await self._memory_store.initialize()
        
        # Initialize extractors (lazy loading)
        try:
            self._git_extractor = GitMemoryExtractor(str(self.project_path))
        except Exception as e:
            # Git repo might not exist, that's ok
            self._git_extractor = None
        
        self._code_extractor = CodeMemoryExtractor()
        
        self._initialized = True
    
    # ==================== Git Integration (Week 2) ====================
    
    async def index_git_history(
        self, 
        limit: int = 1000,
        file_path: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Index Git commit history into memory.
        
        Args:
            limit: Maximum number of commits to index
            file_path: Optional specific file to index history for
            progress_callback: Optional callback(current, total) for progress updates
            
        Returns:
            Statistics about the indexing operation
            
        Example:
            >>> stats = await memory.index_git_history(limit=100)
            >>> print(f"Indexed {stats['commits_indexed']} commits")
        """
        if not self._initialized:
            raise RuntimeError("CodeMemory not initialized")
        
        if not self._git_extractor or not self._git_extractor.is_valid():
            raise RuntimeError("Git repository not found or not accessible")
        
        # Extract commits
        commits = self._git_extractor.extract_recent(
            file_path=file_path, 
            limit=limit
        )
        
        indexed_count = 0
        errors = []
        
        for i, commit in enumerate(commits):
            try:
                # Build rich content for embedding
                content_parts = [
                    f"Commit: {commit.hash}",
                    f"Author: {commit.author}",
                    f"Date: {commit.timestamp.isoformat()}",
                    f"Message: {commit.message}",
                    f"Files changed: {', '.join(commit.files_changed)}",
                ]
                
                if commit.diff_summary:
                    content_parts.append(f"Changes:\n{commit.diff_summary}")
                
                content = "\n\n".join(content_parts)
                
                entry = MemoryEntry(
                    content=content,
                    source=f"git:{commit.hash}",
                    memory_type="git_commit",
                    metadata={
                        "hash": commit.hash,
                        "author": commit.author,
                        "timestamp": commit.timestamp.isoformat(),
                        "files": commit.files_changed,
                        "message": commit.message,
                        "stats": commit.stats or {},
                    }
                )
                await self._memory_store.add(entry)
                indexed_count += 1
                
                if progress_callback:
                    progress_callback(i + 1, len(commits))
                    
            except Exception as e:
                errors.append(f"Failed to index commit {commit.hash}: {e}")
        
        self._stats["git_commits_indexed"] += indexed_count
        
        return {
            "commits_indexed": indexed_count,
            "total_commits": len(commits),
            "errors": errors,
            "file_path": file_path,
        }
    
    async def query_git_history(
        self, 
        query: str, 
        limit: int = 5,
        author: Optional[str] = None,
        since: Optional[datetime] = None,
        file_pattern: Optional[str] = None,
    ) -> List[GitSearchResult]:
        """Search Git history with semantic search.
        
        Args:
            query: Search query (e.g., "auth module changes")
            limit: Maximum results
            author: Optional filter by author name/email
            since: Optional filter by date (commits after this date)
            file_pattern: Optional filter by file path pattern
            
        Returns:
            List of matching commits with relevance scores
            
        Example:
            >>> results = await memory.query_git_history("fix login bug", limit=3)
            >>> for r in results:
            ...     print(f"{r.commit_hash}: {r.message}")
        """
        if not self._initialized:
            raise RuntimeError("CodeMemory not initialized")
        
        # Search in memory store
        results = await self._memory_store.search(query, limit=limit * 2)
        
        git_results = []
        for r in results:
            if r.memory_type != "git_commit":
                continue
            
            metadata = r.metadata or {}
            
            # Apply filters
            if author and author.lower() not in metadata.get("author", "").lower():
                continue
            
            if since:
                commit_date = datetime.fromisoformat(metadata.get("timestamp", "1970-01-01"))
                if commit_date < since:
                    continue
            
            if file_pattern:
                files = metadata.get("files", [])
                if not any(file_pattern in f for f in files):
                    continue
            
            git_results.append(GitSearchResult(
                commit_hash=metadata.get("hash", ""),
                message=metadata.get("message", ""),
                author=metadata.get("author", ""),
                date=datetime.fromisoformat(metadata.get("timestamp", "1970-01-01T00:00:00")),
                files_changed=metadata.get("files", []),
                relevance_score=0.9,  # TODO: Use actual score from search
                diff_summary="",  # Could extract from content if needed
            ))
            
            if len(git_results) >= limit:
                break
        
        return git_results
    
    async def get_file_history(self, file_path: str, limit: int = 20) -> List[GitSearchResult]:
        """Get commit history for a specific file.
        
        Args:
            file_path: Path to file (relative to repo root)
            limit: Maximum number of commits to return
            
        Returns:
            List of commits affecting this file
            
        Example:
            >>> history = await memory.get_file_history("auth/login.py")
            >>> for commit in history:
            ...     print(f"{commit.date}: {commit.message}")
        """
        if not self._initialized:
            raise RuntimeError("CodeMemory not initialized")
        
        if not self._git_extractor or not self._git_extractor.is_valid():
            raise RuntimeError("Git repository not accessible")
        
        # First, ensure this file's history is indexed
        # Search for existing entries
        results = await self._memory_store.search(
            f"file:{file_path}", 
            limit=limit
        )
        
        git_results = []
        for r in results:
            if r.memory_type != "git_commit":
                continue
            
            metadata = r.metadata or {}
            files = metadata.get("files", [])
            
            if file_path in files:
                git_results.append(GitSearchResult(
                    commit_hash=metadata.get("hash", ""),
                    message=metadata.get("message", ""),
                    author=metadata.get("author", ""),
                    date=datetime.fromisoformat(metadata.get("timestamp", "1970-01-01T00:00:00")),
                    files_changed=files,
                    relevance_score=1.0,
                    diff_summary="",
                ))
        
        # If not enough results, try to index more
        if len(git_results) < limit:
            await self.index_git_history(file_path=file_path, limit=limit)
            # Re-query
            return await self.get_file_history(file_path, limit)
        
        return git_results[:limit]
    
    async def get_repo_stats(self) -> Dict[str, Any]:
        """Get Git repository statistics.
        
        Returns:
            Dictionary with repository statistics
        """
        if not self._initialized:
            raise RuntimeError("CodeMemory not initialized")
        
        if not self._git_extractor or not self._git_extractor.is_valid():
            return {"error": "Git repository not accessible"}
        
        return self._git_extractor.get_repo_stats()
    
    # ==================== Code Integration (Week 3) ====================
    
    async def index_codebase(self, languages: Optional[List[str]] = None) -> int:
        """Index codebase structure into memory.
        
        Args:
            languages: List of languages to index (default: all supported)
            
        Returns:
            Number of symbols indexed
            
        Example:
            >>> count = await memory.index_codebase(["python", "typescript"])
            >>> print(f"Indexed {count} symbols")
        """
        if not self._initialized:
            raise RuntimeError("CodeMemory not initialized")
        
        # TODO: Week 3 - Implement full code indexing
        # For now, placeholder
        
        return 0
    
    async def search_code(self, query: str, language: Optional[str] = None) -> List[SearchResult]:
        """Search code symbols.
        
        Args:
            query: Search query (e.g., "login function")
            language: Filter by language
            
        Returns:
            List of matching code symbols
        """
        if not self._initialized:
            raise RuntimeError("CodeMemory not initialized")
        
        # TODO: Week 3 - Implement code search
        return []
    
    async def find_references(self, symbol: str) -> List[SearchResult]:
        """Find all references to a symbol.
        
        Args:
            symbol: Symbol name (e.g., "authenticate_user")
            
        Returns:
            List of references
        """
        if not self._initialized:
            raise RuntimeError("CodeMemory not initialized")
        
        # TODO: Week 3 - Implement reference search
        return []
    
    # ==================== General Memory ====================
    
    async def add(self, content: str, source: str, metadata: Optional[Dict] = None) -> str:
        """Add a memory entry.
        
        Args:
            content: Memory content
            source: Source identifier (e.g., "kimi", "claude")
            metadata: Optional metadata
            
        Returns:
            Memory entry ID
        """
        if not self._initialized:
            raise RuntimeError("CodeMemory not initialized")
        
        entry = MemoryEntry(
            content=content,
            source=source,
            memory_type="generic",
            metadata=metadata or {},
        )
        
        memory_id = await self._memory_store.add(entry)
        self._stats["total_memories"] += 1
        
        return memory_id
    
    async def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        """Search all memories.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching memories
        """
        if not self._initialized:
            raise RuntimeError("CodeMemory not initialized")
        
        results = await self._memory_store.search(query, limit=limit)
        
        return [
            SearchResult(
                content=r.content,
                source=r.source,
                score=0.9,  # TODO: Add proper scoring
                metadata=r.metadata,
            )
            for r in results
        ]
    
    # ==================== Stats & Info ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get indexing statistics."""
        return {
            **self._stats,
            "project_path": str(self.project_path),
            "initialized": self._initialized,
            "has_git": self._git_extractor is not None and self._git_extractor.is_valid(),
        }
    
    async def close(self) -> None:
        """Close all resources."""
        if self._memory_store:
            # MemoryStore doesn't have close, but future implementations might
            pass
        self._initialized = False
    
    async def __aenter__(self):
        await self._initialize()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
