"""Tests for Rank Flip Rate (RFR) definition."""

from src.evaluation.rank_flip_rate import compute_rank_flip_rate_by_dataset


def test_rfr_perfect_agreement_zero() -> None:
    rows = [
        {"model": "A", "dataset": "X", "auc_roc": 0.9, "aff_f1": 0.8},
        {"model": "B", "dataset": "X", "auc_roc": 0.5, "aff_f1": 0.5},
    ]
    out = compute_rank_flip_rate_by_dataset(rows)
    assert out["by_dataset"]["X"]["n_comparable_pairs"] == 1
    assert out["by_dataset"]["X"]["n_flips"] == 0
    assert out["by_dataset"]["X"]["rfr"] == 0.0


def test_rfr_one_flip() -> None:
    rows = [
        {"model": "A", "dataset": "X", "auc_roc": 0.9, "aff_f1": 0.3},
        {"model": "B", "dataset": "X", "auc_roc": 0.5, "aff_f1": 0.8},
    ]
    out = compute_rank_flip_rate_by_dataset(rows)
    assert out["by_dataset"]["X"]["n_flips"] == 1
    assert out["by_dataset"]["X"]["rfr"] == 1.0


def test_rfr_ties_excluded() -> None:
    rows = [
        {"model": "A", "dataset": "X", "auc_roc": 0.5, "aff_f1": 0.8},
        {"model": "B", "dataset": "X", "auc_roc": 0.5, "aff_f1": 0.5},
    ]
    out = compute_rank_flip_rate_by_dataset(rows)
    assert out["by_dataset"]["X"]["n_comparable_pairs"] == 0
