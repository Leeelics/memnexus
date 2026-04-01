"""Advanced retrieval strategies.

.. warning::
    EXPERIMENTAL - Frozen in v1.0
    This module contains experimental features that are not actively maintained.
    For stable retrieval, use basic search from MemoryStore.
"""

import warnings

warnings.warn(
    "memory.retrieval is experimental and frozen in v1.0. "
    "Use memory.store for stable retrieval.",
    DeprecationWarning,
    stacklevel=2,
)

from memnexus.memory.retrieval.adaptive import (
    AdaptiveRetriever,
    HybridRetriever,
    QueryHistory,
    UncertaintyEstimate,
)

__all__ = [
    "AdaptiveRetriever",
    "HybridRetriever",
    "QueryHistory",
    "UncertaintyEstimate",
]
