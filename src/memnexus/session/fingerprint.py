"""Semantic fingerprinting for decision deduplication."""

import hashlib
import re
from dataclasses import dataclass
from typing import Optional

from memnexus.session.models import DecisionFingerprint


@dataclass
class FingerprintResult:
    """Result of fingerprinting."""

    hash: str
    keywords: list[str]
    content_preview: str


class KeywordExtractor:
    """Extract keywords from text content."""

    # Common stop words to filter out
    STOP_WORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "must", "shall",
        "can", "need", "dare", "ought", "used", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "as", "into",
        "through", "during", "before", "after", "above", "below",
        "between", "under", "and", "but", "or", "yet", "so", "if",
        "because", "although", "though", "while", "where", "when",
        "that", "which", "who", "whom", "whose", "what", "this",
        "these", "those", "i", "you", "he", "she", "it", "we",
        "they", "me", "him", "her", "us", "them", "my", "your",
        "his", "her", "its", "our", "their", "mine", "yours",
        "hers", "ours", "theirs", "myself", "yourself", "himself",
        "herself", "itself", "ourselves", "yourselves", "themselves",
    }

    # Technical terms to boost weight
    TECH_TERMS = {
        "api", "database", "db", "sql", "nosql", "redis", "cache",
        "server", "client", "frontend", "backend", "fullstack",
        "microservice", "monolith", "docker", "kubernetes", "k8s",
        "aws", "gcp", "azure", "cloud", "lambda", "serverless",
        "auth", "authentication", "authorization", "jwt", "oauth",
        "password", "token", "session", "cookie", "encryption",
        "https", "ssl", "tls", "security", "firewall", "vpn",
        "react", "vue", "angular", "svelte", "frontend", "ui",
        "component", "hook", "state", "props", "redux", "context",
        "node", "nodejs", "express", "fastapi", "django", "flask",
        "spring", "rails", "laravel", "python", "javascript",
        "typescript", "java", "go", "golang", "rust", "c++", "c#",
        "ruby", "php", "kotlin", "swift", "dart", "flutter",
        "testing", "test", "unittest", "pytest", "jest", "mocha",
        "cypress", "selenium", "e2e", "integration", "coverage",
        "git", "github", "gitlab", "ci", "cd", "pipeline",
        "jenkins", "githubactions", "travis", "circleci",
        "refactor", "rewrite", "migrate", "upgrade", "update",
        "fix", "bugfix", "hotfix", "patch", "optimize",
        "performance", "memory", "cpu", "speed", "latency",
        "architecture", "design", "pattern", "solid", "dry",
        "kiss", "clean", "hexagonal", "domain", "ddd",
    }

    def __init__(self, min_length: int = 3, max_keywords: int = 20):
        self.min_length = min_length
        self.max_keywords = max_keywords

    def extract(self, content: str) -> list[str]:
        """Extract keywords from content.

        Returns list of keywords sorted by relevance (most relevant first).
        """
        # Normalize text
        normalized = content.lower()
        normalized = re.sub(r"[^\w\s]", " ", normalized)

        # Extract words
        words = normalized.split()

        # Count word frequencies
        word_counts: dict[str, int] = {}
        for word in words:
            # Skip short words and stop words
            if len(word) < self.min_length or word in self.STOP_WORDS:
                continue

            # Apply weights
            count = 1
            if word in self.TECH_TERMS:
                count = 3  # Boost technical terms

            word_counts[word] = word_counts.get(word, 0) + count

        # Sort by frequency and get top keywords
        sorted_words = sorted(
            word_counts.items(),
            key=lambda x: (-x[1], x[0]),  # Sort by count desc, then alphabetically
        )

        keywords = [word for word, _ in sorted_words[:self.max_keywords]]
        return keywords


class MinHashFingerprinter:
    """MinHash-based semantic fingerprinter."""

    def __init__(
        self,
        num_hashes: int = 128,
        num_bands: int = 16,
        rows_per_band: int = 8,
    ):
        self.num_hashes = num_hashes
        self.num_bands = num_bands
        self.rows_per_band = rows_per_band
        self.keyword_extractor = KeywordExtractor()

        # Initialize hash functions
        self._hash_seeds = [i * 1000 + 12345 for i in range(num_hashes)]

    def _get_shingles(self, text: str, k: int = 3) -> set[str]:
        """Get k-shingles (word n-grams) from text."""
        words = text.lower().split()
        if len(words) < k:
            return set(words)

        shingles = set()
        for i in range(len(words) - k + 1):
            shingle = " ".join(words[i : i + k])
            shingles.add(shingle)
        return shingles

    def _compute_minhash(self, shingles: set[str]) -> list[int]:
        """Compute MinHash signature."""
        signature = []

        for seed in self._hash_seeds:
            min_hash = float("inf")
            for shingle in shingles:
                # Combine seed with shingle hash
                combined = f"{seed}:{shingle}"
                hash_val = hashlib.md5(combined.encode()).hexdigest()
                int_hash = int(hash_val, 16)
                min_hash = min(min_hash, int_hash)
            signature.append(min_hash)

        return signature

    def fingerprint(self, content: str, source_session: str = "") -> FingerprintResult:
        """Generate fingerprint for content.

        Args:
            content: The decision content to fingerprint
            source_session: Source session ID

        Returns:
            FingerprintResult with hash, keywords, and preview
        """
        # Extract keywords
        keywords = self.keyword_extractor.extract(content)

        # Generate shingles
        shingles = self._get_shingles(content)

        # Compute MinHash signature
        signature = self._compute_minhash(shingles)

        # Create hash from signature
        signature_str = ",".join(str(x) for x in signature)
        hash_val = hashlib.sha256(signature_str.encode()).hexdigest()[:16]

        # Create preview (first 100 chars)
        preview = content[:100].replace("\n", " ").strip()
        if len(content) > 100:
            preview += "..."

        return FingerprintResult(
            hash=hash_val,
            keywords=keywords,
            content_preview=preview,
        )

    def estimate_similarity(self, sig1: list[int], sig2: list[int]) -> float:
        """Estimate Jaccard similarity from MinHash signatures.

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if len(sig1) != len(sig2):
            return 0.0

        matches = sum(1 for a, b in zip(sig1, sig2) if a == b)
        return matches / len(sig1)


def create_fingerprint(
    content: str,
    source_session: str,
    timestamp: str,
) -> DecisionFingerprint:
    """Create a DecisionFingerprint from content.

    Args:
        content: Decision content
        source_session: Source session ID
        timestamp: ISO timestamp

    Returns:
        DecisionFingerprint
    """
    fingerprinter = MinHashFingerprinter()
    result = fingerprinter.fingerprint(content, source_session)

    return DecisionFingerprint(
        hash=result.hash,
        keywords=result.keywords,
        timestamp=timestamp,
        source_session=source_session,
        content_preview=result.content_preview,
    )
