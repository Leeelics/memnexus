"""MemNexus - Multi-Agent Collaboration Orchestration System."""

__version__ = "0.1.0"
__author__ = "Leeelics"
__license__ = "MIT"

try:
    from memnexus.core.config import settings
    from memnexus.core.session import Session, SessionManager
    from memnexus.agents.base import BaseAgent, AgentConfig
    from memnexus.memory.store import MemoryStore
except ImportError:
    # Dependencies not installed yet
    pass

__all__ = [
    "__version__",
    "settings",
    "Session",
    "SessionManager",
    "BaseAgent",
    "AgentConfig",
    "MemoryStore",
]
