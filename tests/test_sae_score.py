"""Unit tests for Structure-Aware Evaluation Score (SAEScore)."""

from src.evaluation.sae_score import (
    compute_alpha_from_counts,
    compute_alpha_from_short_ratio,
    compute_dataset_alpha_from_taxonomy_summary,
    compute_sae_score,
    rank_by_metric,
)


def test_alpha_from_short_ratio_bounds() -> None:
    assert compute_alpha_from_short_ratio(0.0) == 1.0
    assert compute_alpha_from_short_ratio(1.0) == 0.0
    assert compute_alpha_from_short_ratio(-1.0) == 1.0
    assert compute_alpha_from_short_ratio(2.0) == 0.0


def test_alpha_from_counts() -> None:
    assert compute_alpha_from_counts(n_short=0, n_total=100) == 1.0
    assert compute_alpha_from_counts(n_short=20, n_total=100) == 0.8
    assert compute_alpha_from_counts(n_short=0, n_total=0) == 1.0


def test_sae_score_weighting() -> None:
    result = compute_sae_score(point_metric=0.8, segment_metric=0.2, alpha=0.75)
    assert abs(result.score - 0.35) < 1e-9
    assert result.alpha == 0.75


def test_alpha_from_taxonomy_summary() -> None:
    alpha = compute_dataset_alpha_from_taxonomy_summary(
        {"Short": 0, "Medium": 7, "Long": 29}
    )
    assert alpha == 1.0


def test_rank_by_metric_order_and_reversal() -> None:
    rows = [
        {"model": "A", "dataset": "X", "score": 0.9},
        {"model": "B", "dataset": "X", "score": 0.5},
        {"model": "C", "dataset": "Y", "score": 0.7},
    ]
    r = rank_by_metric(rows, "score", model_key="model", dataset_key="dataset")
    assert r[("A", "X")] == 1
    assert r[("C", "Y")] == 2
    assert r[("B", "X")] == 3
    assert abs(r[("A", "X")] - r[("B", "X")]) == 2


def test_rank_by_metric_empty() -> None:
    assert rank_by_metric([], "x") == {}


def test_psm_style_alpha_from_taxonomy() -> None:
    """PSM (eBay): 37 short / 72 segments => alpha ≈ 0.486."""
    alpha = compute_dataset_alpha_from_taxonomy_summary(
        {"Short": 37, "Medium": 16, "Long": 19}
    )
    assert abs(alpha - (1.0 - 37.0 / 72.0)) < 1e-9


def test_alpha_half_blends_point_and_segment() -> None:
    """At alpha=0.5, SAEScore lies strictly between AUC-ROC and Aff-F1 (when they differ)."""
    hi_auc = compute_sae_score(0.9, 0.1, alpha=0.5).score
    hi_aff = compute_sae_score(0.3, 0.9, alpha=0.5).score
    assert hi_aff > hi_auc
    assert abs(hi_aff - (0.5 * 0.3 + 0.5 * 0.9)) < 1e-9

