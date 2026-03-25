"""FastAPI server for MemNexus Code Memory.

This is a lightweight HTTP wrapper around the CodeMemory library.
For programmatic use, consider using the library directly:

    from memnexus import CodeMemory
    memory = await CodeMemory.init("./my-project")

Usage:
    memnexus server  # Starts server on http://localhost:8080
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from memnexus.code_memory import CodeMemory, SearchResult, GitSearchResult

# Global state
_code_memory: Optional[CodeMemory] = None
_project_path: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    global _code_memory
    
    print("Starting MemNexus Code Memory Server")
    print(f"Project: {_project_path or 'Not specified (use --project)'}")
    
    # Initialize CodeMemory if project path is provided
    if _project_path:
        try:
            _code_memory = await CodeMemory.init(_project_path)
            print("✓ CodeMemory initialized")
        except Exception as e:
            print(f"⚠ Failed to initialize: {e}")
            print("  Run: memnexus init")
    
    yield
    
    # Shutdown
    if _code_memory:
        await _code_memory.close()
    print("Shutting down...")


app = FastAPI(
    title="MemNexus Code Memory",
    version="0.1.0",
    description="Persistent memory for AI programming tools",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "MemNexus Code Memory",
        "version": "0.1.0",
        "status": "running",
        "initialized": _code_memory is not None,
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "initialized": _code_memory is not None,
        "project": _project_path,
    }


@app.get("/stats")
async def stats():
    """Get indexing statistics."""
    if not _code_memory:
        raise HTTPException(status_code=503, detail="CodeMemory not initialized")
    
    return _code_memory.get_stats()


# ==================== Search API ====================

@app.get("/api/v1/search")
async def search(query: str, limit: int = 5) -> List[Dict]:
    """Search all memories.
    
    Args:
        query: Search query
        limit: Maximum number of results
        
    Returns:
        List of search results
        
    Example:
        GET /api/v1/search?query=login&limit=3
    """
    if not _code_memory:
        raise HTTPException(status_code=503, detail="CodeMemory not initialized")
    
    results = await _code_memory.search(query, limit=limit)
    return [_result_to_dict(r) for r in results]


@app.post("/api/v1/memory")
async def add_memory(data: Dict) -> Dict:
    """Add a memory entry.
    
    Args:
        data: Memory data with 'content', 'source', optional 'metadata'
        
    Returns:
        Memory entry ID
        
    Example:
        POST /api/v1/memory
        {
            "content": "User wants login feature",
            "source": "kimi",
            "metadata": {"session_id": "abc123"}
        }
    """
    if not _code_memory:
        raise HTTPException(status_code=503, detail="CodeMemory not initialized")
    
    memory_id = await _code_memory.add(
        content=data["content"],
        source=data["source"],
        metadata=data.get("metadata"),
    )
    
    return {"id": memory_id, "status": "added"}


# ==================== Git API (Week 2) ====================

@app.post("/api/v1/git/index")
async def index_git(limit: int = 1000) -> Dict:
    """Index Git history.
    
    Args:
        limit: Maximum number of commits to index
        
    Returns:
        Number of commits indexed
    """
    if not _code_memory:
        raise HTTPException(status_code=503, detail="CodeMemory not initialized")
    
    result = await _code_memory.index_git_history(limit=limit)
    return {
        "indexed": result.get("commits_indexed", 0),
        "total": result.get("total_commits", 0),
        "type": "git_commits",
        "errors": result.get("errors", []),
    }


@app.get("/api/v1/git/search")
async def search_git(query: str, limit: int = 5) -> List[Dict]:
    """Search Git history.
    
    Args:
        query: Search query
        limit: Maximum number of results
        
    Example:
        GET /api/v1/git/search?query=auth%20changes&limit=5
    """
    if not _code_memory:
        raise HTTPException(status_code=503, detail="CodeMemory not initialized")
    
    results = await _code_memory.query_git_history(query, limit=limit)
    return [_git_result_to_dict(r) for r in results]


# ==================== Code API (Week 3) ====================

@app.post("/api/v1/code/index")
async def index_code(
    languages: Optional[List[str]] = None,
    file_patterns: Optional[List[str]] = None
) -> Dict:
    """Index codebase.
    
    Args:
        languages: List of languages to index (default: python)
        file_patterns: File patterns to include
        
    Returns:
        Indexing statistics
        
    Example:
        POST /api/v1/code/index
        {"languages": ["python"], "file_patterns": ["*.py"]}
    """
    if not _code_memory:
        raise HTTPException(status_code=503, detail="CodeMemory not initialized")
    
    result = await _code_memory.index_codebase(
        languages=languages,
        file_patterns=file_patterns
    )
    return {
        "indexed": result.get("symbols_indexed", 0),
        "files_processed": result.get("files_processed", 0),
        "type": "code_symbols",
        "languages": result.get("languages", []),
        "errors": result.get("errors", []),
    }


@app.get("/api/v1/code/search")
async def search_code(
    query: str, 
    language: Optional[str] = None,
    symbol_type: Optional[str] = None,
    limit: int = 5
) -> List[Dict]:
    """Search code symbols.
    
    Args:
        query: Search query
        language: Filter by language
        symbol_type: Filter by type (function, class, method)
        limit: Maximum results
        
    Example:
        GET /api/v1/code/search?query=authenticate&language=python&type=function
    """
    if not _code_memory:
        raise HTTPException(status_code=503, detail="CodeMemory not initialized")
    
    results = await _code_memory.search_code(
        query, 
        language=language,
        symbol_type=symbol_type,
        limit=limit
    )
    return [_result_to_dict(r) for r in results]


@app.get("/api/v1/code/symbol/{name}")
async def find_symbol(name: str) -> Dict:
    """Find a specific symbol by name.
    
    Args:
        name: Symbol name (e.g., "authenticate_user")
        
    Returns:
        Symbol information if found
        
    Example:
        GET /api/v1/code/symbol/authenticate_user
    """
    if not _code_memory:
        raise HTTPException(status_code=503, detail="CodeMemory not initialized")
    
    result = await _code_memory.find_symbol(name)
    if not result:
        raise HTTPException(status_code=404, detail=f"Symbol '{name}' not found")
    
    return _result_to_dict(result)


# ==================== Helpers ====================

def _result_to_dict(result: SearchResult) -> Dict:
    """Convert SearchResult to dict."""
    return {
        "content": result.content,
        "source": result.source,
        "score": result.score,
        "metadata": result.metadata,
    }


def _git_result_to_dict(result: GitSearchResult) -> Dict:
    """Convert GitSearchResult to dict."""
    return {
        "commit_hash": result.commit_hash,
        "message": result.message,
        "author": result.author,
        "date": result.date.isoformat(),
        "files_changed": result.files_changed,
        "relevance_score": result.relevance_score,
        "diff_summary": result.diff_summary,
    }


def start_server(project_path: Optional[str] = None, host: str = "127.0.0.1", port: int = 8080):
    """Start the server programmatically.
    
    Args:
        project_path: Path to project (optional)
        host: Host to bind to
        port: Port to bind to
    """
    import uvicorn
    
    global _project_path
    _project_path = project_path
    
    uvicorn.run(app, host=host, port=port)
