"""Evaluation modules for anomaly detection research and production."""

from .metrics import evaluate
try:
    # prts is an optional dependency for affiliation-based metrics.
    from .affiliation import compute_affiliation_f1, threshold_by_rate
except ModuleNotFoundError:  # pragma: no cover
    def compute_affiliation_f1(*args, **kwargs):  # type: ignore[no-redef]
        raise ModuleNotFoundError(
            "prts is required for compute_affiliation_f1. Install it (e.g., `python3 -m pip install prts`)."
        )

    def threshold_by_rate(*args, **kwargs):  # type: ignore[no-redef]
        raise ModuleNotFoundError(
            "prts is required for threshold_by_rate (and affiliation metrics). Install it (e.g., `python3 -m pip install prts`)."
        )
from .sae_score import (
    SAEScoreResult,
    compute_alpha_from_counts,
    compute_alpha_from_short_ratio,
    compute_dataset_alpha_from_taxonomy_summary,
    compute_sae_score,
    rank_by_metric,
)
from .saps import SAPSConfig, apply_saps, suggest_saps_config_from_lengths
from .rank_flip_rate import compute_rank_flip_rate_by_dataset
from .statistical_tests import (
    ModelScores,
    average_ranks,
    build_cd_diagram_data,
    friedman_test,
    wilcoxon_pairwise,
)

__version__ = "0.1.0.dev0"

__all__ = [
    "__version__",
    "evaluate",
    "compute_rank_flip_rate_by_dataset",
    "ModelScores",
    "average_ranks",
    "build_cd_diagram_data",
    "friedman_test",
    "wilcoxon_pairwise",
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
