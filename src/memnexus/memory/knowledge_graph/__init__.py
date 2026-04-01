"""Knowledge Graph integration for MemNexus.

.. warning::
    EXPERIMENTAL - Frozen in v1.0
    This module contains experimental features that are not actively maintained.
    These features are research-oriented (HippoRAG-inspired) and not recommended
    for production use.
"""

import warnings

warnings.warn(
    "memory.knowledge_graph is experimental and frozen in v1.0. "
    "Not recommended for production use.",
    DeprecationWarning,
    stacklevel=2,
)

from memnexus.memory.knowledge_graph.builder import (
    KnowledgeGraphBuilder,
    KnowledgeGraphConfig,
    KnowledgeNode,
    KnowledgeRelation,
)

__all__ = [
    "KnowledgeGraphBuilder",
    "KnowledgeGraphConfig",
    "KnowledgeNode",
    "KnowledgeRelation",
]
