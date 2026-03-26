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

__version__ = "0.2.1"
__author__ = "Leeelics"
__license__ = "MIT"

# Main entry point
try:
    from memnexus.code_memory import CodeMemory, SearchResult
except ImportError:
    # Dependencies not installed
    pass

# Legacy exports (for backward compatibility)
try:
    from memnexus.memory import MemoryStore, MemoryEntry
    from memnexus.memory.git import GitMemoryExtractor, GitCommit
    from memnexus.memory.code import CodeMemoryExtractor, CodeSymbol
except ImportError:
    pass

__all__ = [
    # Main API
    "CodeMemory",
    "SearchResult",
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
