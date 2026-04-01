"""Session Explorer for cross-session context discovery.

This module enables proactive exploration of historical sessions
to discover relevant context across conversation boundaries.

Example:
    >>> from memnexus.session import SessionExplorer
    >>> explorer = SessionExplorer()
    >>> result = await explorer.explore_related(
    ...     current_session_id="current_123",
    ...     query="database choice"
    ... )
    >>> for decision in result.decisions:
    ...     print(f"Found: {decision.content}")
"""

from memnexus.session.deduplicator import DecisionDeduplicator
from memnexus.session.explorer import (
    ExploreOptions,
    SessionExplorer,
)
from memnexus.session.models import (
    Decision,
    DuplicateCheckResult,
    ExplorationRecord,
    ExplorationResult,
    ExplorationStats,
    ExplorerConfig,
    ScorerConfig,
    SessionExplorerError,
)
from memnexus.session.scorer import RelevanceScorer

__all__ = [
    # Main classes
    "SessionExplorer",
    "DecisionDeduplicator",
    "RelevanceScorer",
    # Options and config
    "ExploreOptions",
    "ExplorerConfig",
    "ScorerConfig",
    # Data models
    "Decision",
    "DuplicateCheckResult",
    "ExplorationRecord",
    "ExplorationResult",
    "ExplorationStats",
    # Exceptions
    "SessionExplorerError",
]
