"""Statistical significance tests for Phase 1-B benchmark.

Implements:
  - Wilcoxon signed-rank test (pairwise model comparison across datasets)
  - Friedman test (omnibus test across all models)
  - Critical Difference (CD) diagram data generation (Demšar 2006)
  - Average-rank computation for CD diagrams
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy import stats


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class ModelScores:
    """Per-model scores across datasets and seeds.

    scores: dict[(dataset, seed)] -> metric_value
    """
    model: str
    metric: str
    scores: dict[tuple[str, int], float] = field(default_factory=dict)

    def mean_per_dataset(self) -> dict[str, float]:
        """Average over seeds for each dataset."""
        from collections import defaultdict
        acc: dict[str, list[float]] = defaultdict(list)
        for (dataset, _seed), val in self.scores.items():
            acc[dataset].append(val)
        return {ds: float(np.mean(vals)) for ds, vals in acc.items()}

    def flat_values(self, datasets: list[str] | None = None) -> np.ndarray:
        """Return mean-per-dataset values as a flat array (for Wilcoxon)."""
        means = self.mean_per_dataset()
        if datasets is None:
            datasets = sorted(means)
        return np.array([means[d] for d in datasets if d in means])


@dataclass
class WilcoxonResult:
    model_a: str
    model_b: str
    metric: str
    statistic: float
    p_value: float
    significant: bool  # p < 0.05
    direction: str     # "A>B", "B>A", or "tie"


@dataclass
class FriedmanResult:
    metric: str
    statistic: float
    p_value: float
    significant: bool


@dataclass
class CDDiagramData:
    """Data needed to draw a Critical Difference diagram."""
    metric: str
    model_ranks: dict[str, float]          # model -> average rank
    cd_threshold: float                    # CD value at alpha=0.05
    n_datasets: int
    n_models: int
    cliques: list[list[str]]               # groups of models not significantly different


# ---------------------------------------------------------------------------
# Core statistical functions
# ---------------------------------------------------------------------------

def wilcoxon_pairwise(
    model_scores: list[ModelScores],
    datasets: list[str] | None = None,
    alpha: float = 0.05,
) -> list[WilcoxonResult]:
    """Run Wilcoxon signed-rank test for every pair of models.

    Args:
        model_scores: List of ModelScores, one per model.
        datasets: Dataset subset to evaluate on.  None = all shared datasets.
        alpha: Significance level.

    Returns:
        List of WilcoxonResult for every (model_a, model_b) pair where a < b.
    """
    if datasets is None:
        # Use intersection of datasets present in all models
        shared: set[str] = set()
        for ms in model_scores:
            ds_set = set(ms.mean_per_dataset().keys())
            shared = ds_set if not shared else shared & ds_set
        datasets = sorted(shared)

    results: list[WilcoxonResult] = []
    metric = model_scores[0].metric if model_scores else "unknown"
    n = len(model_scores)
    for i in range(n):
        for j in range(i + 1, n):
            a = model_scores[i]
            b = model_scores[j]
            va = a.flat_values(datasets)
            vb = b.flat_values(datasets)
            if len(va) < 2 or len(vb) < 2 or len(va) != len(vb):
                continue
            diff = va - vb
            if np.all(diff == 0):
                results.append(WilcoxonResult(
                    model_a=a.model, model_b=b.model, metric=metric,
                    statistic=0.0, p_value=1.0, significant=False, direction="tie"
                ))
                continue
            try:
                stat, p = stats.wilcoxon(diff, alternative="two-sided")
            except ValueError:
                p = 1.0
                stat = 0.0
            direction = "tie"
            if p < alpha:
                direction = f"{a.model}>{b.model}" if va.mean() > vb.mean() else f"{b.model}>{a.model}"
            results.append(WilcoxonResult(
                model_a=a.model, model_b=b.model, metric=metric,
                statistic=float(stat), p_value=float(p),
                significant=p < alpha, direction=direction,
            ))
    return results


def friedman_test(
    model_scores: list[ModelScores],
    datasets: list[str] | None = None,
) -> FriedmanResult:
    """Friedman rank test across all models (omnibus test).

    Args:
        model_scores: One ModelScores per model.
        datasets: Datasets to include (None = shared intersection).

    Returns:
        FriedmanResult with chi-square statistic and p-value.
    """
    if datasets is None:
        shared: set[str] = set()
        for ms in model_scores:
            ds_set = set(ms.mean_per_dataset().keys())
            shared = ds_set if not shared else shared & ds_set
        datasets = sorted(shared)

    metric = model_scores[0].metric if model_scores else "unknown"
    # Build matrix: rows=datasets, cols=models
    matrix = np.array([ms.flat_values(datasets) for ms in model_scores]).T
    if matrix.shape[1] < 3:
        # Friedman requires at least 3 groups (models)
        return FriedmanResult(metric=metric, statistic=0.0, p_value=1.0, significant=False)
    if matrix.shape[0] < 2:
        return FriedmanResult(metric=metric, statistic=0.0, p_value=1.0, significant=False)
    stat, p = stats.friedmanchisquare(*[matrix[:, j] for j in range(matrix.shape[1])])
    return FriedmanResult(
        metric=metric, statistic=float(stat), p_value=float(p), significant=p < 0.05
    )


def average_ranks(
    model_scores: list[ModelScores],
    datasets: list[str] | None = None,
    higher_is_better: bool = True,
) -> dict[str, float]:
    """Compute average rank of each model across datasets (Demšar 2006).

    Args:
        model_scores: One ModelScores per model.
        datasets: Datasets to rank across.
        higher_is_better: If True, rank 1 = highest score.

    Returns:
        Dict mapping model_name -> average rank (1-indexed).
    """
    if datasets is None:
        shared: set[str] = set()
        for ms in model_scores:
            ds_set = set(ms.mean_per_dataset().keys())
            shared = ds_set if not shared else shared & ds_set
        datasets = sorted(shared)

    # matrix[i, j] = score of model i on dataset j
    matrix = np.array([ms.flat_values(datasets) for ms in model_scores])
    n_models, n_datasets = matrix.shape
    rank_matrix = np.zeros_like(matrix)
    for j in range(n_datasets):
        col = matrix[:, j]
        # scipy.stats.rankdata ranks 1=smallest; flip if higher_is_better
        ranks = stats.rankdata(col, method="average")
        if higher_is_better:
            ranks = n_models + 1 - ranks
        rank_matrix[:, j] = ranks
    avg_ranks = rank_matrix.mean(axis=1)
    return {ms.model: float(avg_ranks[i]) for i, ms in enumerate(model_scores)}


def _cd_threshold(n_models: int, n_datasets: int, alpha: float = 0.05) -> float:
    """Critical Difference threshold using Nemenyi post-hoc test (Demšar 2006).

    CD = q_alpha * sqrt(k(k+1) / (6*N))
    where q_alpha is from the Studentized range distribution / sqrt(2).
    """
    # q_alpha values for alpha=0.05 (from Demšar 2006, Table 5)
    q_table = {
        2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728, 6: 2.850,
        7: 2.949, 8: 3.031, 9: 3.102, 10: 3.164,
    }
    k = min(n_models, 10)
    q = q_table.get(k, 3.164)
    cd = q * np.sqrt(k * (k + 1) / (6 * n_datasets))
    return float(cd)


def build_cd_diagram_data(
    model_scores: list[ModelScores],
    datasets: list[str] | None = None,
    higher_is_better: bool = True,
    alpha: float = 0.05,
) -> CDDiagramData:
    """Build all data needed to render a Critical Difference diagram.

    Args:
        model_scores: One ModelScores per model.
        datasets: Datasets to rank across (None = shared).
        higher_is_better: Direction for ranking.
        alpha: Significance level for CD threshold.

    Returns:
        CDDiagramData with average ranks, CD threshold, and cliques.
    """
    if datasets is None:
        shared: set[str] = set()
        for ms in model_scores:
            ds_set = set(ms.mean_per_dataset().keys())
            shared = ds_set if not shared else shared & ds_set
        datasets = sorted(shared)

    ranks = average_ranks(model_scores, datasets, higher_is_better)
    n_models = len(model_scores)
    n_datasets = len(datasets)
    cd = _cd_threshold(n_models, n_datasets, alpha)
    metric = model_scores[0].metric if model_scores else "unknown"

    # Find cliques: groups of models whose rank difference <= CD
    sorted_models = sorted(ranks, key=lambda m: ranks[m])
    cliques: list[list[str]] = []
    for i, m_i in enumerate(sorted_models):
        clique = [m_i]
        for j in range(i + 1, len(sorted_models)):
            m_j = sorted_models[j]
            if abs(ranks[m_j] - ranks[m_i]) <= cd:
                clique.append(m_j)
            else:
                break
        if len(clique) >= 2:
            # Only add if not already contained in a previous clique
            if not any(set(clique).issubset(set(c)) for c in cliques):
                cliques.append(clique)

    return CDDiagramData(
        metric=metric,
        model_ranks=ranks,
        cd_threshold=cd,
        n_datasets=n_datasets,
        n_models=n_models,
        cliques=cliques,
    )


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def wilcoxon_results_to_dict(results: list[WilcoxonResult]) -> list[dict[str, Any]]:
    return [
        {
            "model_a": r.model_a,
            "model_b": r.model_b,
            "metric": r.metric,
            "statistic": round(r.statistic, 4),
            "p_value": round(r.p_value, 4),
            "significant": r.significant,
            "direction": r.direction,
        }
        for r in results
    ]


def cd_diagram_data_to_dict(cd: CDDiagramData) -> dict[str, Any]:
    return {
        "metric": cd.metric,
        "model_ranks": {k: round(v, 4) for k, v in sorted(cd.model_ranks.items(), key=lambda x: x[1])},
        "cd_threshold": round(cd.cd_threshold, 4),
        "n_datasets": cd.n_datasets,
        "n_models": cd.n_models,
        "cliques": cd.cliques,
    }
