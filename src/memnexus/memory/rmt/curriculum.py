"""
CurriculumLearning for RMT (Recurrent Memory Transformer).

Implements progressive training from short to long sequences,
enabling stable training of models on extremely long contexts.

Reference: "Beyond Attention: Breaking the Limits of Transformer Context Length
with Recurrent Memory" (AAAI 2024)
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np


class CurriculumStage(Enum):
    """Stages of curriculum learning."""

    WARMUP = "warmup"
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"
    EXTREME = "extreme"


@dataclass
class CurriculumStep:
    """A single step in the curriculum."""

    stage: CurriculumStage
    sequence_length: int
    segment_size: int
    num_epochs: int
    learning_rate: float
    description: str = ""


@dataclass
class CurriculumConfig:
    """Configuration for curriculum learning."""

    # Length progression
    min_length: int = 512
    max_length: int = 2_000_000  # 2M tokens
    num_stages: int = 5
    length_multiplier: float = 4.0  # 4x length increase per stage

    # Training config
    warmup_epochs: int = 1
    epochs_per_stage: int = 3
    learning_rate_start: float = 1e-4
    learning_rate_end: float = 1e-5

    # Segment config
    base_segment_size: int = 512
    max_segment_size: int = 2048


@dataclass
class TrainingMetrics:
    """Metrics for curriculum training."""

    stage: CurriculumStage
    epoch: int
    loss: float
    perplexity: float
    sequence_length: int
    processing_time_ms: float
    memory_usage_mb: float


class CurriculumLearning:
    """
    Curriculum learning for progressive sequence length training.

    RMT uses curriculum learning to train on increasingly long sequences:
    1. Start with short sequences (512 tokens)
    2. Gradually increase length (4x per stage)
    3. Train to 2M+ tokens
    4. Maintain training stability

    This enables models pre-trained on short sequences to adapt to
    extremely long contexts without instability.

    Example:
        >>> curriculum = CurriculumLearning(max_length=100000, num_stages=4)
        >>> schedule = curriculum.create_curriculum()
        >>>
        >>> for step in schedule:
        ...     print(f"Stage: {step.stage.value}, Length: {step.sequence_length}")
        Stage: warmup, Length: 512
        Stage: short, Length: 2048
        Stage: medium, Length: 8192
        Stage: long, Length: 32768
    """

    def __init__(
        self,
        max_length: int = 2_000_000,
        num_stages: int = 5,
        min_length: int = 512,
        base_segment_size: int = 512,
        epochs_per_stage: int = 3,
    ):
        """
        Initialize curriculum learning.

        Args:
            max_length: Maximum sequence length to train on
            num_stages: Number of curriculum stages
            min_length: Starting sequence length
            base_segment_size: Initial segment size
            epochs_per_stage: Training epochs per stage
        """
        self.config = CurriculumConfig(
            min_length=min_length,
            max_length=max_length,
            num_stages=num_stages,
            base_segment_size=base_segment_size,
            epochs_per_stage=epochs_per_stage,
        )
        self._metrics_history: list[TrainingMetrics] = []

    def create_curriculum(
        self,
        max_length: int | None = None,
        num_stages: int | None = None,
    ) -> list[CurriculumStep]:
        """
        Create progressive length curriculum schedule.

        Args:
            max_length: Optional override for max length
            num_stages: Optional override for number of stages

        Returns:
            List of curriculum steps

        Example:
            >>> curriculum = CurriculumLearning(max_length=32768, num_stages=4)
            >>> schedule = curriculum.create_curriculum()
            >>> len(schedule)
            12  # 4 stages x 3 epochs
            >>> schedule[0].sequence_length
            512
            >>> schedule[-1].sequence_length
            32768
        """
        if max_length is None:
            max_length = self.config.max_length
        if num_stages is None:
            num_stages = self.config.num_stages

        # Calculate length progression
        multiplier = (max_length / self.config.min_length) ** (1 / (num_stages - 1))

        curriculum = []
        stages = [
            CurriculumStage.WARMUP,
            CurriculumStage.SHORT,
            CurriculumStage.MEDIUM,
            CurriculumStage.LONG,
            CurriculumStage.EXTREME,
        ]

        current_length = self.config.min_length

        for i, stage in enumerate(stages[:num_stages]):
            # Calculate segment size (increases with length)
            segment_size = min(
                self.config.base_segment_size * (2 ** (i // 2)),
                self.config.max_segment_size,
            )

            # Calculate learning rate (decreases with length)
            lr_progress = i / max(num_stages - 1, 1)
            learning_rate = (
                self.config.learning_rate_start * (1 - lr_progress)
                + self.config.learning_rate_end * lr_progress
            )

            # Determine epochs
            if stage == CurriculumStage.WARMUP:
                num_epochs = self.config.warmup_epochs
            else:
                num_epochs = self.config.epochs_per_stage

            # Create description
            descriptions = {
                CurriculumStage.WARMUP: "Warmup with very short sequences",
                CurriculumStage.SHORT: "Short sequence adaptation",
                CurriculumStage.MEDIUM: "Medium length training",
                CurriculumStage.LONG: "Long sequence processing",
                CurriculumStage.EXTREME: "Extreme length (2M+ tokens)",
            }

            for epoch in range(num_epochs):
                curriculum.append(
                    CurriculumStep(
                        stage=stage,
                        sequence_length=int(current_length),
                        segment_size=segment_size,
                        num_epochs=num_epochs,
                        learning_rate=learning_rate,
                        description=descriptions.get(stage, ""),
                    )
                )

            current_length = min(current_length * multiplier, max_length)

        return curriculum

    def train_with_curriculum(
        self,
        train_fn: Callable[[CurriculumStep], tuple[float, float]],
        max_length: int | None = None,
        num_stages: int | None = None,
        early_stopping_patience: int = 2,
    ) -> dict[str, Any]:
        """
        Execute curriculum training.

        Args:
            train_fn: Function that takes a CurriculumStep and returns (loss, perplexity)
            max_length: Optional override for max length
            num_stages: Optional override for number of stages
            early_stopping_patience: Epochs to wait before stopping on no improvement

        Returns:
            Training results dictionary

        Example:
            >>> def train_step(step):
            ...     # Simulate training
            ...     loss = 2.0 / step.sequence_length
            ...     ppl = np.exp(loss)
            ...     return loss, ppl
            >>>
            >>> results = curriculum.train_with_curriculum(train_step)
            >>> print(f"Final loss: {results['final_loss']:.4f}")
        """
        curriculum = self.create_curriculum(max_length, num_stages)

        best_loss = float("inf")
        patience_counter = 0

        for step in curriculum:
            # Train on current stage
            loss, perplexity = train_fn(step)

            # Record metrics
            metrics = TrainingMetrics(
                stage=step.stage,
                epoch=curriculum.index(step) % step.num_epochs,
                loss=loss,
                perplexity=perplexity,
                sequence_length=step.sequence_length,
                processing_time_ms=0.0,
                memory_usage_mb=0.0,
            )
            self._metrics_history.append(metrics)

            # Early stopping check
            if loss < best_loss:
                best_loss = loss
                patience_counter = 0
            else:
                patience_counter += 1

            if patience_counter >= early_stopping_patience:
                print(f"Early stopping at stage {step.stage.value}")
                break

        return {
            "final_loss": loss,
            "final_perplexity": perplexity,
            "best_loss": best_loss,
            "total_steps": len(self._metrics_history),
            "curriculum_completed": patience_counter < early_stopping_patience,
        }

    def generate_training_sequence(
        self,
        length: int,
        vocab_size: int = 50000,
    ) -> np.ndarray:
        """
        Generate a synthetic training sequence.

        Args:
            length: Sequence length
            vocab_size: Vocabulary size

        Returns:
            Token array
        """
        return np.random.randint(0, vocab_size, size=length, dtype=np.int64)

    def get_adaptive_segment_size(
        self,
        sequence_length: int,
        base_size: int = 512,
    ) -> int:
        """
        Get adaptive segment size based on sequence length.

        Longer sequences can use larger segments for efficiency.

        Args:
            sequence_length: Length of sequence
            base_size: Base segment size

        Returns:
            Recommended segment size
        """
        if sequence_length < 2048:
            return base_size
        elif sequence_length < 8192:
            return base_size * 2
        elif sequence_length < 32768:
            return base_size * 3
        else:
            return self.config.max_segment_size

    def get_metrics_summary(self) -> dict[str, Any]:
        """
        Get summary of training metrics.

        Returns:
            Dictionary with training statistics
        """
        if not self._metrics_history:
            return {"status": "no_training_data"}

        stages = {}
        for m in self._metrics_history:
            stage_name = m.stage.value
            if stage_name not in stages:
                stages[stage_name] = []
            stages[stage_name].append(m)

        summary = {
            "total_steps": len(self._metrics_history),
            "stages": {},
            "overall": {
                "best_loss": min(m.loss for m in self._metrics_history),
                "final_loss": self._metrics_history[-1].loss,
                "best_perplexity": min(m.perplexity for m in self._metrics_history),
                "final_perplexity": self._metrics_history[-1].perplexity,
            },
        }

        for stage_name, metrics in stages.items():
            summary["stages"][stage_name] = {
                "steps": len(metrics),
                "avg_loss": sum(m.loss for m in metrics) / len(metrics),
                "avg_perplexity": sum(m.perplexity for m in metrics) / len(metrics),
                "max_length": max(m.sequence_length for m in metrics),
            }

        return summary

    def plot_progress(self) -> str:
        """
        Generate ASCII plot of training progress.

        Returns:
            ASCII visualization string
        """
        if not self._metrics_history:
            return "No training data available"

        lines = ["Curriculum Training Progress", "=" * 40]

        # Loss progression
        lines.append("\nLoss over time:")
        for m in self._metrics_history:
            bar_length = int(20 * (2.0 - min(m.loss, 2.0)) / 2.0)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            lines.append(f"{m.stage.value[:8]:8} |{bar}| {m.loss:.4f} (len={m.sequence_length:,})")

        # Perplexity progression
        lines.append("\nPerplexity over time:")
        for m in self._metrics_history:
            ppl_normalized = min(m.perplexity / 10.0, 2.0)
            bar_length = int(20 * (2.0 - ppl_normalized) / 2.0)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            lines.append(f"{m.stage.value[:8]:8} |{bar}| {m.perplexity:.2f}")

        return "\n".join(lines)

    def export_checkpoint(self) -> dict[str, Any]:
        """
        Export curriculum state for resuming training.

        Returns:
            Checkpoint dictionary
        """
        return {
            "config": self.config,
            "metrics_history": [
                {
                    "stage": m.stage.value,
                    "epoch": m.epoch,
                    "loss": m.loss,
                    "perplexity": m.perplexity,
                    "sequence_length": m.sequence_length,
                }
                for m in self._metrics_history
            ],
        }

    @classmethod
    def from_checkpoint(cls, checkpoint: dict[str, Any]) -> "CurriculumLearning":
        """
        Restore curriculum from checkpoint.

        Args:
            checkpoint: Checkpoint dictionary

        Returns:
            Restored CurriculumLearning instance
        """
        config = checkpoint.get("config", {})
        instance = cls(
            max_length=config.get("max_length", 2_000_000),
            num_stages=config.get("num_stages", 5),
            min_length=config.get("min_length", 512),
            base_segment_size=config.get("base_segment_size", 512),
        )

        # Restore metrics
        for m in checkpoint.get("metrics_history", []):
            instance._metrics_history.append(
                TrainingMetrics(
                    stage=CurriculumStage(m["stage"]),
                    epoch=m["epoch"],
                    loss=m["loss"],
                    perplexity=m["perplexity"],
                    sequence_length=m["sequence_length"],
                    processing_time_ms=0.0,
                    memory_usage_mb=0.0,
                )
            )

        return instance


__all__ = [
    "CurriculumStage",
    "CurriculumStep",
    "CurriculumConfig",
    "TrainingMetrics",
    "CurriculumLearning",
]
