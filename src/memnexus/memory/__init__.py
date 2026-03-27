"""Memory and RAG system for MemNexus.

This module provides core memory functionality for AI programming tools.

Stable Components (v1.0):
- MemoryStore: Vector storage using LanceDB
- MemoryEntry: Memory entry dataclass
- RAGPipeline: Basic RAG functionality
- Document/DocumentChunker: Document processing

Experimental Components (frozen in v1.0):
- AdvancedRAG: See memory/advanced_rag.py
- HierarchicalMemory: See memory/layers/
- AdaptiveRetriever: See memory/retrieval/
"""

# Core memory system (stable)
from memnexus.memory.store import MemoryStore, MemoryEntry
from memnexus.memory.context import ContextManager
from memnexus.memory.rag import RAGPipeline, Document, DocumentChunker

# Sync features require: pip install redis
# from memnexus.memory.sync import (
#     MemorySyncManager,
#     MemorySyncBus,
#     AgentMemoryBridge,
#     SyncEvent,
# )

# Core types
from memnexus.memory.core.types import (
    MemoryType,
    RetrievalResult,
)

# Git and Code integration (Week 2-3)
from memnexus.memory.git import GitMemoryExtractor, GitCommit
from memnexus.memory.code import CodeMemoryExtractor, CodeSymbol

__all__ = [
    # Core memory (stable)
    "MemoryStore",
    "MemoryEntry",
    "ContextManager",
    "RAGPipeline",
    "Document",
    "DocumentChunker",
    # Core types
    "MemoryType",
    "RetrievalResult",
    # Git integration (Week 2)
    "GitMemoryExtractor",
    "GitCommit",
    # Code integration (Week 3)
    "CodeMemoryExtractor",
    "CodeSymbol",
    # Note: Sync features require redis, import directly from memory.sync
]
