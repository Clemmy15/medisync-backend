"""Ranking evaluation utilities — NDCG@10, Hit Rate, Diversity."""

from __future__ import annotations

import math
from collections import Counter


def dcg_at_k(relevances: list[float], k: int) -> float:
    return sum(
        rel / math.log2(i + 2) for i, rel in enumerate(relevances[:k])
    )


def ndcg_at_k(relevances: list[float], k: int = 10) -> float:
    if not relevances:
        return 0.0
    actual = dcg_at_k(relevances, k)
    ideal = dcg_at_k(sorted(relevances, reverse=True), k)
    if ideal <= 0:
        return 0.0
    return round(actual / ideal, 4)


def hit_rate(relevances: list[float], threshold: float = 0.5) -> float:
    if not relevances:
        return 0.0
    hits = sum(1 for r in relevances if r >= threshold)
    return round(hits / len(relevances), 4)


def recommendation_diversity(categories: list[str]) -> float:
    """1 - normalized Herfindahl index (higher = more diverse)."""
    if not categories:
        return 0.0
    counts = Counter(categories)
    n = len(categories)
    hhi = sum((c / n) ** 2 for c in counts.values())
    unique_ratio = len(counts) / n
    return round(0.5 * (1 - hhi) + 0.5 * unique_ratio, 4)


def build_ranking_metrics(
    ranked_items: list[dict],
    *,
    k: int = 10,
    relevance_threshold: float = 0.5,
) -> dict:
    relevances = [float(i.get("confidence", 0)) for i in ranked_items]
    categories = [str(i.get("category", "")) for i in ranked_items]
    return {
        "ndcg_at_10": ndcg_at_k(relevances, k),
        "hit_rate": hit_rate(relevances, relevance_threshold),
        "recommendation_diversity": recommendation_diversity(categories),
        "item_count": len(ranked_items),
    }
