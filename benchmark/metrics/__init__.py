"""Benchmark metrics module.

Provides evaluation metrics for retrieval and ranking tasks:
- Recall@K, Precision@K
- NDCG@K (Normalized Discounted Cumulative Gain)
- MRR (Mean Reciprocal Rank)
- MAP (Mean Average Precision)
"""

from benchmark.metrics.performance import (
    measure_latency,
    measure_memory,
    measure_throughput,
)
from benchmark.metrics.ranking import (
    compute_map,
    compute_mrr,
    compute_ndcg_at_k,
)
from benchmark.metrics.retrieval import (
    compute_f1_at_k,
    compute_precision_at_k,
    compute_recall_at_k,
)

__all__ = [
    # Retrieval metrics
    "compute_recall_at_k",
    "compute_precision_at_k",
    "compute_f1_at_k",
    # Ranking metrics
    "compute_ndcg_at_k",
    "compute_mrr",
    "compute_map",
    # Performance metrics
    "measure_latency",
    "measure_throughput",
    "measure_memory",
]
