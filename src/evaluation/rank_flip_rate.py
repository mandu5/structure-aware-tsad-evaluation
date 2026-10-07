"""Rank Flip Rate (RFR): pairwise ordering consistency between two metrics.

Used in the paper as a single, reviewer-friendly definition of metric-induced
ranking instability *within each dataset* (same set of models compared under
two scalar scores).
"""

from __future__ import annotations

import math
from typing import Any


def _finite(x: Any) -> bool:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return False
    return math.isfinite(v)


def compute_rank_flip_rate_by_dataset(
    rows: list[dict[str, Any]],
    *,
    metric_a: str = "auc_roc",
    metric_b: str = "aff_f1",
    dataset_key: str = "dataset",
    model_key: str = "model",
) -> dict[str, Any]:
    """Compute RFR per dataset.

    Definition (paper):
        RFR = (# of unordered model pairs whose relative ordering differs between
        metric_a and metric_b) / (# of comparable pairs).

    Comparable pair rule:
        Include unordered pairs (m1, m2) only if both metrics are finite and
        **strict** on both sides: metric_a(m1) != metric_a(m2) and
        metric_b(m1) != metric_b(m2). Pairs involving any tie on either metric
        are excluded from the denominator (and numerator).
    """
    by_ds: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        ds = str(r[dataset_key])
        by_ds.setdefault(ds, []).append(r)

    per_ds: dict[str, Any] = {}
    rfr_values: list[float] = []

    for ds, rs in sorted(by_ds.items()):
        ms = [r for r in rs if _finite(r.get(metric_a)) and _finite(r.get(metric_b))]
        n_flips = 0
        n_comp = 0
        for i in range(len(ms)):
            for j in range(i + 1, len(ms)):
                a_i = float(ms[i][metric_a])
                a_j = float(ms[j][metric_a])
                b_i = float(ms[i][metric_b])
                b_j = float(ms[j][metric_b])
                if a_i == a_j or b_i == b_j:
                    continue
                n_comp += 1
                sign_a = 1 if a_i > a_j else -1
                sign_b = 1 if b_i > b_j else -1
                if sign_a != sign_b:
                    n_flips += 1
        rfr = (n_flips / n_comp) if n_comp > 0 else float("nan")
        per_ds[ds] = {
            "n_models_with_both_metrics": len(ms),
            "n_comparable_pairs": n_comp,
            "n_flips": n_flips,
            "rfr": rfr,
        }
        if not math.isnan(rfr):
            rfr_values.append(rfr)

    mean_rfr = sum(rfr_values) / len(rfr_values) if rfr_values else float("nan")

    return {
        "definition": (
            "RFR = (# unordered model pairs with opposite strict ordering between "
            f"{metric_a} and {metric_b}) / (# comparable pairs). "
            "Comparable pairs exclude ties on either metric."
        ),
        "metric_a": metric_a,
        "metric_b": metric_b,
        "by_dataset": per_ds,
        "mean_rfr_over_datasets_with_pairs": mean_rfr,
    }
