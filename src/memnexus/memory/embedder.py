"""Lightweight embedding for MemNexus.

Two embedding options available:
1. TF-IDF (default): Lightweight, zero dependencies, good for code search
2. External API: Best quality via OpenAI API (requires `pip install openai`)

Recommended setup:
- Default (TF-IDF): Fast install, works out of the box
- OpenAI API: Set embedding.method="openai" in config.yaml for best quality
"""

import hashlib
import math
import re
from collections import Counter


class TfidfEmbedder:
    """Lightweight TF-IDF embedder for code search.

    This is a simplified TF-IDF implementation optimized for code:
    - Tokenizes by splitting on non-alphanumeric characters
    - Lowercases all tokens
    - Removes common stopwords
    - Uses fixed vocabulary size for consistent embedding dimensions

    Pros:
    - Zero dependencies (only Python standard library)
    - Fast (no neural network inference)
    - Good for keyword matching in code

    Cons:
    - No semantic understanding ("auth" != "authentication")
    - Lower quality than neural embeddings

    For production use, consider external APIs:
    >>> embedder = ExternalApiEmbedder(api_key="...", model="text-embedding-3-small")

    Example:
        >>> embedder = TfidfEmbedder(dim=384)
        >>> embedding = embedder.embed("def authenticate_user(username, password):")
        >>> len(embedding)
        384
    """

    # Common English stopwords + code keywords
    STOPWORDS = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "shall",
        "can",
        "need",
        "dare",
        "ought",
        "used",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "under",
        "and",
        "but",
        "or",
        "yet",
        "so",
        "if",
        "because",
        "although",
        "though",
        "while",
        "where",
        "when",
        "that",
        "which",
        "who",
        "whom",
        "whose",
        "what",
        "this",
        "these",
        "those",
        "i",
        "me",
        "my",
        "myself",
        "we",
        "our",
        "you",
        "your",
        "he",
        "him",
        "his",
        "she",
        "her",
        "it",
        "its",
        "they",
        "them",
        "their",
        "def",
        "return",
        "else",
        "class",
        "import",
        "try",
        "except",
        "finally",
        "pass",
        "none",
        "true",
        "false",
        "self",
        "cls",
        "not",
    }

    def __init__(self, dim: int = 384, max_features: int = 10000):
        """Initialize TF-IDF embedder.

        Args:
            dim: Embedding dimension (default: 384 to match all-MiniLM-L6-v2)
            max_features: Maximum vocabulary size
        """
        self.dim = dim
        self.max_features = max_features
        self._vocab: dict[str, int] = {}
        self._idf: dict[str, float] = {}
        self._document_count = 0

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into words."""
        # Split on non-alphanumeric, keep underscores (for code)
        tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text.lower())
        # Filter stopwords and short tokens
        return [t for t in tokens if t not in self.STOPWORDS and len(t) > 1]

    def _get_token_hash(self, token: str) -> int:
        """Get consistent hash for token to map to dimension."""
        return int(hashlib.md5(token.encode()).hexdigest(), 16)

    def embed(self, text: str) -> list[float]:
        """Embed text into vector.

        Args:
            text: Text to embed

        Returns:
            Embedding vector of dimension self.dim
        """
        tokens = self._tokenize(text)

        if not tokens:
            return [0.0] * self.dim

        # Count tokens (TF)
        token_counts = Counter(tokens)
        total_tokens = len(tokens)

        # Create sparse vector
        vector = [0.0] * self.dim

        for token, count in token_counts.items():
            # TF: term frequency
            tf = count / total_tokens

            # Map token to dimension using hash
            dim_idx = self._get_token_hash(token) % self.dim

            # Accumulate (multiple tokens can map to same dimension)
            vector[dim_idx] += tf

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts."""
        return [self.embed(text) for text in texts]


class HashEmbedder:
    """Ultra-lightweight embedder using feature hashing.

    Even simpler than TF-IDF, just hashes tokens to dimensions.
    Good for very fast, low-memory embedding.

    Example:
        >>> embedder = HashEmbedder(dim=384)
        >>> embedding = embedder.embed("def authenticate_user(username, password):")
    """

    def __init__(self, dim: int = 384, ngram_range: tuple = (1, 2)):
        """Initialize hash embedder.

        Args:
            dim: Embedding dimension
            ngram_range: (min_n, max_n) for character n-grams
        """
        self.dim = dim
        self.ngram_range = ngram_range

    def _get_ngrams(self, text: str) -> list[str]:
        """Extract character n-grams from text."""
        text = text.lower()
        ngrams = []
        for n in range(self.ngram_range[0], self.ngram_range[1] + 1):
            for i in range(len(text) - n + 1):
                ngrams.append(text[i : i + n])
        return ngrams

    def embed(self, text: str) -> list[float]:
        """Embed text using feature hashing."""
        ngrams = self._get_ngrams(text)

        vector = [0.0] * self.dim

        for ngram in ngrams:
            # Hash ngram to dimension
            idx = int(hashlib.md5(ngram.encode()).hexdigest(), 16) % self.dim
            # Use sign based on hash for better distribution
            sign = 1 if int(hashlib.md5((ngram + "sign").encode()).hexdigest(), 16) % 2 == 0 else -1
            vector[idx] += sign

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector


class ExternalApiEmbedder:
    """Embedder that calls external API (OpenAI, etc.).

    For best quality embeddings, use external APIs:
    - OpenAI: text-embedding-3-small (cheap, good quality)
    - Cohere: embed-english-v3
    - Voyage: voyage-lite-02-instruct

    Example:
        >>> embedder = ExternalApiEmbedder(
        ...     api_key="sk-...",
        ...     provider="openai",
        ...     model="text-embedding-3-small"
        ... )
        >>> embedding = embedder.embed("def authenticate_user(username, password):")
    """

    def __init__(
        self,
        api_key: str,
        provider: str = "openai",
        model: str | None = None,
        api_base: str | None = None,
    ):
        """Initialize external API embedder.

        Args:
            api_key: API key
            provider: "openai", "cohere", or "custom"
            model: Model name (provider-specific)
            api_base: Custom API base URL (for self-hosted)
        """
        self.api_key = api_key
        self.provider = provider
        self.api_base = api_base

        # Default models
        if model is None:
            if provider == "openai":
                model = "text-embedding-3-small"
            elif provider == "cohere":
                model = "embed-english-v3"

        self.model = model
        self._client = None

    def _get_client(self):
        """Lazy load client."""
        if self._client is None:
            if self.provider == "openai":
                try:
                    import openai
                except ImportError:
                    raise ImportError("OpenAI client not installed. Run: pip install openai")
                self._client = openai.OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base,
                )
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

        return self._client

    def embed(self, text: str) -> list[float]:
        """Embed text using external API."""
        client = self._get_client()

        if self.provider == "openai":
            response = client.embeddings.create(
                model=self.model,
                input=text,
            )
            return response.data[0].embedding

        raise ValueError(f"Unsupported provider: {self.provider}")

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts."""
        client = self._get_client()

        if self.provider == "openai":
            response = client.embeddings.create(
                model=self.model,
                input=texts,
            )
            return [r.embedding for r in response.data]

        # Fallback to individual calls
        return [self.embed(text) for text in texts]


def get_embedder(method: str = "tfidf", dim: int = 384, **kwargs):
    """Get embedder by method name.

    Two options available:
    1. TF-IDF (default): Lightweight, zero dependencies, good for keyword matching
    2. External API: Best quality embeddings via OpenAI/Cohere/etc.

    Args:
        method: "tfidf", "hash", or "openai"
        dim: Embedding dimension (for local methods)
        **kwargs: Additional args for specific methods

    Returns:
        Embedder instance

    Examples:
        >>> # Default: lightweight TF-IDF
        >>> embedder = get_embedder()

        >>> # External API (best quality)
        >>> embedder = get_embedder(
        ...     method="openai",
        ...     api_key="sk-...",
        ...     model="text-embedding-3-small"
        ... )
    """
    if method == "tfidf":
        return TfidfEmbedder(dim=dim)
    elif method == "hash":
        return HashEmbedder(dim=dim)
    elif method == "openai":
        return ExternalApiEmbedder(
            api_key=kwargs.get("api_key"),
            provider="openai",
            model=kwargs.get("model", "text-embedding-3-small"),
        )
    else:
        raise ValueError(f"Unknown embedding method: {method}. Use 'tfidf', 'hash', or 'openai'.")
