"""Session Explorer for cross-session context discovery."""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from memnexus.session.deduplicator import DecisionDeduplicator
from memnexus.session.models import (
    Decision,
    ExplorationRecord,
    ExplorationResult,
    ExplorationStats,
    ExplorerConfig,
    SessionExplorerError,
)
from memnexus.session.scorer import RelevanceScorer, SessionData
from memnexus.session.storage import StorageBackend, create_storage


@dataclass
class ExploreOptions:
    """Options for exploration."""

    limit: int = 5
    min_relevance: float = 0.2
    skip_explored: bool = True


class SessionExplorer:
    """Main interface for session exploration functionality.

    Example:
        >>> explorer = SessionExplorer()
        >>> result = await explorer.explore_related(
        ...     current_session_id="current_123",
        ...     query="database choice",
        ...     limit=5
        ... )
        >>> for decision in result.decisions:
        ...     print(f"Found: {decision.content}")
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        config: Optional[ExplorerConfig] = None,
    ):
        """Initialize the SessionExplorer.

        Args:
            storage_path: Path to store exploration data
            config: Configuration options
        """
        if storage_path is None:
            storage_path = Path.home() / ".memnexus" / "explorer"

        self.storage_path = Path(storage_path)
        self.config = config or ExplorerConfig()

        # Initialize storage
        self.storage: StorageBackend = create_storage(
            self.storage_path,
            self.config.storage_backend,
        )

        # Initialize components
        self.deduplicator = DecisionDeduplicator(self.storage_path)
        self.scorer = RelevanceScorer()

        # Session directory
        self.sessions_dir = Path.home() / ".memnexus" / "sessions"

    async def explore_related(
        self,
        current_session_id: str,
        query: str,
        context: Optional[dict] = None,
        options: Optional[ExploreOptions] = None,
    ) -> ExplorationResult:
        """Explore historical sessions for relevant decisions.

        Args:
            current_session_id: ID of current session (excluded from results)
            query: Search query string
            context: Additional context (cwd, project, etc.)
            options: Exploration options

        Returns:
            ExplorationResult containing decisions and metadata
        """
        if context is None:
            context = {}

        if options is None:
            options = ExploreOptions()

        # Find available sessions
        sessions = self._discover_sessions()

        # Filter out current session
        sessions = [s for s in sessions if s.session_id != current_session_id]

        # Filter out already explored sessions
        if options.skip_explored:
            sessions = [
                s for s in sessions
                if not self.is_explored(s.session_id, current_session_id)
            ]

        if not sessions:
            return ExplorationResult(
                decisions=[],
                explored_sessions=[],
                total_relevance=0.0,
                query=query,
            )

        # Score sessions
        scored_sessions = []
        for session in sessions:
            score = self.scorer.calculate(session, query, context)
            if score >= options.min_relevance:
                scored_sessions.append((score, session))

        # Sort by relevance
        scored_sessions.sort(key=lambda x: -x[0])

        # Extract decisions from top sessions
        decisions = []
        explored_session_ids = []
        total_relevance = 0.0

        for score, session in scored_sessions:
            if len(decisions) >= options.limit:
                break

            # Get decisions from session
            session_decisions = self._extract_decisions(session)

            for decision_content in session_decisions:
                if len(decisions) >= options.limit:
                    break

                # Check for duplicates
                dup_result = await self.deduplicator.check_duplicate(decision_content)

                if not dup_result.is_duplicate:
                    # Add fingerprint
                    fingerprint = await self.deduplicator.add_fingerprint(
                        content=decision_content,
                        source_session=session.session_id,
                    )

                    decision = Decision(
                        content=decision_content,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        source_session=session.session_id,
                        fingerprint=fingerprint,
                    )

                    decisions.append(decision)

            explored_session_ids.append(session.session_id)
            total_relevance += score

            # Mark as explored
            await self.mark_explored(
                session_id=session.session_id,
                by_session=current_session_id,
                relevance=score,
                decisions_count=len(session_decisions),
            )

        return ExplorationResult(
            decisions=decisions,
            explored_sessions=explored_session_ids,
            total_relevance=total_relevance,
            query=query,
        )

    def _discover_sessions(self) -> list[SessionData]:
        """Discover available sessions."""
        sessions = []

        if not self.sessions_dir.exists():
            return sessions

        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, encoding="utf-8") as f:
                    data = json.load(f)

                session = SessionData(
                    session_id=data.get("session_id", session_file.stem),
                    decisions=data.get("decisions", []),
                    project=data.get("project", ""),
                    working_directory=data.get("working_directory", ""),
                    timestamp=data.get("timestamp", ""),
                )
                sessions.append(session)
            except (json.JSONDecodeError, IOError):
                continue

        return sessions

    def _extract_decisions(self, session: SessionData) -> list[str]:
        """Extract decision content from session."""
        decisions = []

        for decision in session.decisions:
            if isinstance(decision, dict):
                content = decision.get("content", "")
                if content:
                    decisions.append(content)
            elif isinstance(decision, str):
                decisions.append(decision)

        return decisions[: self.config.max_decisions_per_session]

    async def mark_explored(
        self,
        session_id: str,
        by_session: str,
        relevance: float = 0.0,
        decisions_count: int = 0,
    ) -> None:
        """Mark a session as having been explored.

        Args:
            session_id: Session that was explored
            by_session: Session that did the exploring
            relevance: Relevance score
            decisions_count: Number of decisions extracted
        """
        record = ExplorationRecord(
            session_id=session_id,
            explored_by=by_session,
            explored_at=datetime.now(timezone.utc).isoformat(),
            relevance_score=relevance,
            decisions_extracted=decisions_count,
        )

        self.storage.save_exploration(record)

    def is_explored(
        self,
        session_id: str,
        by_session: Optional[str] = None,
    ) -> bool:
        """Check if a session has been explored.

        Args:
            session_id: Session to check
            by_session: Optional filter by exploring session

        Returns:
            True if session has been explored
        """
        record = self.storage.get_exploration(session_id)

        if record is None:
            return False

        if by_session:
            return record.explored_by == by_session

        return True

    def get_stats(self) -> ExplorationStats:
        """Get exploration statistics.

        Returns:
            ExplorationStats
        """
        explorations = self.storage.get_all_explorations()
        fingerprints = self.deduplicator.get_all_keywords()
        sessions = self._discover_sessions()

        return ExplorationStats(
            total_explored_sessions=len(explorations),
            total_unique_decisions=len(fingerprints),
            known_keywords_count=len(fingerprints),
            available_session_files=len(sessions),
        )

    def close(self) -> None:
        """Close storage connections."""
        self.storage.close()
        self.deduplicator.close()
