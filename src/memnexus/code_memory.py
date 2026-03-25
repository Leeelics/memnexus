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
    
    async def index_codebase(
        self, 
        languages: Optional[List[str]] = None,
        file_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Index codebase structure into memory.
        
        Args:
            languages: List of languages to index (default: all supported)
            file_patterns: File patterns to include (default: based on languages)
            exclude_patterns: Patterns to exclude
            progress_callback: Optional callback(current, total, file)
            
        Returns:
            Statistics about the indexing operation
            
        Example:
            >>> result = await memory.index_codebase(["python"])
            >>> print(f"Indexed {result['symbols_indexed']} symbols from {result['files_processed']} files")
        """
        if not self._initialized:
            raise RuntimeError("CodeMemory not initialized")
        
        if not self._code_extractor:
            raise RuntimeError("Code extractor not available")
        
        # Determine file patterns from languages
        if file_patterns is None:
            if languages is None:
                file_patterns = ["*.py"]  # Default to Python
            else:
                pattern_map = {
                    "python": "*.py",
                    "javascript": "*.js",
                    "typescript": "*.ts",
                }
                file_patterns = [pattern_map.get(lang, f"*.{lang}") for lang in languages]
        
        # Extract all chunks
        chunks_by_file = self._code_extractor.extract_from_directory(
            str(self.project_path),
            patterns=file_patterns,
            exclude_patterns=exclude_patterns
        )
        
        indexed_count = 0
        errors = []
        files_processed = 0
        
        total_files = len(chunks_by_file)
        
        for file_path, chunks in chunks_by_file.items():
            files_processed += 1
            
            if progress_callback:
                progress_callback(files_processed, total_files, file_path)
            
            for chunk in chunks:
                try:
                    # Build rich content for embedding
                    content_parts = [
                        f"# {chunk.symbol.name if chunk.symbol else 'Code Chunk'}",
                        f"# File: {chunk.symbol.file_path if chunk.symbol else 'unknown'}",
                        f"# Type: {chunk.chunk_type}",
                        "",
                        chunk.context,
                        "",
                        chunk.content,
                    ]
                    
                    content = "\n".join(content_parts)
                    
                    entry = MemoryEntry(
                        content=content,
                        source=f"code:{chunk.symbol.file_path if chunk.symbol else 'unknown'}",
                        memory_type="code_symbol",
                        metadata={
                            "symbol_name": chunk.symbol.name if chunk.symbol else None,
                            "symbol_type": chunk.symbol.symbol_type if chunk.symbol else chunk.chunk_type,
                            "file_path": chunk.symbol.file_path if chunk.symbol else None,
                            "start_line": chunk.symbol.start_line if chunk.symbol else None,
                            "end_line": chunk.symbol.end_line if chunk.symbol else None,
                            "language": chunk.language,
                            "signature": chunk.symbol.signature if chunk.symbol else None,
                            "docstring": chunk.symbol.docstring if chunk.symbol else None,
                        }
                    )
                    
                    await self._memory_store.add(entry)
                    indexed_count += 1
                    
                except Exception as e:
                    errors.append(f"Failed to index chunk from {file_path}: {e}")
        
        self._stats["code_symbols_indexed"] += indexed_count
        
        return {
            "symbols_indexed": indexed_count,
            "files_processed": files_processed,
            "errors": errors,
            "languages": languages or ["python"],
        }
    
    async def search_code(
        self, 
        query: str, 
        language: Optional[str] = None,
        symbol_type: Optional[str] = None,
        file_pattern: Optional[str] = None,
        limit: int = 5
    ) -> List[SearchResult]:
        """Search code symbols.
        
        Args:
            query: Search query (e.g., "login function")
            language: Filter by language (e.g., "python")
            symbol_type: Filter by type ("function", "class", "method")
            file_pattern: Filter by file path pattern
            limit: Maximum results
            
        Returns:
            List of matching code symbols
            
        Example:
            >>> results = await memory.search_code("authenticate", symbol_type="function")
            >>> for r in results:
            ...     print(f"{r.metadata['symbol_name']}: {r.metadata['file_path']}")
        """
        if not self._initialized:
            raise RuntimeError("CodeMemory not initialized")
        
        # Search in memory store
        results = await self._memory_store.search(query, limit=limit * 2)
        
        code_results = []
        for r in results:
            if r.memory_type != "code_symbol":
                continue
            
            metadata = r.metadata or {}
            
            # Apply filters
            if language and metadata.get("language") != language:
                continue
            
            if symbol_type and metadata.get("symbol_type") != symbol_type:
                continue
            
            if file_pattern and file_pattern not in metadata.get("file_path", ""):
                continue
            
            code_results.append(SearchResult(
                content=r.content,
                source=r.source,
                score=0.9,  # TODO: Use actual score
                metadata=metadata,
            ))
            
            if len(code_results) >= limit:
                break
        
        return code_results
    
    async def find_symbol(self, name: str) -> Optional[SearchResult]:
        """Find a specific symbol by name.
        
        Args:
            name: Symbol name (e.g., "authenticate_user" or "AuthController.login")
            
        Returns:
            SearchResult if found, None otherwise
        """
        if not self._initialized:
            raise RuntimeError("CodeMemory not initialized")
        
        # Search for exact match
        results = await self._memory_store.search(name, limit=10)
        
        for r in results:
            if r.memory_type != "code_symbol":
                continue
            
            metadata = r.metadata or {}
            symbol_name = metadata.get("symbol_name", "")
            
            # Exact match or ends with name (for methods)
            if symbol_name == name or symbol_name.endswith(f".{name}"):
                return SearchResult(
                    content=r.content,
                    source=r.source,
                    score=1.0,
                    metadata=metadata,
                )
        
        return None
    
    async def get_code_stats(self) -> Dict[str, Any]:
        """Get codebase statistics.
        
        Returns:
            Dictionary with code statistics
        """
        if not self._initialized:
            raise RuntimeError("CodeMemory not initialized")
        
        if not self._code_extractor:
            return {"error": "Code extractor not available"}
        
        # Get summary of project
        summary = self._code_extractor.get_file_summary(str(self.project_path))
        
        return {
            "project_path": str(self.project_path),
            "symbols_indexed": self._stats["code_symbols_indexed"],
            **summary,
        }
    
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
