"""Tests for the numpy-only statistics used by compute_structure_robustness.py.

These functions replace scipy equivalents so the artifact keeps a small
dependency set; the tests pin them against hand-computed values.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

_SPEC = importlib.util.spec_from_file_location(
    "compute_structure_robustness",
    Path(__file__).resolve().parents[1] / "scripts" / "compute_structure_robustness.py",
)
_MOD = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_MOD)


def test_rankdata_without_ties() -> None:
    assert list(_MOD._rankdata(np.array([10.0, 30.0, 20.0]))) == [1.0, 3.0, 2.0]


def test_rankdata_averages_ties() -> None:
    # values 5,5 occupy ranks 1 and 2 -> both get 1.5
    assert list(_MOD._rankdata(np.array([5.0, 5.0, 9.0]))) == [1.5, 1.5, 3.0]
    # a three-way tie at the top occupies ranks 2,3,4 -> all get 3.0
    assert list(_MOD._rankdata(np.array([1.0, 7.0, 7.0, 7.0]))) == [1.0, 3.0, 3.0, 3.0]


def test_spearman_monotone_extremes() -> None:
    x = np.array([1.0, 2.0, 3.0, 4.0])
    assert abs(_MOD._spearman(x, 2 * x + 1) - 1.0) < 1e-12
    assert abs(_MOD._spearman(x, -x) + 1.0) < 1e-12


def test_spearman_matches_hand_computed_value() -> None:
    # No ties, so rho = 1 - 6*sum(d^2)/(n*(n^2-1)) with n=5.
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = np.array([2.0, 1.0, 4.0, 3.0, 5.0])
    expected = 1 - 6 * (1 + 1 + 1 + 1 + 0) / (5 * (25 - 1))
    assert abs(_MOD._spearman(x, y) - expected) < 1e-12


def test_spearman_constant_input_is_nan() -> None:
    assert np.isnan(_MOD._spearman(np.array([1.0, 1.0, 1.0]), np.array([1.0, 2.0, 3.0])))


def test_series_pairs_counts_flips_and_gaps() -> None:
    # A=(0.9,0.7) B=(0.5,0.2) C=(0.8,0.9)
    #   A,B: +0.4 / +0.5 -> agree
    #   A,C: +0.1 / -0.2 -> FLIP  (the flip sits on the smallest AUC gap)
    #   B,C: -0.3 / -0.7 -> agree
    auc = np.array([0.9, 0.5, 0.8])
    other = np.array([0.7, 0.2, 0.9])
    gap, flipped = _MOD._series_pairs(auc, other)
    assert len(gap) == 3
    assert flipped.sum() == 1
    assert abs(gap[flipped][0] - 0.1) < 1e-12
    assert sorted(round(g, 10) for g in gap.tolist()) == [0.1, 0.3, 0.4]


def test_series_pairs_drops_ties_on_either_metric() -> None:
    auc = np.array([0.5, 0.5, 0.7])
    other = np.array([0.1, 0.2, 0.2])
    gap, _ = _MOD._series_pairs(auc, other)
    # (0,1) tied on auc; (1,2) tied on other; only (0,2) survives.
    assert len(gap) == 1


def test_perm_pvalue_is_bounded_and_small_for_perfect_correlation() -> None:
    rng = np.random.default_rng(0)
    x = np.arange(12.0)
    p = _MOD._spearman_perm_p(x, x, 200, rng)
    assert 0.0 < p <= 1.0
    assert p < 0.05
