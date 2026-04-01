"""Benchmark datasets module.

Provides synthetic and real-world datasets for benchmarking:
- Synthetic repositories with known ground truth
- Real open-source repositories with human annotations
"""

from benchmark.datasets.loader import DatasetLoader
from benchmark.datasets.synthetic import (
    CodeBenchmarkDataset,
    GitBenchmarkDataset,
    SyntheticRepoGenerator,
)

__all__ = [
    "SyntheticRepoGenerator",
    "GitBenchmarkDataset",
    "CodeBenchmarkDataset",
    "DatasetLoader",
]
