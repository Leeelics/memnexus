"""
Adaptive Retrieval - SEAKR-inspired implementation.

Intelligently decides whether to retrieve external knowledge based on
model uncertainty estimation.
"""

import asyncio
import hashlib
import re
import time
from dataclasses import dataclass, field

from memnexus.memory.core.types import (
    MemoryEntry,
    RetrievalResult,
    RetrievalStrategy,
    UncertaintyEstimate,
)


@dataclass
class QueryHistory:
    """Track query performance for adaptive decisions."""

    query_hash: str
    count: int = 0
    success_count: int = 0
    last_used: float = field(default_factory=time.time)
    avg_latency: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.count == 0:
            return 0.5  # Unknown
        return self.success_count / self.count

    def record_result(self, success: bool, latency: float):
        self.count += 1
        if success:
            self.success_count += 1
        # Exponential moving average for latency
        self.avg_latency = 0.7 * self.avg_latency + 0.3 * latency
        self.last_used = time.time()


class AdaptiveRetriever:
    """
    SEAKR-inspired adaptive retriever.

    Decides whether to retrieve based on:
    1. Query complexity analysis
    2. Historical performance on similar queries
    3. Semantic uncertainty estimation

    Reference: "SEAKR: Self-aware Knowledge Retrieval for Adaptive
    Retrieval Augmented Generation" (2024)
    """

    def __init__(
        self,
        base_retriever,
        uncertainty_threshold: float = 0.6,
        complexity_threshold: float = 0.5,
        history_window: int = 1000,
    ):
        self.base_retriever = base_retriever
        self.uncertainty_threshold = uncertainty_threshold
        self.complexity_threshold = complexity_threshold
        self.history_window = history_window

        # Query performance history
        self._history: dict[str, QueryHistory] = {}

        # Complexity indicators
        self._complexity_patterns = {
            "factual_question": r"^(what|who|when|where|why|how)\s+(is|are|was|were|did|do|does)",
            "comparison": r"\b(compare|versus|vs|difference|similarities?|better|worse)\b",
            "multi_hop": r"\b(and|also|as well as|in addition to)\b.*\?",
            "specific_entity": r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b",  # Named entities
            "temporal": r"\b(20\d\d|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b",
            "technical": r"\b(api|database|algorithm|framework|architecture|implementation)\b",
        }

    def _hash_query(self, query: str) -> str:
        """Create a normalized hash for query tracking."""
        # Normalize: lowercase, remove extra spaces
        normalized = " ".join(query.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()[:16]

    def _estimate_complexity(self, query: str) -> tuple[float, dict[str, float]]:
        """
        Estimate query complexity.

        Returns:
            Overall complexity score (0-1) and breakdown by factor.
        """
        scores = {}

        # Length factor (longer queries tend to be more complex)
        word_count = len(query.split())
        scores["length"] = min(word_count / 20, 1.0)

        # Pattern matching
        for name, pattern in self._complexity_patterns.items():
            matches = len(re.findall(pattern, query, re.IGNORECASE))
            scores[name] = min(matches * 0.3, 1.0)

        # Question type
        if query.strip().endswith("?"):
            scores["question"] = 0.7
        else:
            scores["question"] = 0.3

        # Overall complexity (weighted sum)
        weights = {
            "length": 0.15,
            "factual_question": 0.2,
            "comparison": 0.25,
            "multi_hop": 0.2,
            "specific_entity": 0.1,
            "temporal": 0.05,
            "technical": 0.15,
            "question": 0.1,
        }

        overall = sum(scores.get(k, 0) * weights.get(k, 0) for k in set(scores) | set(weights))
        return min(overall, 1.0), scores

    def _estimate_uncertainty(
        self, query: str, context: list[MemoryEntry] | None = None
    ) -> UncertaintyEstimate:
        """
        Estimate semantic uncertainty for the query.

        In a full implementation, this would use the LLM's internal
        confidence scores. Here we use heuristics.
        """
        complexity, _ = self._estimate_complexity(query)

        # Historical accuracy
        query_hash = self._hash_query(query)
        history = self._history.get(query_hash)
        historical_acc = history.success_rate if history else None

        # Vague queries have higher uncertainty
        vague_terms = ["something", "someone", "somewhere", "somehow", "maybe", "perhaps"]
        vagueness = sum(1 for term in vague_terms if term in query.lower()) / len(vague_terms)

        # Calculate entropy (simplified)
        entropy = complexity * 2.0 + vagueness * 1.5

        # Confidence is inverse of uncertainty
        confidence = 1.0 - min(entropy / 3.0, 1.0)

        return UncertaintyEstimate(
            query=query, entropy=entropy, confidence=confidence, historical_accuracy=historical_acc
        )

    def should_retrieve(
        self, query: str, context: list[MemoryEntry] | None = None
    ) -> tuple[bool, UncertaintyEstimate]:
        """
        Decide whether retrieval is needed.

        Returns:
            (should_retrieve, uncertainty_estimate)
        """
        uncertainty = self._estimate_uncertainty(query, context)

        # Decision based on multiple factors
        reasons_to_retrieve = []

        # 1. High uncertainty
        if uncertainty.confidence < (1 - self.uncertainty_threshold):
            reasons_to_retrieve.append("low_confidence")

        # 2. High complexity
        complexity, _ = self._estimate_complexity(query)
        if complexity > self.complexity_threshold:
            reasons_to_retrieve.append("high_complexity")

        # 3. Poor historical performance
        if uncertainty.historical_accuracy is not None:
            if uncertainty.historical_accuracy < self.uncertainty_threshold:
                reasons_to_retrieve.append("poor_history")

        # 4. No relevant context
        if context:
            recent_context = [m for m in context if m.age_hours < 1]
            if len(recent_context) < 3:
                reasons_to_retrieve.append("insufficient_context")
        else:
            reasons_to_retrieve.append("no_context")

        should_retrieve = len(reasons_to_retrieve) > 0

        # Store decision metadata
        uncertainty.metadata = {
            "reasons": reasons_to_retrieve,
            "complexity": complexity,
        }

        return should_retrieve, uncertainty

    async def retrieve(
        self,
        query: str,
        limit: int = 10,
        context: list[MemoryEntry] | None = None,
    ) -> RetrievalResult:
        """
        Adaptive retrieval with intelligent decision-making.
        """
        start_time = time.time()

        # Decision phase
        should_retrieve, uncertainty = self.should_retrieve(query, context)

        if not should_retrieve:
            # Low uncertainty - skip retrieval
            return RetrievalResult(
                memories=[],
                strategy_used=RetrievalStrategy.ADAPTIVE,
                query_time_ms=(time.time() - start_time) * 1000,
                total_candidates=0,
                confidence=uncertainty.confidence,
            )

        # Retrieval phase
        try:
            results = await self.base_retriever.retrieve(query, limit)
            query_time = (time.time() - start_time) * 1000

            # Update history (async fire-and-forget)
            asyncio.create_task(self._update_history(query, len(results) > 0, query_time))

            return RetrievalResult(
                memories=results,
                strategy_used=RetrievalStrategy.ADAPTIVE,
                query_time_ms=query_time,
                total_candidates=len(results),
                confidence=uncertainty.confidence,
            )

        except Exception:
            # Fallback to empty on error
            return RetrievalResult(
                memories=[],
                strategy_used=RetrievalStrategy.ADAPTIVE,
                query_time_ms=(time.time() - start_time) * 1000,
                total_candidates=0,
                confidence=0.0,
            )

    async def _update_history(self, query: str, success: bool, latency: float):
        """Update query history asynchronously."""
        query_hash = self._hash_query(query)

        if query_hash not in self._history:
            self._history[query_hash] = QueryHistory(query_hash=query_hash)

        self._history[query_hash].record_result(success, latency)

        # Cleanup old history
        if len(self._history) > self.history_window:
            # Remove oldest entries
            sorted_items = sorted(self._history.items(), key=lambda x: x[1].last_used)
            for key, _ in sorted_items[: len(sorted_items) // 4]:
                del self._history[key]

    def get_stats(self) -> dict:
        """Get retrieval statistics."""
        if not self._history:
            return {"total_queries": 0}

        total = sum(h.count for h in self._history.values())
        successes = sum(h.success_count for h in self._history.values())

        return {
            "total_queries": total,
            "successful_retrievals": successes,
            "success_rate": successes / total if total > 0 else 0,
            "unique_queries": len(self._history),
            "avg_latency_ms": sum(h.avg_latency for h in self._history.values())
            / len(self._history),
        }


class HybridRetriever:
    """
    Hybrid retriever combining multiple retrieval strategies.

    - Dense retrieval (vector similarity)
    - Sparse retrieval (BM25/keyword)
    - Fusion of results
    """

    def __init__(
        self,
        vector_retriever,
        keyword_retriever=None,
        weights: tuple[float, float] = (0.7, 0.3),
        reranker=None,
    ):
        self.vector_retriever = vector_retriever
        self.keyword_retriever = keyword_retriever
        self.weights = weights
        self.reranker = reranker

    async def retrieve(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """
        Retrieve using hybrid approach.
        """
        results = []

        # Dense retrieval
        if self.vector_retriever:
            vector_results = await self.vector_retriever.retrieve(query, limit * 2)
            for r in vector_results:
                r.metadata["retrieval_score"] = r.metadata.get("score", 0.5) * self.weights[0]
                r.metadata["source"] = "vector"
            results.extend(vector_results)

        # Sparse retrieval
        if self.keyword_retriever:
            keyword_results = await self.keyword_retriever.retrieve(query, limit * 2)
            for r in keyword_results:
                r.metadata["retrieval_score"] = r.metadata.get("score", 0.5) * self.weights[1]
                r.metadata["source"] = "keyword"
            results.extend(keyword_results)

        # Merge and deduplicate
        seen = set()
        unique = []
        for r in sorted(results, key=lambda x: x.metadata.get("retrieval_score", 0), reverse=True):
            if r.id not in seen:
                seen.add(r.id)
                unique.append(r)

        # Rerank if available
        if self.reranker and len(unique) > limit:
            unique = await self.reranker.rerank(query, unique, limit)

        return unique[:limit]


# Convenience exports
__all__ = [
    "AdaptiveRetriever",
    "HybridRetriever",
    "QueryHistory",
    "UncertaintyEstimate",
]
