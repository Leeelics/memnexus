"""MemNexus - Code Memory for AI Programming Tools.

MemNexus provides persistent memory for AI coding assistants,
enabling them to remember project context across sessions.

Example:
    >>> from memnexus import MemoryStore
    >>> store = MemoryStore()
    >>> await store.initialize()
    >>> await store.add(content="User wants login feature", source="kimi")
"""

__version__ = "0.1.0"
__author__ = "Leeelics"
__license__ = "MIT"

try:
    from memnexus.core.config import settings
    from memnexus.core.session import Session, SessionManager
    from memnexus.memory import MemoryStore, MemoryEntry
except ImportError:
    # Dependencies not installed yet
    pass

__all__ = [
    "__version__",
    "settings",
    "Session",
    "SessionManager",
    "MemoryStore",
    "MemoryEntry",
]
