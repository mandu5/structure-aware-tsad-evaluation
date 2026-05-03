"""Helpers for affiliation-based time-series evaluation."""

from __future__ import annotations

import numpy as np
from prts import ts_precision, ts_recall


def threshold_by_rate(scores: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """Threshold scores using the ground-truth anomaly rate."""
    scores_arr = np.asarray(scores, dtype=float).reshape(-1)
    labels_arr = np.asarray(labels, dtype=int).reshape(-1)
    rate = float(np.clip(labels_arr.mean(), 1e-6, 1 - 1e-6))
    threshold = float(np.quantile(scores_arr, 1.0 - rate))
    return (scores_arr >= threshold).astype(np.int32)


def _to_events(values: list[int]) -> list[tuple[int, int]]:
    events: list[tuple[int, int]] = []
    active = False
    start = 0
    for idx, value in enumerate(values):
        if value and not active:
            start, active = idx, True
        elif not value and active:
            events.append((start, idx))
            active = False
    if active:
        events.append((start, len(values)))
    return events


def compute_affiliation_f1(labels: np.ndarray, preds: np.ndarray) -> float:
    """Compute Affiliation-F1 with compatibility across prts versions."""
    labels_list = np.asarray(labels, dtype=int).reshape(-1).tolist()
    preds_list = np.asarray(preds, dtype=int).reshape(-1).tolist()
    try:
        precision = ts_precision(preds_list, labels_list, cardinality="one", bias="flat")
        recall = ts_recall(preds_list, labels_list, cardinality="one", bias="flat")
    except TypeError:
        pred_events = _to_events(preds_list)
        true_events = _to_events(labels_list)
        if not pred_events or not true_events:
            return 0.0
        time_range = (0, len(labels_list))
        precision = ts_precision(pred_events, true_events, time_range)
        recall = ts_recall(pred_events, true_events, time_range)

    if precision + recall == 0:
        return 0.0
    return float(2 * precision * recall / (precision + recall))
