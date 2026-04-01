"""MemNexus - Code Memory for AI Programming Tools.

MemNexus provides persistent memory for AI coding assistants,
enabling them to remember project context across sessions.

Quick Start:
    >>> from memnexus import CodeMemory
    >>> memory = await CodeMemory.init("./my-project")
    >>> await memory.index_git_history()
    >>> results = await memory.search("login authentication")

For more information, see: https://github.com/Leeelics/MemNexus
"""

import contextlib

__version__ = "0.4.0"
__author__ = "Leeelics"
__license__ = "MIT"

# Main entry point
with contextlib.suppress(ImportError):
    from memnexus.code_memory import CodeMemory, SearchResult

# Global memory (cross-project)
with contextlib.suppress(ImportError):
    from memnexus.global_memory import GlobalMemory, GlobalSearchResult, ProjectInfo

# Legacy exports (for backward compatibility)
with contextlib.suppress(ImportError):
    from memnexus.memory import MemoryEntry, MemoryStore
    from memnexus.memory.code import CodeMemoryExtractor, CodeSymbol
    from memnexus.memory.git import GitCommit, GitMemoryExtractor

__all__ = [
    # Main API
    "CodeMemory",
    "SearchResult",
    # Global Memory
    "GlobalMemory",
    "GlobalSearchResult",
    "ProjectInfo",
    # Legacy (backward compatibility)
    "MemoryStore",
    "MemoryEntry",
    "GitMemoryExtractor",
    "GitCommit",
    "CodeMemoryExtractor",
    "CodeSymbol",
    # Metadata
    "__version__",
]
