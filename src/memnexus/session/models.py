"""Data models for Session Explorer."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class Decision:
    """A recorded decision from a session."""

    content: str
    timestamp: str
    source_session: str
    fingerprint: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ExplorationResult:
    """Result of a session exploration."""

    decisions: list[Decision]
    explored_sessions: list[str]
    total_relevance: float
    query: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class DuplicateCheckResult:
    """Result of a duplicate check."""

    is_duplicate: bool
    confidence: float
    similar_decisions: list[Decision]
    fingerprint: Optional[str] = None


@dataclass
class ExplorationStats:
    """Statistics about explorations."""

    total_explored_sessions: int
    total_unique_decisions: int
    known_keywords_count: int
    available_session_files: int


@dataclass
class ExplorerConfig:
    """Configuration for SessionExplorer."""

    # Scoring weights
    keyword_match_weight: float = 0.3
    same_project_weight: float = 1.0
    related_path_weight: float = 0.5

    # Time decay
    time_decay_half_life_days: int = 7

    # Limits
    max_decisions_per_session: int = 20
    max_total_decisions: int = 100

    # Storage
    storage_backend: str = "auto"  # "sqlite", "json", "auto"


@dataclass
class ScorerConfig:
    """Configuration for RelevanceScorer."""

    keyword_weight: float = 0.3
    project_weight: float = 1.0
    path_weight: float = 0.5
    time_decay: float = 7.0  # half-life in days


@dataclass
class DecisionFingerprint:
    """Fingerprint for a decision."""

    hash: str
    keywords: list[str]
    timestamp: str
    source_session: str
    content_preview: str


@dataclass
class ExplorationRecord:
    """Record of a session exploration."""

    session_id: str
    explored_by: str
    explored_at: str
    relevance_score: float
    decisions_extracted: int


# Error Types
class SessionExplorerError(Exception):
    """Base exception for Session Explorer."""
    pass


class StorageError(SessionExplorerError):
    """Storage operation failed."""
    pass


class InvalidSessionError(SessionExplorerError):
    """Session data is invalid or corrupted."""
    pass


class ConfigurationError(SessionExplorerError):
    """Invalid configuration."""
    pass
