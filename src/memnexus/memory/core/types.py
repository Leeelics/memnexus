"""Core types and enums for memory system."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import numpy as np


class MemoryLayer(Enum):
    """Memory hierarchy layers."""

    WORKING = "working"  # 当前上下文
    SHORT_TERM = "short_term"  # 近期历史
    LONG_TERM = "long_term"  # 长期存储


class MemoryType(Enum):
    """Types of memory content."""

    CONVERSATION = "conversation"
    CODE = "code"
    DOCUMENT = "document"
    DECISION = "decision"
    TASK = "task"
    GENERIC = "generic"


class RetrievalStrategy(Enum):
    """Available retrieval strategies."""

    SIMPLE = "simple"  # 纯向量检索
    ADAPTIVE = "adaptive"  # 自适应检索 (SEAKR)
    HYBRID = "hybrid"  # 混合检索 (向量+关键词)
    GRAPH = "graph"  # 知识图谱检索
    HYBRID_GRAPH = "hybrid_graph"  # 向量+图谱混合


@dataclass
class MemoryEntry:
    """
    A single memory entry with enhanced metadata.

    Supports hierarchical memory architecture with importance scoring
    and lifecycle management.
    """

    content: str
    memory_type: MemoryType = MemoryType.GENERIC
    layer: MemoryLayer = MemoryLayer.WORKING

    # Identifiers
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    session_id: str | None = None
    parent_id: str | None = None  # For hierarchical relationships

    # Content metadata
    source: str = "system"
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    # Vector representation
    embedding: np.ndarray | None = None

    # Importance and lifecycle (for intelligent forgetting)
    importance_score: float = 1.0  # 0.0 - 1.0
    access_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)

    # Compression info
    is_compressed: bool = False
    original_length: int | None = None
    compression_ratio: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "layer": self.layer.value,
            "session_id": self.session_id,
            "source": self.source,
            "metadata": self.metadata,
            "tags": self.tags,
            "importance_score": self.importance_score,
            "access_count": self.access_count,
            "created_at": self.created_at.isoformat(),
            "is_compressed": self.is_compressed,
        }

    def access(self):
        """Record an access to this memory."""
        self.access_count += 1
        self.last_accessed = datetime.now(timezone.utc)

    @property
    def age_hours(self) -> float:
        """Get age in hours."""
        return (datetime.now(timezone.utc) - self.created_at).total_seconds() / 3600

    @property
    def effective_importance(self) -> float:
        """
        Calculate effective importance with time decay.

        Based on SynapticRAG's temporal decay mechanism.
        """
        time_decay = np.exp(-self.age_hours / 168)  # 1 week half-life
        access_boost = min(self.access_count * 0.1, 0.5)
        return self.importance_score * time_decay + access_boost


@dataclass
class RetrievalResult:
    """Result from a retrieval operation."""

    memories: list[MemoryEntry]
    strategy_used: RetrievalStrategy
    query_time_ms: float
    total_candidates: int

    # Source breakdown for hybrid retrieval
    source_breakdown: dict[str, int] | None = None

    # Confidence score
    confidence: float = 1.0

    def merge(self, other: "RetrievalResult") -> "RetrievalResult":
        """Merge two retrieval results."""
        all_memories = self.memories + other.memories
        # Deduplicate by ID
        seen = set()
        unique = []
        for m in all_memories:
            if m.id not in seen:
                seen.add(m.id)
                unique.append(m)

        return RetrievalResult(
            memories=unique,
            strategy_used=self.strategy_used,
            query_time_ms=self.query_time_ms + other.query_time_ms,
            total_candidates=self.total_candidates + other.total_candidates,
            confidence=(self.confidence + other.confidence) / 2,
        )


@dataclass
class UncertaintyEstimate:
    """
    Uncertainty estimate for adaptive retrieval (SEAKR).

    Used to decide whether external knowledge retrieval is needed.
    """

    query: str
    entropy: float  # Shannon entropy of model's prediction
    confidence: float  # Model's confidence score
    historical_accuracy: float | None = None  # Accuracy on similar queries

    @property
    def needs_retrieval(self, threshold: float = 0.7) -> bool:
        """
        Determine if retrieval is needed based on uncertainty.

        High entropy + low confidence → needs retrieval
        """
        if self.historical_accuracy is not None:
            return self.historical_accuracy < threshold
        return self.confidence < (1 - threshold) or self.entropy > 1.5


@dataclass
class Triple:
    """
    A knowledge graph triple (subject, relation, object).

    Represents a single fact extracted from text using open information extraction.
    Used by HippoRAG for knowledge graph construction and retrieval.

    Attributes:
        subject: The entity or concept (e.g., "Python", "User")
        relation: The relationship (e.g., "is a", "created", "requires")
        object: The target entity or value (e.g., "programming language", "API")
        confidence: Confidence score from 0.0 to 1.0 (default: 1.0)
        source_text: Original text from which this triple was extracted
        metadata: Additional metadata (e.g., extraction method, timestamp)
    """

    subject: str
    relation: str
    obj: str  # 'object' is a reserved keyword in Python
    confidence: float = 1.0
    source_text: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate confidence score."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

    def to_dict(self) -> dict[str, Any]:
        """Convert triple to dictionary for serialization."""
        return {
            "subject": self.subject,
            "relation": self.relation,
            "object": self.obj,
            "confidence": self.confidence,
            "source_text": self.source_text,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Triple":
        """Create triple from dictionary."""
        return cls(
            subject=data["subject"],
            relation=data["relation"],
            obj=data["object"],
            confidence=data.get("confidence", 1.0),
            source_text=data.get("source_text"),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        """String representation of the triple."""
        return (
            f"Triple({self.subject} --[{self.relation}]--> {self.obj}, conf={self.confidence:.2f})"
        )

    def __hash__(self) -> int:
        """Hash based on subject, relation, and object."""
        return hash((self.subject.lower(), self.relation.lower(), self.obj.lower()))

    def __eq__(self, other: object) -> bool:
        """Equality check ignoring confidence and metadata."""
        if not isinstance(other, Triple):
            return False
        return (
            self.subject.lower() == other.subject.lower()
            and self.relation.lower() == other.relation.lower()
            and self.obj.lower() == other.obj.lower()
        )


# Import here to avoid circular import
import uuid
