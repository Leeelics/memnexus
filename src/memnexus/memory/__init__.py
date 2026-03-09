"""Memory and RAG system for MemNexus."""

# Legacy memory system (backward compatible)
from memnexus.memory.store import MemoryStore, MemoryEntry
from memnexus.memory.context import ContextManager
from memnexus.memory.rag import RAGPipeline, Document, DocumentChunker
from memnexus.memory.sync import (
    MemorySyncManager,
    MemorySyncBus,
    AgentMemoryBridge,
    SyncEvent,
)

# New advanced memory system (v2.0)
from memnexus.memory.core import (
    MemoryLayer,
    MemoryType,
    RetrievalResult,
    RetrievalStrategy,
    UncertaintyEstimate,
)
from memnexus.memory.layers import (
    HierarchicalMemoryManager,
    WorkingMemoryLayer,
    ShortTermMemoryLayer,
    LongTermMemoryLayer,
    LLMCompressor,
)
from memnexus.memory.retrieval import (
    AdaptiveRetriever,
    HybridRetriever,
)
from memnexus.memory.advanced_rag import (
    AdvancedRAG,
    RAGConfig,
    RAGQueryResult,
    RAGPipelineAdapter,
)

__all__ = [
    # Legacy exports (backward compatible)
    "MemoryStore",
    "MemoryEntry",
    "ContextManager",
    "RAGPipeline",
    "Document",
    "DocumentChunker",
    "MemorySyncManager",
    "MemorySyncBus",
    "AgentMemoryBridge",
    "SyncEvent",
    # New core types
    "MemoryLayer",
    "MemoryType",
    "RetrievalResult",
    "RetrievalStrategy",
    "UncertaintyEstimate",
    # New hierarchical memory
    "HierarchicalMemoryManager",
    "WorkingMemoryLayer",
    "ShortTermMemoryLayer",
    "LongTermMemoryLayer",
    "LLMCompressor",
    # New retrieval
    "AdaptiveRetriever",
    "HybridRetriever",
    # New RAG
    "AdvancedRAG",
    "RAGConfig",
    "RAGQueryResult",
    "RAGPipelineAdapter",
]
