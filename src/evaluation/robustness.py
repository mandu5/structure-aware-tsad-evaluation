"""Cluster-aware inference helpers for rank-flip analyses.

A pairwise rank-flip rate is uninterpretable on its own: it needs a null model
(what would random rankings give?), a tie treatment (are the flips just noise
between near-identical models?), and a cluster unit (are the evaluated series
independent, or do they share a source dataset collection?).

These helpers implement the statistics those checks need. They are numpy-only
so the artifact does not take a scipy dependency; permutation tests are used
instead of asymptotic p-values because the cluster-level tests here have very
small n (17 collections in the TSB-AD snapshot, 6 datasets in the TAB study).
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "rankdata",
    "spearman",
    "spearman_perm_p",
    "pairwise_flips",
    "flip_rate_null",
]


def rankdata(a: np.ndarray) -> np.ndarray:
    """Average ranks, matching ``scipy.stats.rankdata(method='average')``."""
    a = np.asarray(a, dtype=float)
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(len(a), dtype=float)
    ranks[order] = np.arange(1, len(a) + 1, dtype=float)
    sorted_a = a[order]
    i = 0
    while i < len(a):
        j = i
        while j + 1 < len(a) and sorted_a[j + 1] == sorted_a[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = ranks[order[i:j + 1]].mean()
        i = j + 1
    return ranks


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rho, computed as the Pearson correlation of average ranks."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3:
        return float("nan")
    rx, ry = rankdata(x[ok]), rankdata(y[ok])
    sx, sy = rx.std(), ry.std()
    if sx == 0 or sy == 0:
        return float("nan")
    return float(((rx - rx.mean()) * (ry - ry.mean())).mean() / (sx * sy))


def spearman_perm_p(x: np.ndarray, y: np.ndarray, n_perm: int, rng: np.random.Generator) -> float:
    """Two-sided permutation p-value for Spearman rho.

    Returns ``(count + 1) / (n_perm + 1)``, so the smallest attainable value is
    ``1 / (n_perm + 1)`` and should be reported as an upper bound, not as an
    exact p-value.
    """
    obs = spearman(x, y)
    if not np.isfinite(obs):
        return float("nan")
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    count = 0
    for _ in range(n_perm):
        if abs(spearman(x, rng.permutation(y))) >= abs(obs) - 1e-12:
            count += 1
    return float((count + 1) / (n_perm + 1))


def pairwise_flips(primary: np.ndarray, secondary: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Compare two metrics over all unordered model pairs within one group.

    Returns ``(primary_gap, flipped)`` over pairs that are non-tied on *both*
    metrics, where ``primary_gap`` is ``|primary_i - primary_j|`` and
    ``flipped`` marks pairs the two metrics order differently.
    """
    primary = np.asarray(primary, dtype=float)
    secondary = np.asarray(secondary, dtype=float)
    n = len(primary)
    if n < 2:
        return np.empty(0), np.empty(0, dtype=bool)
    i, j = np.triu_indices(n, k=1)
    dp = primary[i] - primary[j]
    ds = secondary[i] - secondary[j]
    keep = (dp != 0) & (ds != 0)
    return np.abs(dp[keep]), (np.sign(dp[keep]) != np.sign(ds[keep]))


def flip_rate_null(
    groups: list[tuple[np.ndarray, np.ndarray]],
    n_perm: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Random-ranking null for the pooled pairwise flip rate.

    Permutes the secondary metric across models *within* each group, which
    destroys any association with the primary metric while preserving both
    marginal distributions and the group sizes. For independent rankings the
    expected flip rate is 0.5.
    """
    out = np.empty(n_perm)
    for b in range(n_perm):
        flips = total = 0
        for primary, secondary in groups:
            _, flipped = pairwise_flips(primary, rng.permutation(secondary))
            flips += int(flipped.sum())
            total += int(flipped.size)
        out[b] = flips / total if total else np.nan
    return out
