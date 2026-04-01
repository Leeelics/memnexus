"""Ranking metrics for evaluating result ordering quality.

Metrics:
    - NDCG@K: Normalized Discounted Cumulative Gain
    - MRR: Mean Reciprocal Rank
    - MAP: Mean Average Precision

Example:
    >>> expected = [{"id": "a", "relevance": 1.0}, {"id": "b", "relevance": 0.5}]
    >>> retrieved = ["a", "c", "b"]
    >>> ndcg = compute_ndcg_at_k(expected, retrieved, k=3)
    >>> print(f"NDCG@3: {ndcg:.4f}")
"""

import math
from typing import Any


def compute_dcg(relevances: list[float]) -> float:
    """Compute Discounted Cumulative Gain.

    DCG = sum(rel_i / log2(i + 2)) for i in range(len(relevances))

    Args:
        relevances: List of relevance scores at each rank

    Returns:
        DCG score
    """
    dcg = 0.0
    for i, rel in enumerate(relevances):
        # i starts from 0, but rank starts from 1, so use i + 2 for log2
        dcg += rel / math.log2(i + 2)
    return dcg


def compute_ndcg_at_k(
    expected: list[dict[str, Any]],
    retrieved: list[str],
    k: int,
) -> float:
    """Compute NDCG@K (Normalized Discounted Cumulative Gain).

    NDCG@K = DCG@K / IDCG@K

    where IDCG is the ideal DCG (perfect ranking).

    Args:
        expected: List of expected items with relevance scores
        retrieved: List of retrieved item IDs (ordered by rank)
        k: Number of top results to consider

    Returns:
        NDCG@K score between 0 and 1
    """
    if not expected or not retrieved or k <= 0:
        return 0.0

    # Build relevance lookup from expected items
    relevance_map = {item["id"]: item.get("relevance", 1.0) for item in expected}

    # Get relevance scores for retrieved items
    retrieved_relevances = [relevance_map.get(item_id, 0.0) for item_id in retrieved[:k]]

    # Compute DCG
    dcg = compute_dcg(retrieved_relevances)

    # Compute IDCG (ideal DCG)
    ideal_relevances = sorted(relevance_map.values(), reverse=True)[:k]
    idcg = compute_dcg(ideal_relevances)

    if idcg == 0:
        return 0.0

    return dcg / idcg


def compute_mrr(
    expected: list[dict[str, Any]],
    retrieved: list[str],
    relevance_threshold: float = 0.5,
) -> float:
    """Compute MRR (Mean Reciprocal Rank).

    MRR = (1 / |Q|) * sum(1 / rank_q) for each query q

    where rank_q is the position of the first relevant result.

    Args:
        expected: List of expected items with relevance scores
        retrieved: List of retrieved item IDs (ordered by rank)
        relevance_threshold: Minimum relevance score to consider an item relevant

    Returns:
        MRR score between 0 and 1
    """
    if not expected or not retrieved:
        return 0.0

    # Get relevant items
    relevant_items = {
        item["id"] for item in expected if item.get("relevance", 1.0) >= relevance_threshold
    }

    if not relevant_items:
        return 0.0

    # Find rank of first relevant item
    for rank, item_id in enumerate(retrieved, start=1):
        if item_id in relevant_items:
            return 1.0 / rank

    return 0.0


def compute_ap(
    expected: list[dict[str, Any]],
    retrieved: list[str],
    relevance_threshold: float = 0.5,
) -> float:
    """Compute AP (Average Precision) for a single query.

    AP = sum(Precision@k * rel(k)) / |relevant documents|

    Args:
        expected: List of expected items with relevance scores
        retrieved: List of retrieved item IDs (ordered by rank)
        relevance_threshold: Minimum relevance score to consider an item relevant

    Returns:
        AP score between 0 and 1
    """
    if not expected or not retrieved:
        return 0.0

    # Get relevant items
    relevant_items = {
        item["id"] for item in expected if item.get("relevance", 1.0) >= relevance_threshold
    }

    if not relevant_items:
        return 0.0

    # Compute precision at each rank where a relevant item is found
    precisions = []
    relevant_found = 0

    for k, item_id in enumerate(retrieved, start=1):
        if item_id in relevant_items:
            relevant_found += 1
            precision_at_k = relevant_found / k
            precisions.append(precision_at_k)

    if not precisions:
        return 0.0

    return sum(precisions) / len(relevant_items)


def compute_map(
    queries: list[tuple[list[dict[str, Any]], list[str]]],
    relevance_threshold: float = 0.5,
) -> float:
    """Compute MAP (Mean Average Precision) across multiple queries.

    MAP = mean(AP(q)) for all queries q

    Args:
        queries: List of (expected, retrieved) tuples
        relevance_threshold: Minimum relevance score to consider an item relevant

    Returns:
        MAP score between 0 and 1
    """
    if not queries:
        return 0.0

    aps = [compute_ap(expected, retrieved, relevance_threshold) for expected, retrieved in queries]

    return sum(aps) / len(aps)


def compute_ranking_metrics(
    expected: list[dict[str, Any]],
    retrieved: list[str],
    k_values: list[int] = None,
    relevance_threshold: float = 0.5,
) -> dict[str, float]:
    """Compute all ranking metrics.

    Args:
        expected: List of expected items with relevance scores
        retrieved: List of retrieved item IDs (ordered by rank)
        k_values: List of K values to compute NDCG for (default: [1, 3, 5, 10])
        relevance_threshold: Minimum relevance score to consider an item relevant

    Returns:
        Dictionary mapping metric names to values
    """
    if k_values is None:
        k_values = [1, 3, 5, 10]

    results = {
        "mrr": compute_mrr(expected, retrieved, relevance_threshold),
        "ap": compute_ap(expected, retrieved, relevance_threshold),
    }

    for k in k_values:
        results[f"ndcg@{k}"] = compute_ndcg_at_k(expected, retrieved, k)

    return results
