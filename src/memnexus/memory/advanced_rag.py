"""
Advanced RAG System for MemNexus.

.. warning::
    EXPERIMENTAL - Frozen in v1.0
    This module contains experimental features that are not actively maintained.
    For stable functionality, use RAGPipeline instead.
    
    Features in this file:
    - Adaptive retrieval (SEAKR-inspired)
    - Hierarchical memory (MELODI-inspired)
    - Hybrid search (vector + keyword)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from memnexus.memory.core import MemoryEntry, RetrievalResult, RetrievalStrategy
from memnexus.memory.layers import HierarchicalMemoryManager
from memnexus.memory.retrieval import AdaptiveRetriever, HybridRetriever


@dataclass
class RAGConfig:
    """Configuration for AdvancedRAG."""
    
    # Retrieval strategy
    strategy: RetrievalStrategy = RetrievalStrategy.ADAPTIVE
    
    # Adaptive retrieval settings
    adaptive_threshold: float = 0.6
    
    # Hybrid retrieval weights
    vector_weight: float = 0.7
    keyword_weight: float = 0.3
    
    # Memory layer settings
    working_memory_capacity: int = 10
    short_term_capacity: int = 50
    
    # Context building
    max_context_tokens: int = 4000
    include_sources: bool = True


class AdvancedRAG:
    """
    Advanced Retrieval-Augmented Generation system.
    
    Features:
    1. Adaptive retrieval - only retrieve when uncertain
    2. Hierarchical memory - working/short-term/long-term
    3. Hybrid search - combine vector and keyword
    4. Intelligent context building
    
    Example:
        >>> rag = AdvancedRAG(vector_store=my_store)
        >>> await rag.initialize()
        >>> 
        >>> # Add documents
        >>> await rag.add_document("User wants a REST API...")
        >>> 
        >>> # Query with adaptive retrieval
        >>> result = await rag.query("What API design patterns should I use?")
        >>> print(result.context)
    """
    
    def __init__(
        self,
        session_id: str,
        vector_store=None,
        llm_client=None,
        config: Optional[RAGConfig] = None,
    ):
        self.session_id = session_id
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.config = config or RAGConfig()
        
        # Initialize hierarchical memory
        self.memory_manager = HierarchicalMemoryManager(
            working_capacity=self.config.working_memory_capacity,
            short_term_capacity=self.config.short_term_capacity,
            vector_store=vector_store,
            llm_client=llm_client,
        )
        
        # Initialize retrievers
        self._init_retrievers()
        
        self._initialized = False
    
    def _init_retrievers(self):
        """Initialize retrieval components."""
        # Base retriever using memory manager
        base_retriever = self.memory_manager
        
        # Adaptive wrapper
        self.adaptive_retriever = AdaptiveRetriever(
            base_retriever=base_retriever,
            uncertainty_threshold=self.config.adaptive_threshold,
        )
        
        # Hybrid retriever (for non-adaptive mode)
        # Note: In a full implementation, we'd also have a separate
        # keyword retriever here
        self.hybrid_retriever = HybridRetriever(
            vector_retriever=base_retriever,
            weights=(self.config.vector_weight, self.config.keyword_weight),
        )
    
    async def initialize(self):
        """Initialize the RAG system."""
        if self._initialized:
            return
        
        # Start maintenance tasks
        await self.memory_manager.start_maintenance(interval_minutes=60)
        
        self._initialized = True
    
    async def add_document(
        self,
        content: str,
        source: str = "document",
        metadata: Optional[Dict] = None,
    ) -> MemoryEntry:
        """
        Add a document to the knowledge base.
        
        The document flows through the memory hierarchy:
        Working → Short-term → Long-term
        """
        return await self.memory_manager.add(
            content=content,
            source=source,
            session_id=self.session_id,
            metadata=metadata or {},
        )
    
    async def add_documents(
        self,
        documents: List[str],
        source: str = "document",
    ) -> List[MemoryEntry]:
        """Add multiple documents."""
        memories = []
        for doc in documents:
            memory = await self.add_document(doc, source)
            memories.append(memory)
        return memories
    
    async def query(
        self,
        query: str,
        limit: int = 10,
        strategy: Optional[RetrievalStrategy] = None,
    ) -> 'RAGQueryResult':
        """
        Query the RAG system.
        
        Args:
            query: The query string
            limit: Maximum number of results
            strategy: Override retrieval strategy
        
        Returns:
            RAGQueryResult with context and metadata
        """
        strategy = strategy or self.config.strategy
        
        # Execute retrieval based on strategy
        if strategy == RetrievalStrategy.ADAPTIVE:
            retrieval_result = await self.adaptive_retriever.retrieve(
                query=query,
                limit=limit,
            )
        elif strategy == RetrievalStrategy.HYBRID:
            memories = await self.hybrid_retriever.retrieve(query, limit)
            retrieval_result = RetrievalResult(
                memories=memories,
                strategy_used=strategy,
                query_time_ms=0.0,  # Would be measured in real implementation
                total_candidates=len(memories),
            )
        else:
            # Simple retrieval from memory manager
            retrieval_result = await self.memory_manager.retrieve(
                query=query,
                limit=limit,
                strategy=strategy,
            )
        
        # Build context string
        context = await self._build_context(retrieval_result.memories)
        
        return RAGQueryResult(
            query=query,
            context=context,
            memories=retrieval_result.memories,
            retrieval_result=retrieval_result,
            strategy_used=strategy,
        )
    
    async def _build_context(self, memories: List[MemoryEntry]) -> str:
        """Build formatted context from memories."""
        if not memories:
            return ""
        
        parts = []
        current_length = 0
        max_length = self.config.max_context_tokens * 4  # Rough char estimate
        
        for memory in memories:
            # Format based on layer
            if memory.layer.value == "working":
                prefix = "[Current Context]"
            elif memory.layer.value == "short_term":
                prefix = "[Recent History]"
            else:
                prefix = "[Background Knowledge]"
            
            content = f"{prefix}\n{memory.content}\n\n"
            
            if current_length + len(content) > max_length:
                break
            
            parts.append(content)
            current_length += len(content)
        
        return "".join(parts)
    
    async def get_recent_context(self) -> str:
        """Get recent conversation context."""
        return await self.memory_manager.get_recent_context()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics."""
        stats = {
            "config": {
                "strategy": self.config.strategy.value,
                "adaptive_threshold": self.config.adaptive_threshold,
            },
            "memory": self.memory_manager.get_stats(),
            "retrieval": self.adaptive_retriever.get_stats(),
        }
        return stats
    
    async def close(self):
        """Clean up resources."""
        await self.memory_manager.stop_maintenance()


@dataclass
class RAGQueryResult:
    """Result from a RAG query."""
    
    query: str
    context: str
    memories: List[MemoryEntry]
    retrieval_result: RetrievalResult
    strategy_used: RetrievalStrategy
    
    # Optional generation result
    generated_text: Optional[str] = None
    
    def to_prompt(self, system_prompt: Optional[str] = None) -> str:
        """Convert to full prompt for LLM."""
        parts = []
        
        if system_prompt:
            parts.append(f"System: {system_prompt}")
        
        if self.context:
            parts.append(f"Context:\n{self.context}")
        
        parts.append(f"User: {self.query}")
        parts.append("Assistant:")
        
        return "\n\n".join(parts)
    
    def get_sources(self) -> List[Dict[str, Any]]:
        """Get source information for citations."""
        return [
            {
                "id": m.id,
                "source": m.source,
                "layer": m.layer.value,
                "importance": m.importance_score,
            }
            for m in self.memories
        ]


# Legacy adapter for backward compatibility
class RAGPipelineAdapter:
    """
    Adapter to make AdvancedRAG compatible with old RAGPipeline interface.
    
    Allows gradual migration without breaking existing code.
    """
    
    def __init__(self, session_id: str, **kwargs):
        self._advanced_rag = AdvancedRAG(session_id=session_id, **kwargs)
    
    async def initialize(self):
        await self._advanced_rag.initialize()
    
    async def ingest_document(self, content: str, **kwargs):
        """Old interface: ingest_document"""
        return await self._advanced_rag.add_document(content, **kwargs)
    
    async def query_with_context(self, query: str, top_k: int = 5, **kwargs):
        """Old interface: query_with_context"""
        result = await self._advanced_rag.query(query, limit=top_k)
        return {
            "context": result.context,
            "results": [
                {
                    "text": m.content,
                    "source": m.source,
                    "score": m.importance_score,
                }
                for m in result.memories
            ],
            "sources": result.get_sources(),
        }
    
    async def close(self):
        await self._advanced_rag.close()


__all__ = [
    'AdvancedRAG',
    'RAGConfig',
    'RAGQueryResult',
    'RAGPipelineAdapter',
]
