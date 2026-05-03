"""Evaluation modules for anomaly detection research and production."""

from src.evaluation.metrics import evaluate
try:
    # prts is an optional dependency for affiliation-based metrics.
    from src.evaluation.affiliation import compute_affiliation_f1, threshold_by_rate
except ModuleNotFoundError:  # pragma: no cover
    def compute_affiliation_f1(*args, **kwargs):  # type: ignore[no-redef]
        raise ModuleNotFoundError(
            "prts is required for compute_affiliation_f1. Install it (e.g., `python3 -m pip install prts`)."
        )

    def threshold_by_rate(*args, **kwargs):  # type: ignore[no-redef]
        raise ModuleNotFoundError(
            "prts is required for threshold_by_rate (and affiliation metrics). Install it (e.g., `python3 -m pip install prts`)."
        )
from src.evaluation.sae_score import (
    SAEScoreResult,
    compute_alpha_from_counts,
    compute_alpha_from_short_ratio,
    compute_dataset_alpha_from_taxonomy_summary,
    compute_sae_score,
    rank_by_metric,
)
from src.evaluation.saps import SAPSConfig, apply_saps, suggest_saps_config_from_lengths

__all__ = [
    "evaluate",
    # Optional exports (may be None if prts is not installed).
    "compute_affiliation_f1",
    "threshold_by_rate",
    "SAEScoreResult",
    "compute_alpha_from_counts",
    "compute_alpha_from_short_ratio",
    "compute_dataset_alpha_from_taxonomy_summary",
    "compute_sae_score",
    "rank_by_metric",
    "SAPSConfig",
    "apply_saps",
    "suggest_saps_config_from_lengths",
]
