"""Relevance scoring for session exploration."""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from memnexus.session.models import ScorerConfig


@dataclass
class SessionData:
    """Session data for scoring."""

    session_id: str
    decisions: list[dict]  # List of decision dicts with "content" key
    project: str = ""
    working_directory: str = ""
    timestamp: str = ""


class RelevanceScorer:
    """Calculates relevance scores between sessions and queries.

    Example:
        >>> scorer = RelevanceScorer()
        >>> session = SessionData(
        ...     session_id="abc",
        ...     decisions=[{"content": "Use PostgreSQL"}],
        ...     project="myapp"
        ... )
        >>> score = scorer.calculate(session, "database choice")
        >>> print(f"Relevance: {score:.2f}")
    """

    def __init__(self, config: Optional[ScorerConfig] = None):
        """Initialize with optional custom weights.

        Args:
            config: Scorer configuration with custom weights
        """
        self.config = config or ScorerConfig()

    def calculate(
        self,
        session_data: SessionData | dict,
        query: str,
        context: Optional[dict] = None,
    ) -> float:
        """Calculate relevance score.

        Args:
            session_data: Session data or dict
            query: Search query
            context: Additional context (cwd, project, etc.)

        Returns:
            Score between 0.0 and 1.0
        """
        if isinstance(session_data, dict):
            session_data = SessionData(**session_data)

        if context is None:
            context = {}

        # Extract query keywords
        query_keywords = set(self._extract_keywords(query))
        if not query_keywords:
            return 0.0

        # Calculate keyword match score
        keyword_score = self._calculate_keyword_score(
            session_data.decisions, query_keywords
        )

        # Calculate project match bonus
        project_bonus = self._calculate_project_bonus(
            session_data, context.get("project", ""), context.get("cwd", "")
        )

        # Calculate time decay
        time_decay = self._calculate_time_decay(session_data.timestamp)

        # Combined score
        base_score = (
            keyword_score * self.config.keyword_weight +
            project_bonus * self.config.project_weight
        )

        # Apply time decay
        final_score = base_score * time_decay

        # Normalize to 0.0-1.0
        max_possible = (
            self.config.keyword_weight +
            self.config.project_weight
        )
        normalized = min(1.0, final_score / max_possible if max_possible > 0 else 0)

        return normalized

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from text."""
        # Normalize
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)

        # Extract words
        words = text.split()

        # Filter short words and common stop words
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "can", "to", "of",
            "in", "for", "on", "with", "at", "by", "from", "as", "and",
            "but", "or", "yet", "so", "it", "this", "that", "these",
            "those", "i", "you", "he", "she", "we", "they",
        }

        keywords = [
            w for w in words
            if len(w) >= 3 and w not in stop_words
        ]

        return keywords

    def _calculate_keyword_score(
        self,
        decisions: list[dict],
        query_keywords: set[str],
    ) -> float:
        """Calculate keyword match score."""
        if not decisions or not query_keywords:
            return 0.0

        total_matches = 0
        total_words = 0

        for decision in decisions:
            content = decision.get("content", "")
            decision_keywords = set(self._extract_keywords(content))

            matches = len(query_keywords & decision_keywords)
            total_matches += matches
            total_words += len(decision_keywords) + len(query_keywords)

        if total_words == 0:
            return 0.0

        # Normalize by total words
        return total_matches / len(query_keywords)

    def _calculate_project_bonus(
        self,
        session_data: SessionData,
        current_project: str,
        current_cwd: str,
    ) -> float:
        """Calculate project/path match bonus."""
        bonus = 0.0

        # Same project
        if current_project and session_data.project:
            if current_project == session_data.project:
                bonus += 1.0

        # Related path (one is subdirectory of other)
        if current_cwd and session_data.working_directory:
            cwd = current_cwd.rstrip("/")
            session_dir = session_data.working_directory.rstrip("/")

            if cwd == session_dir:
                bonus += 0.5
            elif cwd.startswith(session_dir + "/") or session_dir.startswith(cwd + "/"):
                bonus += 0.3

        return bonus

    def _calculate_time_decay(self, timestamp_str: str) -> float:
        """Calculate time decay factor.

        Uses exponential decay with configurable half-life.
        """
        if not timestamp_str:
            return 0.5  # Neutral if no timestamp

        try:
            # Parse timestamp
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1] + "+00:00"

            timestamp = datetime.fromisoformat(timestamp_str)
            now = datetime.now(timezone.utc)

            # If timestamp has no timezone, assume UTC
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            age_days = (now - timestamp).total_seconds() / 86400

            # Exponential decay
            # time_decay_factor = 1.0 / (1.0 + age_in_days / 7)
            half_life = self.config.time_decay
            decay = 1.0 / (1.0 + age_days / half_life)

            return decay
        except (ValueError, TypeError):
            return 0.5  # Neutral on parse error
