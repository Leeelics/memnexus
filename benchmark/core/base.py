"""Base classes for benchmark framework."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class Dataset:
    """Benchmark dataset container."""

    name: str
    queries: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.queries)


@dataclass
class BenchmarkResult:
    """Result of a benchmark task."""

    task_name: str
    metrics: dict[str, float]
    raw_results: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_name": self.task_name,
            "metrics": self.metrics,
            "raw_results": self.raw_results,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "duration_seconds": self.duration_seconds,
        }


class BenchmarkTask[T](ABC):
    """Base class for benchmark tasks."""

    def __init__(self, name: str, config: dict[str, Any] | None = None):
        self.name = name
        self.config = config or {}
        self._setup_done = False

    @abstractmethod
    def setup(self) -> None:
        """Setup the task (load data, init models, etc.)."""
        pass

    @abstractmethod
    async def run(self, dataset: Dataset | None = None) -> BenchmarkResult:
        """Run the benchmark task."""
        pass

    @abstractmethod
    def teardown(self) -> None:
        """Cleanup resources."""
        pass

    def ensure_setup(self) -> None:
        """Ensure setup has been called."""
        if not self._setup_done:
            self.setup()
            self._setup_done = True
