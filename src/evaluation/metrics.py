"""Evaluation utilities for anomaly detection models."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray,
) -> dict[str, float]:
    """Compute the standard set of binary classification metrics.

    F1 is the primary metric for this project due to severe class imbalance
    in the SECOM dataset.  Accuracy is intentionally omitted.

    Args:
        y_true: Ground-truth binary labels of shape ``(n_samples,)``.
        y_pred: Predicted binary labels of shape ``(n_samples,)``.
        y_proba: Predicted anomaly probabilities of shape ``(n_samples,)``.

    Returns:
        Dictionary with keys ``f1``, ``roc_auc``, ``precision``, ``recall``,
        and ``avg_precision``.
    """
    return {
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_proba)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "avg_precision": float(average_precision_score(y_true, y_proba)),
    }
