"""
Base classes for hierarchical memory layers.

Implements MELODI-style memory hierarchy:
- Working Memory: High-fidelity, limited capacity
- Short-term Memory: Compressed recent context
- Long-term Memory: Summarized, vector-indexed
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Protocol

from memnexus.memory.core.types import MemoryEntry, MemoryLayer, RetrievalResult


class Compressor(Protocol):
    """Protocol for memory compression strategies."""

    async def compress(self, memories: list[MemoryEntry]) -> MemoryEntry:
        """Compress multiple memories into one."""
        ...

    async def should_compress(self, memory: MemoryEntry) -> bool:
        """Determine if a memory should be compressed."""
        ...


class LLMCompressor:
    """
    LLM-based memory compression.

    Uses LLM to generate summaries of memory batches.
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.compression_threshold = 1000  # characters

    async def compress(self, memories: list[MemoryEntry]) -> MemoryEntry:
        """
        Generate a compressed summary of memories.
        """
        if not memories:
            raise ValueError("Cannot compress empty memories")

        # Combine content
        combined = "\n\n".join([f"[{m.source}]: {m.content}" for m in memories])

        if self.llm_client:
            # Use LLM for intelligent summarization
            prompt = f"""Summarize the following conversation memories into a concise paragraph.
Keep key facts, decisions, and context. Be specific but brief.

Memories:
{combined}

Summary:"""

            try:
                summary = await self.llm_client.generate(prompt, max_tokens=500)
            except Exception:
                # Fallback to truncation
                summary = combined[:2000] + "..."
        else:
            # Simple truncation fallback
            summary = combined[:2000] + "..."

        # Create compressed memory
        return MemoryEntry(
            content=summary,
            memory_type=memories[0].memory_type,
            layer=MemoryLayer.SHORT_TERM,
            source="compression",
            is_compressed=True,
            original_length=len(combined),
            compression_ratio=len(summary) / len(combined) if combined else 1.0,
            metadata={
                "source_memories": [m.id for m in memories],
                "compression_method": "llm_summary" if self.llm_client else "truncation",
            },
        )

    async def should_compress(self, memory: MemoryEntry) -> bool:
        """Check if memory should be compressed."""
        return len(memory.content) > self.compression_threshold


class AbstractMemoryLayer(ABC):
    """
    Abstract base class for memory layers.

    Each layer manages memories at a specific granularity and lifecycle stage.
    """

    def __init__(
        self,
        layer_type: MemoryLayer,
        capacity: int,
        compressor: Compressor | None = None,
    ):
        self.layer_type = layer_type
        self.capacity = capacity
        self.compressor = compressor
        self._memories: list[MemoryEntry] = []
        self._lock = asyncio.Lock()

    @property
    def size(self) -> int:
        """Current number of memories."""
        return len(self._memories)

    @property
    def is_full(self) -> bool:
        """Check if layer is at capacity."""
        return len(self._memories) >= self.capacity

    @abstractmethod
    async def add(self, memory: MemoryEntry) -> MemoryEntry | None:
        """
        Add a memory to this layer.

        Returns:
            Overflow memory if capacity exceeded, None otherwise.
        """
        ...

    @abstractmethod
    async def retrieve(self, query: str, limit: int = 10, **kwargs) -> RetrievalResult:
        """Retrieve memories from this layer."""
        ...

    async def get_all(self) -> list[MemoryEntry]:
        """Get all memories in this layer."""
        async with self._lock:
            return self._memories.copy()

    async def clear(self):
        """Clear all memories."""
        async with self._lock:
            self._memories.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get layer statistics."""
        return {
            "layer": self.layer_type.value,
            "capacity": self.capacity,
            "size": self.size,
            "utilization": self.size / self.capacity if self.capacity > 0 else 0,
            "compressed_count": sum(1 for m in self._memories if m.is_compressed),
        }


class WorkingMemoryLayer(AbstractMemoryLayer):
    """
    Working memory layer - high-fidelity, immediate context.

    Similar to human working memory:
    - Limited capacity (7±2 items)
    - High fidelity
    - Recent only
    """

    def __init__(self, capacity: int = 10):
        super().__init__(layer_type=MemoryLayer.WORKING, capacity=capacity, compressor=None)
        self._access_history: dict[str, datetime] = {}

    async def add(self, memory: MemoryEntry) -> MemoryEntry | None:
        """
        Add to working memory.

        If full, evict oldest memory.
        """
        async with self._lock:
            memory.layer = MemoryLayer.WORKING

            # Evict oldest if necessary
            overflow = None
            if len(self._memories) >= self.capacity:
                overflow = self._memories.pop(0)

            self._memories.append(memory)
            self._access_history[memory.id] = datetime.now(timezone.utc)

            return overflow

    async def retrieve(self, query: str, limit: int = 10, **kwargs) -> RetrievalResult:
        """
        Retrieve from working memory.

        Simple recency-based retrieval for working memory.
        """
        async with self._lock:
            # Return most recent memories
            results = self._memories[-limit:]

            return RetrievalResult(
                memories=results,
                strategy_used=None,  # Working memory doesn't use retrieval
                query_time_ms=0.0,
                total_candidates=len(results),
            )

    async def get_recent(self, n: int = 5) -> list[MemoryEntry]:
        """Get n most recent memories."""
        async with self._lock:
            return self._memories[-n:]

    async def flush(self) -> list[MemoryEntry]:
        """Clear and return all memories for compression."""
        async with self._lock:
            batch = self._memories.copy()
            self._memories.clear()
            self._access_history.clear()
            return batch


class ShortTermMemoryLayer(AbstractMemoryLayer):
    """
    Short-term memory layer - compressed recent history.

    MELODI-style compression:
    - Aggregates working memory overflows
    - Maintains narrative coherence
    - Medium retention
    """

    def __init__(
        self,
        capacity: int = 50,
        compressor: Compressor | None = None,
        compression_batch_size: int = 5,
    ):
        super().__init__(
            layer_type=MemoryLayer.SHORT_TERM,
            capacity=capacity,
            compressor=compressor or LLMCompressor(),
        )
        self.compression_batch_size = compression_batch_size
        self._compression_queue: list[MemoryEntry] = []

    async def add(self, memory: MemoryEntry) -> MemoryEntry | None:
        """
        Add to short-term memory.

        Compresses batched memories when queue fills.
        """
        async with self._lock:
            memory.layer = MemoryLayer.SHORT_TERM

            # Add to compression queue
            self._compression_queue.append(memory)

            # Compress if batch is full
            if len(self._compression_queue) >= self.compression_batch_size:
                await self._compress_batch()

            # Check capacity
            overflow = None
            if len(self._memories) >= self.capacity:
                # Remove oldest
                overflow = self._memories.pop(0)

            return overflow

    async def _compress_batch(self):
        """Compress queued memories."""
        if not self._compression_queue:
            return

        batch = self._compression_queue.copy()
        self._compression_queue.clear()

        if self.compressor:
            compressed = await self.compressor.compress(batch)
            self._memories.append(compressed)
        else:
            # No compression, just add
            self._memories.extend(batch)

    async def retrieve(self, query: str, limit: int = 10, **kwargs) -> RetrievalResult:
        """
        Retrieve from short-term memory.

        Returns compressed summaries that match query keywords.
        """
        async with self._lock:
            # Simple keyword matching (can be enhanced with embeddings)
            query_words = set(query.lower().split())

            scored = []
            for memory in self._memories:
                memory_words = set(memory.content.lower().split())
                overlap = len(query_words & memory_words)
                scored.append((memory, overlap))

            # Sort by relevance
            scored.sort(key=lambda x: x[1], reverse=True)
            results = [m for m, _ in scored[:limit]]

            return RetrievalResult(
                memories=results,
                strategy_used=None,
                query_time_ms=0.0,
                total_candidates=len(results),
            )

    async def flush_oldest(self, ratio: float = 0.3) -> list[MemoryEntry]:
        """
        Flush oldest memories to long-term storage.

        Args:
            ratio: Fraction of memories to flush (0.0 - 1.0)
        """
        async with self._lock:
            n = int(len(self._memories) * ratio)
            oldest = self._memories[:n]
            self._memories = self._memories[n:]
            return oldest

    async def finalize(self):
        """Compress any remaining queued memories."""
        async with self._lock:
            if self._compression_queue:
                await self._compress_batch()


__all__ = [
    "AbstractMemoryLayer",
    "WorkingMemoryLayer",
    "ShortTermMemoryLayer",
    "Compressor",
    "LLMCompressor",
]
