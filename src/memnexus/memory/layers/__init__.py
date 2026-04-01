"""Hierarchical memory layers.

.. warning::
    EXPERIMENTAL - Frozen in v1.0
    This module contains experimental features that are not actively maintained.
    For stable functionality, use MemoryStore from memnexus.memory.store.
"""

import warnings

warnings.warn(
    "memory.layers is experimental and frozen in v1.0. "
    "Use memory.store for stable functionality.",
    DeprecationWarning,
    stacklevel=2,
)

from memnexus.memory.layers.base import (
    AbstractMemoryLayer,
    Compressor,
    LLMCompressor,
    ShortTermMemoryLayer,
    WorkingMemoryLayer,
)
from memnexus.memory.layers.manager import (
    HierarchicalMemoryManager,
    LongTermMemoryLayer,
)

__all__ = [
    "AbstractMemoryLayer",
    "Compressor",
    "LLMCompressor",
    "WorkingMemoryLayer",
    "ShortTermMemoryLayer",
    "LongTermMemoryLayer",
    "HierarchicalMemoryManager",
]
