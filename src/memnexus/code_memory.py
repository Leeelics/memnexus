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
        self._git_extractor = GitMemoryExtractor(str(self.project_path))
        self._code_extractor = CodeMemoryExtractor()
        
        self._initialized = True
    
    # ==================== Git Integration (Week 2) ====================
    
    async def index_git_history(self, limit: int = 1000) -> int:
        """Index Git commit history into memory.
        
        Args:
            limit: Maximum number of commits to index
            
        Returns:
            Number of commits indexed
            
        Example:
            >>> count = await memory.index_git_history(limit=100)
            >>> print(f"Indexed {count} commits")
        """
        if not self._initialized:
            raise RuntimeError("CodeMemory not initialized")
        
        # TODO: Week 2 - Implement full Git indexing
        # For now, just extract and store basic info
        
        commits = self._git_extractor.extract_recent(limit=limit)
        
        for commit in commits:
            entry = MemoryEntry(
                content=f"{commit.message}\n\n{commit.diff_summary}",
                source=f"git:{commit.hash}",
                memory_type="git_commit",
                metadata={
                    "hash": commit.hash,
                    "author": commit.author,
                    "timestamp": commit.timestamp.isoformat(),
                    "files": commit.files_changed,
                }
            )
            await self._memory_store.add(entry)
        
        self._stats["git_commits_indexed"] = len(commits)
        return len(commits)
    
    async def query_git_history(self, query: str, limit: int = 5) -> List[SearchResult]:
        """Search Git history.
        
        Args:
            query: Search query (e.g., "auth module changes")
            limit: Maximum results
            
        Returns:
            List of matching commits
        """
        if not self._initialized:
            raise RuntimeError("CodeMemory not initialized")
        
        # Search in memory store with git type filter
        results = await self._memory_store.search(query, limit=limit)
        
        return [
            SearchResult(
                content=r.content,
                source=r.source,
                score=0.9,  # TODO: Add proper scoring
                metadata=r.metadata,
            )
            for r in results
            if r.memory_type == "git_commit"
        ]
    
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
