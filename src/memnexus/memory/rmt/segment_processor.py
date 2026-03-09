"""
SegmentProcessor for RMT (Recurrent Memory Transformer).

Handles sequence segmentation with memory injection and extraction.
Enables processing long sequences by splitting them into manageable segments.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Iterator
import numpy as np


@dataclass
class Segment:
    """A sequence segment with memory tokens."""

    tokens: np.ndarray
    segment_id: int
    memory_tokens: Optional[np.ndarray] = None
    start_pos: int = 0
    end_pos: int = 0

    def __post_init__(self):
        if self.end_pos == 0:
            self.end_pos = self.start_pos + len(self.tokens)


@dataclass
class SegmentConfig:
    """Configuration for segment processing."""

    segment_size: int = 2048
    overlap_size: int = 128
    memory_token_count: int = 16
    padding_token_id: int = 0

    def effective_segment_size(self) -> int:
        """Get effective size excluding overlap."""
        return self.segment_size - self.overlap_size


class SegmentProcessor:
    """
    Processor for segmenting sequences and managing memory tokens.

    RMT processes long sequences by:
    1. Splitting into overlapping segments
    2. Injecting memory tokens at segment boundaries
    3. Extracting updated memory after processing
    4. Passing memory to next segment

    This enables O(n) complexity instead of O(n²) for long sequences.

    Example:
        >>> processor = SegmentProcessor(segment_size=2048, memory_tokens=16)
        >>> tokens = np.random.randint(0, 50000, size=100000)  # 100K tokens
        >>> segments = list(processor.segment_sequence(tokens))
        >>> len(segments)  # ~50 segments
        50
    """

    def __init__(
        self,
        segment_size: int = 2048,
        overlap_size: int = 128,
        memory_token_count: int = 16,
        padding_token_id: int = 0,
    ):
        """
        Initialize segment processor.

        Args:
            segment_size: Maximum tokens per segment
            overlap_size: Overlapping tokens between segments
            memory_token_count: Number of memory tokens to inject
            padding_token_id: Token ID for padding
        """
        self.config = SegmentConfig(
            segment_size=segment_size,
            overlap_size=overlap_size,
            memory_token_count=memory_token_count,
            padding_token_id=padding_token_id,
        )

    def segment_sequence(
        self,
        tokens: np.ndarray,
        segment_size: Optional[int] = None,
    ) -> Iterator[Segment]:
        """
        Split tokens into overlapping segments.

        Args:
            tokens: Input token array of shape (seq_len,)
            segment_size: Optional override for segment size

        Yields:
            Segment objects with position information

        Example:
            >>> tokens = np.arange(10000)
            >>> processor = SegmentProcessor(segment_size=2048, overlap_size=128)
            >>> segments = list(processor.segment_sequence(tokens))
            >>> segments[0].tokens.shape[0]  # First segment
            2048
        """
        if segment_size is None:
            segment_size = self.config.segment_size

        seq_len = len(tokens)
        effective_size = segment_size - self.config.overlap_size

        segment_id = 0
        start = 0

        while start < seq_len:
            end = min(start + segment_size, seq_len)

            # Extract segment tokens
            segment_tokens = tokens[start:end]

            # Pad if necessary
            if len(segment_tokens) < segment_size:
                padding = np.full(
                    segment_size - len(segment_tokens),
                    self.config.padding_token_id,
                    dtype=tokens.dtype,
                )
                segment_tokens = np.concatenate([segment_tokens, padding])

            yield Segment(
                tokens=segment_tokens,
                segment_id=segment_id,
                start_pos=start,
                end_pos=end,
            )

            # Move to next segment with overlap
            start += effective_size
            segment_id += 1

    def inject_memory(
        self,
        segment: Segment,
        memory_tokens: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Inject memory tokens into a segment.

        Memory tokens are prepended to the segment, creating a
        "memory-augmented" input that carries context from previous segments.

        Args:
            segment: The segment to augment
            memory_tokens: Memory tokens from previous segment (optional).
                          Can be 1D (token IDs) or 2D (embeddings).

        Returns:
            Augmented token array with memory tokens prepended

        Example:
            >>> segment = Segment(tokens=np.arange(100), segment_id=0)
            >>> memory = np.array([999] * 16)
            >>> augmented = processor.inject_memory(segment, memory)
            >>> augmented[:16]  # First 16 tokens are memory
            array([999, 999, ...])
        """
        if memory_tokens is None:
            # Initialize empty memory tokens (1D token IDs)
            memory_tokens = np.full(
                self.config.memory_token_count,
                self.config.padding_token_id,
                dtype=segment.tokens.dtype,
            )

        # Handle 2D memory tokens (embeddings) - flatten to 1D for token injection
        if memory_tokens.ndim == 2:
            # For embeddings, we create placeholder token IDs
            # In practice, these would be special memory token IDs
            memory_tokens = np.full(
                self.config.memory_token_count,
                self.config.padding_token_id,
                dtype=segment.tokens.dtype,
            )

        # Ensure correct count
        if len(memory_tokens) != self.config.memory_token_count:
            raise ValueError(
                f"Memory token count mismatch: {len(memory_tokens)} "
                f"!= {self.config.memory_token_count}"
            )

        # Prepend memory tokens to segment
        return np.concatenate([memory_tokens, segment.tokens])

    def extract_memory(
        self,
        output: np.ndarray,
        from_input: bool = True,
    ) -> np.ndarray:
        """
        Extract memory tokens from model output.

        Args:
            output: Model output tensor of shape (seq_len, hidden_dim)
                   or token array of shape (seq_len,)
            from_input: If True, extract from beginning (input memory position)
                       If False, extract from end (output memory position)

        Returns:
            Memory tokens array

        Example:
            >>> # Simulate model output with 2048 + 16 memory tokens
            >>> output = np.random.randn(2064, 768)
            >>> memory = processor.extract_memory(output)
            >>> memory.shape
            (16, 768)
        """
        if from_input:
            # Memory tokens are at the beginning
            return output[: self.config.memory_token_count]
        else:
            # Memory tokens are at the end
            return output[-self.config.memory_token_count :]

    def create_memory_tokens(
        self,
        hidden_dim: int,
        dtype=None,
    ) -> np.ndarray:
        """
        Initialize memory tokens for the first segment.

        Args:
            hidden_dim: Dimension of hidden states
            dtype: Data type for tokens

        Returns:
            Initialized memory tokens
        """
        # Use small random initialization (similar to transformer embeddings)
        if dtype is None:
            dtype = np.float32
        return np.random.randn(self.config.memory_token_count, hidden_dim).astype(dtype) * 0.02

    def merge_segment_outputs(
        self,
        segments: List[Segment],
        remove_overlap: bool = True,
    ) -> np.ndarray:
        """
        Merge processed segments back into a single sequence.

        Args:
            segments: List of processed segments
            remove_overlap: If True, remove overlapping regions

        Returns:
            Merged token array
        """
        if not segments:
            return np.array([])

        if remove_overlap:
            # Only take non-overlapping portions
            effective_size = self.config.effective_segment_size()
            parts = []
            for i, seg in enumerate(segments):
                start = self.config.memory_token_count  # Skip memory tokens
                if i > 0:
                    # Skip overlap from previous segment
                    start += self.config.overlap_size
                parts.append(seg.tokens[start : start + effective_size])
            return np.concatenate(parts)
        else:
            # Concatenate all tokens (with overlap)
            return np.concatenate([seg.tokens for seg in segments])

    def get_segment_count(
        self,
        seq_len: int,
        segment_size: Optional[int] = None,
    ) -> int:
        """
        Calculate number of segments needed for a sequence.

        Args:
            seq_len: Length of input sequence
            segment_size: Optional override for segment size

        Returns:
            Number of segments required
        """
        if segment_size is None:
            segment_size = self.config.segment_size

        effective_size = segment_size - self.config.overlap_size
        return (seq_len + effective_size - 1) // effective_size

    def estimate_flops_reduction(
        self,
        seq_len: int,
        hidden_dim: int = 768,
    ) -> float:
        """
        Estimate FLOPs reduction compared to full attention.

        RMT reduces complexity from O(n²) to O(n) by processing
        segments independently and passing memory tokens.

        Args:
            seq_len: Total sequence length
            hidden_dim: Hidden dimension of model

        Returns:
            Estimated FLOPs reduction factor
        """
        # Standard attention: O(n² * d)
        standard_flops = seq_len * seq_len * hidden_dim

        # RMT: O(k * m² * d) where k = num segments, m = segment size
        num_segments = self.get_segment_count(seq_len)
        segment_size = self.config.segment_size
        rmt_flops = num_segments * segment_size * segment_size * hidden_dim

        return standard_flops / rmt_flops if rmt_flops > 0 else 1.0


__all__ = [
    "Segment",
    "SegmentConfig",
    "SegmentProcessor",
]
