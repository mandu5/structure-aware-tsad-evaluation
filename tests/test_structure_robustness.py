"""Tests for the numpy-only statistics in src/evaluation/robustness.py.

These functions replace scipy equivalents so the artifact keeps a small
dependency set; the tests pin them against hand-computed values.
"""

from __future__ import annotations

import numpy as np

from src.evaluation import robustness as _MOD


def test_rankdata_without_ties() -> None:
    assert list(_MOD.rankdata(np.array([10.0, 30.0, 20.0]))) == [1.0, 3.0, 2.0]


def test_rankdata_averages_ties() -> None:
    # values 5,5 occupy ranks 1 and 2 -> both get 1.5
    assert list(_MOD.rankdata(np.array([5.0, 5.0, 9.0]))) == [1.5, 1.5, 3.0]
    # a three-way tie at the top occupies ranks 2,3,4 -> all get 3.0
    assert list(_MOD.rankdata(np.array([1.0, 7.0, 7.0, 7.0]))) == [1.0, 3.0, 3.0, 3.0]


def test_spearman_monotone_extremes() -> None:
    x = np.array([1.0, 2.0, 3.0, 4.0])
    assert abs(_MOD.spearman(x, 2 * x + 1) - 1.0) < 1e-12
    assert abs(_MOD.spearman(x, -x) + 1.0) < 1e-12


def test_spearman_matches_hand_computed_value() -> None:
    # No ties, so rho = 1 - 6*sum(d^2)/(n*(n^2-1)) with n=5.
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = np.array([2.0, 1.0, 4.0, 3.0, 5.0])
    expected = 1 - 6 * (1 + 1 + 1 + 1 + 0) / (5 * (25 - 1))
    assert abs(_MOD.spearman(x, y) - expected) < 1e-12


def test_spearman_constant_input_is_nan() -> None:
    assert np.isnan(_MOD.spearman(np.array([1.0, 1.0, 1.0]), np.array([1.0, 2.0, 3.0])))


def test_series_pairs_counts_flips_and_gaps() -> None:
    # A=(0.9,0.7) B=(0.5,0.2) C=(0.8,0.9)
    #   A,B: +0.4 / +0.5 -> agree
    #   A,C: +0.1 / -0.2 -> FLIP  (the flip sits on the smallest AUC gap)
    #   B,C: -0.3 / -0.7 -> agree
    auc = np.array([0.9, 0.5, 0.8])
    other = np.array([0.7, 0.2, 0.9])
    gap, flipped = _MOD.pairwise_flips(auc, other)
    assert len(gap) == 3
    assert flipped.sum() == 1
    assert abs(gap[flipped][0] - 0.1) < 1e-12
    assert sorted(round(g, 10) for g in gap.tolist()) == [0.1, 0.3, 0.4]


def test_series_pairs_drops_ties_on_either_metric() -> None:
    auc = np.array([0.5, 0.5, 0.7])
    other = np.array([0.1, 0.2, 0.2])
    gap, _ = _MOD.pairwise_flips(auc, other)
    # (0,1) tied on auc; (1,2) tied on other; only (0,2) survives.
    assert len(gap) == 1


def test_pairwise_flips_keeps_the_same_pairs_when_arguments_are_swapped() -> None:
    """The two-sided margin analysis depends on this.

    Swapping the arguments must return the margins of the other metric over the
    SAME pairs in the SAME order, so that a mask built from one call can index
    the flip vector from the other. Ties are excluded symmetrically, so this
    holds, but it is load-bearing enough to pin down.
    """
    rng = np.random.default_rng(3)
    for _ in range(20):
        a = rng.integers(0, 4, size=7).astype(float)  # small range -> many ties
        b = rng.integers(0, 4, size=7).astype(float)
        gap_ab, flip_ab = _MOD.pairwise_flips(a, b)
        gap_ba, flip_ba = _MOD.pairwise_flips(b, a)
        assert len(gap_ab) == len(gap_ba)
        assert np.array_equal(flip_ab, flip_ba)


def test_perm_pvalue_is_bounded_and_small_for_perfect_correlation() -> None:
    rng = np.random.default_rng(0)
    x = np.arange(12.0)
    p = _MOD.spearman_perm_p(x, x, 200, rng)
    assert 0.0 < p <= 1.0
    assert p < 0.05


def _retention(scores, clusters, n_boot=200, seed=0):
    return _MOD.rank_retention(
        np.asarray(scores, dtype=float), np.asarray(clusters), n_boot, np.random.default_rng(seed)
    )


def test_rank_retention_clean_separation_is_always_kept() -> None:
    scores = np.tile([3.0, 2.0, 1.0], (6, 1)) + np.random.default_rng(1).normal(0, 0.01, (6, 3))
    out = _retention(scores, list("aabbcc"))
    assert list(out["point_rank"]) == [1, 2, 3]
    assert list(out["retention"]) == [1.0, 1.0, 1.0]
    assert list(out["top1_freq"]) == [1.0, 0.0, 0.0]
    assert list(out["rank_lo"]) == [1.0, 2.0, 3.0]


def test_rank_retention_resamples_collections_not_series() -> None:
    # Model 0 wins in collection "a" only; model 1 wins in "b" and "c" and leads
    # overall (3.67 vs 3.0). Drawing "a" twice out of three collections makes
    # model 0 the leader, so the leader cannot be kept in every resample.
    scores = [[9.0, 1.0], [9.0, 1.0], [0.0, 5.0], [0.0, 5.0], [0.0, 5.0], [0.0, 5.0]]
    out = _retention(scores, list("aabbcc"), n_boot=2000)
    assert list(out["point_rank"]) == [2, 1]
    assert 0.0 < out["retention"][1] < 1.0
    # Only two models and no exact ties: the two rank-1 frequencies sum to 1.
    assert abs(out["top1_freq"].sum() - 1.0) < 1e-12
    # Series-level resampling would almost never flip this; collection-level
    # resampling flips whenever "a" is drawn at least twice, P = 7/27.
    assert abs(out["top1_freq"][0] - 7 / 27) < 0.03


def test_rank_retention_skips_missing_cells() -> None:
    scores = [[3.0, 1.0], [3.0, np.nan], [3.0, 1.0], [3.0, 1.0]]
    out = _retention(scores, list("abcd"))
    assert list(out["point_rank"]) == [1, 2]
    assert list(out["retention"]) == [1.0, 1.0]


def test_rank_retention_ties_share_a_rank() -> None:
    out = _retention([[1.0, 1.0, 0.0], [1.0, 1.0, 0.0]], list("ab"))
    assert list(out["point_rank"]) == [1, 1, 3]


def test_rank_retention_rejects_mismatched_clusters() -> None:
    import pytest

    with pytest.raises(ValueError):
        _retention([[1.0, 2.0]], list("ab"))
