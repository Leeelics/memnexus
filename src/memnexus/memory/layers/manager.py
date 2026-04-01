"""
Hierarchical Memory Manager.

Coordinates between working, short-term, and long-term memory layers.
Implements MELODI-style compression flow and intelligent memory lifecycle.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any

from memnexus.memory.core.types import MemoryEntry, MemoryLayer, RetrievalResult, RetrievalStrategy
from memnexus.memory.layers.base import (
    AbstractMemoryLayer,
    LLMCompressor,
    ShortTermMemoryLayer,
    WorkingMemoryLayer,
)


class LongTermMemoryLayer(AbstractMemoryLayer):
    """
    Long-term memory layer - persistent, vector-indexed storage.

    Features:
    - Vector similarity search
    - Importance-based retention
    - Automatic consolidation
    """

    def __init__(
        self,
        vector_store=None,
        importance_threshold: float = 0.3,
        consolidation_interval: int = 100,  # Memories before consolidation
    ):
        super().__init__(
            layer_type=MemoryLayer.LONG_TERM,
            capacity=float("inf"),  # No fixed capacity
            compressor=None,
        )
        self.vector_store = vector_store
        self.importance_threshold = importance_threshold
        self.consolidation_interval = consolidation_interval
        self._consolidation_counter = 0

    async def add(self, memory: MemoryEntry) -> None:
        """Add to long-term memory."""
        memory.layer = MemoryLayer.LONG_TERM

        # Filter by importance
        if memory.effective_importance < self.importance_threshold:
            return  # Skip low-importance memories

        async with self._lock:
            self._memories.append(memory)
            self._consolidation_counter += 1

            # Add to vector store if available
            if self.vector_store:
                await self.vector_store.add(memory)

            # Trigger consolidation periodically
            if self._consolidation_counter >= self.consolidation_interval:
                asyncio.create_task(self._consolidate())
                self._consolidation_counter = 0

    async def retrieve(self, query: str, limit: int = 10, **kwargs) -> RetrievalResult:
        """
        Retrieve from long-term memory using vector search.
        """
        start_time = asyncio.get_event_loop().time()

        if self.vector_store:
            # Use vector store for semantic search
            results = await self.vector_store.search(query, limit)
        else:
            # Fallback to simple keyword search
            results = await self._keyword_search(query, limit)

        query_time = (asyncio.get_event_loop().time() - start_time) * 1000

        return RetrievalResult(
            memories=results,
            strategy_used=RetrievalStrategy.SIMPLE,
            query_time_ms=query_time,
            total_candidates=len(results),
        )

    async def _keyword_search(self, query: str, limit: int) -> list[MemoryEntry]:
        """Fallback keyword search."""
        query_words = set(query.lower().split())

        scored = []
        for memory in self._memories:
            memory_words = set(memory.content.lower().split())
            overlap = len(query_words & memory_words)
            if overlap > 0:
                scored.append((memory, overlap))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [m for m, _ in scored[:limit]]

    async def _consolidate(self):
        """
        Memory consolidation - merge similar memories.

        Inspired by human sleep memory consolidation.
        """
        async with self._lock:
            if len(self._memories) < 10:
                return

            # Group by time windows
            windows = self._group_by_time(self._memories, hours=24)

            new_memories = []
            for window_memories in windows:
                if len(window_memories) > 3:
                    # Merge similar memories
                    merged = await self._merge_memories(window_memories)
                    new_memories.append(merged)
                else:
                    new_memories.extend(window_memories)

            self._memories = new_memories

    def _group_by_time(
        self, memories: list[MemoryEntry], hours: int = 24
    ) -> list[list[MemoryEntry]]:
        """Group memories by time windows."""
        if not memories:
            return []

        sorted_memories = sorted(memories, key=lambda m: m.created_at)
        windows = []
        current_window = [sorted_memories[0]]
        window_start = sorted_memories[0].created_at

        for memory in sorted_memories[1:]:
            if (memory.created_at - window_start) <= timedelta(hours=hours):
                current_window.append(memory)
            else:
                windows.append(current_window)
                current_window = [memory]
                window_start = memory.created_at

        if current_window:
            windows.append(current_window)

        return windows

    async def _merge_memories(self, memories: list[MemoryEntry]) -> MemoryEntry:
        """Merge multiple memories into one summary."""
        # Simple merging - take the most important and concatenate
        most_important = max(memories, key=lambda m: m.importance_score)

        combined_content = "\n".join(
            [
                f"- {m.content[:200]}"
                for m in memories[:5]  # Limit to avoid too long content
            ]
        )

        return MemoryEntry(
            content=f"Consolidated memory ({len(memories)} items):\n{combined_content}",
            memory_type=most_important.memory_type,
            layer=MemoryLayer.LONG_TERM,
            source="consolidation",
            importance_score=max(m.importance_score for m in memories),
            metadata={
                "merged_count": len(memories),
                "original_ids": [m.id for m in memories],
            },
        )

    async def cleanup(self, max_age_days: int = 30):
        """Remove old, low-importance memories."""
        async with self._lock:
            cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)

            self._memories = [
                m for m in self._memories if m.created_at > cutoff or m.importance_score > 0.7
            ]


class HierarchicalMemoryManager:
    """
    Manages the complete memory hierarchy.

    Coordinates data flow:
    Working Memory → (overflow) → Short-term Memory → (flush) → Long-term Memory

    Based on MELODI's "sandwich" architecture with three layers.
    """

    def __init__(
        self,
        working_capacity: int = 10,
        short_term_capacity: int = 50,
        vector_store=None,
        llm_client=None,
    ):
        self.working = WorkingMemoryLayer(capacity=working_capacity)
        self.short_term = ShortTermMemoryLayer(
            capacity=short_term_capacity, compressor=LLMCompressor(llm_client)
        )
        self.long_term = LongTermMemoryLayer(vector_store=vector_store)

        # Configuration
        self.auto_flush_ratio = 0.3  # Flush 30% of short-term when full
        self._maintenance_task = None

    async def add(self, content: str, **metadata) -> MemoryEntry:
        """
        Add content to memory hierarchy.

        Automatically manages overflow between layers.
        """
        memory = MemoryEntry(content=content, layer=MemoryLayer.WORKING, **metadata)

        # Add to working memory
        overflow = await self.working.add(memory)

        # Handle overflow to short-term
        if overflow:
            st_overflow = await self.short_term.add(overflow)

            # Handle short-term overflow to long-term
            if st_overflow:
                await self._flush_to_long_term()

        return memory

    async def add_batch(self, contents: list[str], **metadata) -> list[MemoryEntry]:
        """Add multiple items efficiently."""
        memories = []
        for content in contents:
            memory = await self.add(content, **metadata)
            memories.append(memory)
        return memories

    async def _flush_to_long_term(self):
        """Flush oldest short-term memories to long-term."""
        oldest = await self.short_term.flush_oldest(ratio=self.auto_flush_ratio)

        for memory in oldest:
            await self.long_term.add(memory)

    async def retrieve(
        self,
        query: str,
        limit: int = 10,
        strategy: RetrievalStrategy = RetrievalStrategy.HYBRID,
    ) -> RetrievalResult:
        """
        Retrieve from appropriate memory layers.

        Strategy:
        - Always check working memory (fast)
        - Check short-term for recent context
        - Search long-term for deep knowledge
        """
        all_results = []
        total_time = 0.0

        # 1. Working memory (always, immediate)
        working_results = await self.working.retrieve(query, limit=min(limit, 5))
        all_results.extend(working_results.memories)
        total_time += working_results.query_time_ms

        # 2. Short-term memory
        if strategy in (RetrievalStrategy.HYBRID, RetrievalStrategy.SIMPLE):
            st_results = await self.short_term.retrieve(
                query, limit=min(limit - len(all_results), 5)
            )
            all_results.extend(st_results.memories)
            total_time += st_results.query_time_ms

        # 3. Long-term memory
        if strategy in (RetrievalStrategy.HYBRID, RetrievalStrategy.SIMPLE):
            remaining = limit - len(all_results)
            if remaining > 0:
                lt_results = await self.long_term.retrieve(query, limit=remaining)
                all_results.extend(lt_results.memories)
                total_time += lt_results.query_time_ms

        # Deduplicate
        seen = set()
        unique = []
        for m in all_results:
            if m.id not in seen:
                seen.add(m.id)
                unique.append(m)

        return RetrievalResult(
            memories=unique[:limit],
            strategy_used=strategy,
            query_time_ms=total_time,
            total_candidates=len(unique),
        )

    async def get_context(
        self,
        query: str,
        max_tokens: int = 4000,
    ) -> str:
        """
        Get formatted context string for LLM.

        Builds context from all layers, respecting token limit.
        """
        # Retrieve from all layers
        results = await self.retrieve(query, limit=20, strategy=RetrievalStrategy.HYBRID)

        # Build context string
        context_parts = []
        current_tokens = 0

        # Prioritize by layer
        layer_order = [MemoryLayer.WORKING, MemoryLayer.SHORT_TERM, MemoryLayer.LONG_TERM]

        for layer in layer_order:
            layer_memories = [m for m in results.memories if m.layer == layer]

            for memory in layer_memories:
                # Rough token estimation
                content = f"[{layer.value}] {memory.content}\n\n"
                estimated_tokens = len(content) // 4

                if current_tokens + estimated_tokens > max_tokens:
                    break

                context_parts.append(content)
                current_tokens += estimated_tokens

            if current_tokens >= max_tokens:
                break

        return "".join(context_parts)

    async def get_recent_context(self, n_working: int = 5, n_short: int = 3) -> str:
        """Get recent context without querying."""
        parts = []

        # Working memory
        working_recent = await self.working.get_recent(n_working)
        for m in reversed(working_recent):  # Chronological order
            parts.append(f"[Current] {m.content}")

        # Short-term memory
        if parts:
            parts.append("\n--- Recent History ---\n")

        st_results = await self.short_term.retrieve("recent", limit=n_short)
        for m in st_results.memories:
            parts.append(f"[Previous] {m.content[:300]}...")

        return "\n\n".join(parts)

    async def start_maintenance(self, interval_minutes: int = 60):
        """Start periodic maintenance tasks."""

        async def maintenance_loop():
            while True:
                await asyncio.sleep(interval_minutes * 60)
                await self._maintenance()

        self._maintenance_task = asyncio.create_task(maintenance_loop())

    async def _maintenance(self):
        """Perform maintenance tasks."""
        # Finalize any pending compression
        await self.short_term.finalize()

        # Cleanup old memories
        await self.long_term.cleanup()

    async def stop_maintenance(self):
        """Stop maintenance tasks."""
        if self._maintenance_task:
            self._maintenance_task.cancel()
            try:
                await self._maintenance_task
            except asyncio.CancelledError:
                pass

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive memory statistics."""
        return {
            "working": self.working.get_stats(),
            "short_term": self.short_term.get_stats(),
            "long_term": self.long_term.get_stats(),
            "total_memories": (self.working.size + self.short_term.size + self.long_term.size),
        }

    async def clear_all(self):
        """Clear all memory layers."""
        await self.working.clear()
        await self.short_term.clear()
        await self.long_term.clear()


__all__ = [
    "LongTermMemoryLayer",
    "HierarchicalMemoryManager",
]
