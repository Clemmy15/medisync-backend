from app.evaluation.metrics import (
    hit_rate,
    ndcg_at_k,
    recommendation_diversity,
)


def test_ndcg_perfect_ranking() -> None:
    assert ndcg_at_k([1.0, 0.9, 0.8], 10) == 1.0


def test_hit_rate() -> None:
    assert hit_rate([0.9, 0.3, 0.6], threshold=0.5) == round(2 / 3, 4)


def test_diversity_single_category() -> None:
    assert recommendation_diversity(["a", "a", "a"]) < recommendation_diversity(
        ["a", "b", "c"]
    )
