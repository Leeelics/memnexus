"""Decision deduplication using semantic fingerprints."""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from memnexus.session.fingerprint import MinHashFingerprinter, create_fingerprint
from memnexus.session.models import (
    Decision,
    DuplicateCheckResult,
)
from memnexus.session.storage import StorageBackend, create_storage


@dataclass
class DeduplicatorConfig:
    """Configuration for DecisionDeduplicator."""

    similarity_threshold: float = 0.8
    max_similar_items: int = 5


class DecisionDeduplicator:
    """Content-based deduplication for decisions.

    Example:
        >>> dedup = DecisionDeduplicator()
        >>> result = await dedup.check_duplicate("Use PostgreSQL for user data")
        >>> if result.is_duplicate:
        ...     print(f"Similar to: {result.similar_decisions[0].content}")
    """

    def __init__(
        self,
        storage_path: Path | None = None,
        config: DeduplicatorConfig | None = None,
        storage_backend: str = "auto",
    ):
        """Initialize the deduplicator.

        Args:
            storage_path: Path to store fingerprint data
            config: Deduplicator configuration
            storage_backend: "sqlite", "json", or "auto"
        """
        if storage_path is None:
            storage_path = Path.home() / ".memnexus" / "explorer"

        self.storage_path = Path(storage_path)
        self.config = config or DeduplicatorConfig()
        self.storage: StorageBackend = create_storage(self.storage_path, storage_backend)
        self.fingerprinter = MinHashFingerprinter()

    async def check_duplicate(
        self,
        content: str,
        context: dict | None = None,
    ) -> DuplicateCheckResult:
        """Check if content is a duplicate.

        Args:
            content: Content to check
            context: Additional context (not used yet)

        Returns:
            DuplicateCheckResult with is_duplicate, confidence, similar_items
        """
        # Generate fingerprint for input content
        temp_fingerprint = self.fingerprinter.fingerprint(content, "")

        # Load all existing fingerprints
        existing = self.storage.get_all_fingerprints()

        if not existing:
            # No existing fingerprints, not a duplicate
            return DuplicateCheckResult(
                is_duplicate=False,
                confidence=0.0,
                similar_decisions=[],
                fingerprint=temp_fingerprint.hash,
            )

        # Compute similarities
        similar_items = []
        max_similarity = 0.0

        for fp_hash, fingerprint in existing.items():
            # Reconstruct signature from stored fingerprint
            # For efficiency, we just compare keywords overlap
            similarity = self._estimate_similarity(
                temp_fingerprint.keywords,
                fingerprint.keywords,
            )

            if similarity > 0.3:  # Only consider items with some similarity
                decision = Decision(
                    content=fingerprint.content_preview,
                    timestamp=fingerprint.timestamp,
                    source_session=fingerprint.source_session,
                    fingerprint=fingerprint.hash,
                    metadata={"keywords": fingerprint.keywords},
                )

                similar_items.append((similarity, decision))

                if similarity > max_similarity:
                    max_similarity = similarity

        # Sort by similarity and take top N
        similar_items.sort(key=lambda x: -x[0])
        top_similar = [item for _, item in similar_items[: self.config.max_similar_items]]

        # Determine if duplicate based on threshold
        is_duplicate = max_similarity >= self.config.similarity_threshold

        # Confidence is the max similarity
        confidence = max_similarity if is_duplicate else max_similarity

        return DuplicateCheckResult(
            is_duplicate=is_duplicate,
            confidence=confidence,
            similar_decisions=top_similar,
            fingerprint=temp_fingerprint.hash,
        )

    def _estimate_similarity(
        self,
        keywords1: list[str],
        keywords2: list[str],
    ) -> float:
        """Estimate similarity based on keyword overlap.

        Returns:
            Jaccard-like similarity score (0.0-1.0)
        """
        if not keywords1 or not keywords2:
            return 0.0

        set1 = set(keywords1)
        set2 = set(keywords2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union

    async def add_fingerprint(
        self,
        content: str,
        source_session: str = "",
        metadata: dict | None = None,
    ) -> str:
        """Add a fingerprint for content.

        Args:
            content: Decision content
            source_session: Source session ID
            metadata: Additional metadata

        Returns:
            The fingerprint hash
        """
        timestamp = datetime.now(UTC).isoformat()

        fingerprint = create_fingerprint(
            content=content,
            source_session=source_session,
            timestamp=timestamp,
        )

        self.storage.save_fingerprint(fingerprint)

        return fingerprint.hash

    def get_all_keywords(self) -> set[str]:
        """Get all known keywords from fingerprints.

        Returns:
            Set of all keywords
        """
        fingerprints = self.storage.get_all_fingerprints()
        all_keywords = set()

        for fp in fingerprints.values():
            all_keywords.update(fp.keywords)

        return all_keywords

    def get_stats(self) -> dict:
        """Get deduplicator statistics.

        Returns:
            Dict with stats
        """
        fingerprints = self.storage.get_all_fingerprints()

        return {
            "total_fingerprints": len(fingerprints),
            "unique_keywords": len(self.get_all_keywords()),
            "storage_path": str(self.storage_path),
        }

    def close(self) -> None:
        """Close storage connection."""
        self.storage.close()
