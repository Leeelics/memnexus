"""Retrieval metrics for evaluating search quality.

Metrics:
    - Recall@K: Proportion of relevant items retrieved in top K
    - Precision@K: Proportion of top K items that are relevant
    - F1@K: Harmonic mean of Precision and Recall

Example:
    >>> expected = [{"id": "a", "relevance": 1.0}, {"id": "b", "relevance": 0.5}]
    >>> retrieved = ["a", "c", "b"]
    >>> recall = compute_recall_at_k(expected, retrieved, k=3)
    >>> print(f"Recall@3: {recall:.4f}")
"""

from typing import Any


def compute_recall_at_k(
    expected: list[dict[str, Any]],
    retrieved: list[str],
    k: int,
    relevance_threshold: float = 0.5,
) -> float:
    """Compute Recall@K metric.

    Recall@K = (number of relevant items in top K) / (total number of relevant items)

    Args:
        expected: List of expected items with relevance scores
        retrieved: List of retrieved item IDs (ordered by rank)
        k: Number of top results to consider
        relevance_threshold: Minimum relevance score to consider an item relevant

    Returns:
        Recall@K score between 0 and 1
    """
    if not expected:
        return 0.0

    # Get relevant expected items
    relevant_items = {
        item["id"] for item in expected if item.get("relevance", 1.0) >= relevance_threshold
    }

    if not relevant_items:
        return 0.0

    # Count relevant items in top K
    retrieved_k = set(retrieved[:k])
    relevant_in_k = len(relevant_items & retrieved_k)

    return relevant_in_k / len(relevant_items)


def compute_precision_at_k(
    expected: list[dict[str, Any]],
    retrieved: list[str],
    k: int,
    relevance_threshold: float = 0.5,
) -> float:
    """Compute Precision@K metric.

    Precision@K = (number of relevant items in top K) / K

    Args:
        expected: List of expected items with relevance scores
        retrieved: List of retrieved item IDs (ordered by rank)
        k: Number of top results to consider
        relevance_threshold: Minimum relevance score to consider an item relevant

    Returns:
        Precision@K score between 0 and 1
    """
    if k <= 0 or not retrieved:
        return 0.0

    # Get relevant expected items
    relevant_items = {
        item["id"] for item in expected if item.get("relevance", 1.0) >= relevance_threshold
    }

    # Count relevant items in top K
    retrieved_k = retrieved[:k]
    if not retrieved_k:
        return 0.0

    relevant_in_k = sum(1 for item in retrieved_k if item in relevant_items)

    return relevant_in_k / len(retrieved_k)


def compute_f1_at_k(
    expected: list[dict[str, Any]],
    retrieved: list[str],
    k: int,
    relevance_threshold: float = 0.5,
) -> float:
    """Compute F1@K metric (harmonic mean of Precision and Recall).

    F1@K = 2 * (Precision@K * Recall@K) / (Precision@K + Recall@K)

    Args:
        expected: List of expected items with relevance scores
        retrieved: List of retrieved item IDs (ordered by rank)
        k: Number of top results to consider
        relevance_threshold: Minimum relevance score to consider an item relevant

    Returns:
        F1@K score between 0 and 1
    """
    precision = compute_precision_at_k(expected, retrieved, k, relevance_threshold)
    recall = compute_recall_at_k(expected, retrieved, k, relevance_threshold)

    if precision + recall == 0:
        return 0.0

    return 2 * (precision * recall) / (precision + recall)


def compute_metrics_at_k(
    expected: list[dict[str, Any]],
    retrieved: list[str],
    k_values: list[int] = None,
    relevance_threshold: float = 0.5,
) -> dict[str, float]:
    """Compute all retrieval metrics at multiple K values.

    Args:
        expected: List of expected items with relevance scores
        retrieved: List of retrieved item IDs (ordered by rank)
        k_values: List of K values to compute metrics for (default: [1, 3, 5, 10])
        relevance_threshold: Minimum relevance score to consider an item relevant

    Returns:
        Dictionary mapping metric names to values
    """
    if k_values is None:
        k_values = [1, 3, 5, 10]

    results = {}
    for k in k_values:
        results[f"recall@{k}"] = compute_recall_at_k(expected, retrieved, k, relevance_threshold)
        results[f"precision@{k}"] = compute_precision_at_k(
            expected, retrieved, k, relevance_threshold
        )
        results[f"f1@{k}"] = compute_f1_at_k(expected, retrieved, k, relevance_threshold)

    return results
