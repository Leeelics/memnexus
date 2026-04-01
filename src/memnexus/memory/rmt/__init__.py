"""RMT (Recurrent Memory Transformer) implementation for MemNexus.

.. warning::
    EXPERIMENTAL - Frozen in v1.0
    This module contains experimental features that are not actively maintained.
    These features are research-oriented and not recommended for production use.

Enables processing sequences up to 2 million tokens by passing memory tokens
between segments, achieving linear complexity O(n) vs quadratic O(n²).

Reference: "Beyond Attention: Breaking the Limits of Transformer Context Length
with Recurrent Memory" (AAAI 2024)
"""

import warnings

warnings.warn(
    "memory.rmt is experimental and frozen in v1.0. "
    "Not recommended for production use.",
    DeprecationWarning,
    stacklevel=2,
)

from memnexus.memory.rmt.curriculum import CurriculumLearning
from memnexus.memory.rmt.memory_manager import RecurrentMemoryManager
from memnexus.memory.rmt.segment_processor import SegmentProcessor

__all__ = [
    "SegmentProcessor",
    "RecurrentMemoryManager",
    "CurriculumLearning",
]
