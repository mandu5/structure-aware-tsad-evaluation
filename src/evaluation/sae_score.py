"""Structure-Aware Evaluation Score (SAEScore).

SAEScore combines point-level and segment-level metrics with a
dataset-dependent weight alpha derived from anomaly structure.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


def _finite_metric(x: Any) -> bool:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return False
    return math.isfinite(v)


@dataclass(frozen=True)
class SAEScoreResult:
    """Container for SAEScore computation outputs."""

    score: float
    alpha: float
    point_metric: float
    segment_metric: float


def compute_alpha_from_short_ratio(short_ratio: float) -> float:
    """Compute structure weight alpha = 1 - short_ratio, clipped to [0, 1]."""
    return max(0.0, min(1.0, 1.0 - float(short_ratio)))


def compute_alpha_from_counts(n_short: int, n_total: int) -> float:
    """Compute alpha from anomaly-type counts."""
    if n_total <= 0:
        return 1.0
    return compute_alpha_from_short_ratio(float(n_short) / float(n_total))


def compute_sae_score(
    point_metric: float,
    segment_metric: float,
    alpha: float,
) -> SAEScoreResult:
    """Compute SAEScore from point/segment metrics and structure weight."""
    a = max(0.0, min(1.0, float(alpha)))
    p = float(point_metric)
    s = float(segment_metric)
    score = (1.0 - a) * p + a * s
    return SAEScoreResult(score=score, alpha=a, point_metric=p, segment_metric=s)


def compute_dataset_alpha_from_taxonomy_summary(summary: dict[str, int]) -> float:
    """Compute alpha from taxonomy summary dict.

    Expected keys: {'Short': int, 'Medium': int, 'Long': int}
    Missing keys default to zero.
    """
    n_short = int(summary.get("Short", 0))
    n_total = (
        int(summary.get("Short", 0))
        + int(summary.get("Medium", 0))
        + int(summary.get("Long", 0))
    )
    return compute_alpha_from_counts(n_short=n_short, n_total=n_total)


def rank_by_metric(
    rows: list[dict[str, Any]],
    metric_key: str,
    *,
    model_key: str = "model",
    dataset_key: str = "dataset",
    reverse: bool = True,
) -> dict[tuple[str, str], int]:
    """Assign dense 1-based ranks by sorting rows on ``metric_key``.

    Ties are broken by Python's stable sort (input order). Rows must include
    ``model_key`` and ``dataset_key`` for each entry.
    """
    if not rows:
        return {}
    ordered = sorted(rows, key=lambda r: float(r[metric_key]), reverse=reverse)
    return {
        (str(r[model_key]), str(r[dataset_key])): i + 1
        for i, r in enumerate(ordered)
    }


def rank_by_metric_global_skip_missing(
    rows: list[dict[str, Any]],
    metric_key: str,
    *,
    model_key: str = "model",
    dataset_key: str = "dataset",
    reverse: bool = True,
) -> dict[tuple[str, str], int | None]:
    """Dense ranks over all rows with finite ``metric_key`` (global leaderboard).

    Rows missing or non-finite ``metric_key`` receive ``None`` (no rank).
    """
    if not rows:
        return {}
    viable = [r for r in rows if _finite_metric(r.get(metric_key))]
    ordered = sorted(viable, key=lambda r: float(r[metric_key]), reverse=reverse)
    rank_map = {
        (str(r[model_key]), str(r[dataset_key])): i + 1
        for i, r in enumerate(ordered)
    }
    out: dict[tuple[str, str], int | None] = {}
    for r in rows:
        k = (str(r[model_key]), str(r[dataset_key]))
        out[k] = rank_map.get(k)
    return out


def rank_by_metric_per_dataset_skip_missing(
    rows: list[dict[str, Any]],
    metric_key: str,
    *,
    model_key: str = "model",
    dataset_key: str = "dataset",
    reverse: bool = True,
) -> dict[tuple[str, str], int | None]:
    """Dense ranks within each dataset for rows with finite ``metric_key``."""
    if not rows:
        return {}
    by_ds: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        by_ds.setdefault(str(r[dataset_key]), []).append(r)
    rank_map: dict[tuple[str, str], int] = {}
    for rs in by_ds.values():
        viable = [r for r in rs if _finite_metric(r.get(metric_key))]
        ordered = sorted(viable, key=lambda r: float(r[metric_key]), reverse=reverse)
        for i, r in enumerate(ordered):
            rank_map[(str(r[model_key]), str(r[dataset_key]))] = i + 1
    out: dict[tuple[str, str], int | None] = {}
    for r in rows:
        k = (str(r[model_key]), str(r[dataset_key]))
        out[k] = rank_map.get(k)
    return out

