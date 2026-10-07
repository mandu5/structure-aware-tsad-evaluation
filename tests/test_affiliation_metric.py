from __future__ import annotations

import numpy as np

from src.evaluation.affiliation import compute_affiliation_f1, threshold_by_rate


def test_threshold_by_rate_marks_top_quantile_as_anomalous() -> None:
    scores = np.array([0.1, 0.2, 0.3, 0.9, 1.0], dtype=float)
    labels = np.array([0, 0, 0, 1, 1], dtype=int)

    preds = threshold_by_rate(scores, labels)

    assert preds.tolist() == [0, 0, 0, 1, 1]


def test_compute_affiliation_f1_rewards_exact_segment_match() -> None:
    labels = np.array([0, 0, 1, 1, 1, 0, 0], dtype=int)
    preds = np.array([0, 0, 1, 1, 1, 0, 0], dtype=int)

    score = compute_affiliation_f1(labels, preds)

    assert score == 1.0


def test_compute_affiliation_f1_penalizes_fragmentation() -> None:
    labels = np.array([0, 0, 1, 1, 1, 1, 0, 0], dtype=int)
    preds = np.array([0, 0, 1, 0, 1, 0, 0, 0], dtype=int)

    score = compute_affiliation_f1(labels, preds)

    assert 0.0 <= score < 1.0
