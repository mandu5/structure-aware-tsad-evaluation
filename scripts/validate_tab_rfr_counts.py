"""Validate TAB rank-flip counts used in the paper text.

The headline counts are AUC-ROC vs Aff-F1 endpoint disagreements. The
taxonomy-weighted SAEScore disagreements are reported separately to avoid
conflating the endpoint and composite quantities.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "experiments/results/sae_metrics_canonical.json"

DEEP_MODELS = ["AT", "TranAD", "CATCH", "DADA", "MOMENT"]
SEVEN_MODELS = DEEP_MODELS + ["IForest", "LOF"]
DATASETS = ["SWaT", "MSL", "SMAP", "WADI", "PSM", "SMD"]

EXPECTED = {
    ("deep", "aff_f1"): (14, 60),
    ("seven", "aff_f1"): (44, 126),
    ("deep", "sae_score"): (8, 60),
    ("seven", "sae_score"): (36, 126),
}


def _score_map(rows: list[dict]) -> dict[tuple[str, str], dict[str, float]]:
    scores: dict[tuple[str, str], dict[str, float]] = {}
    for row in rows:
        model = str(row["model"])
        dataset = str(row["dataset"])
        if dataset not in DATASETS:
            continue
        scores[(dataset, model)] = {
            "auc_roc": float(row["auc_roc"]),
            "aff_f1": float(row["aff_f1"]),
            "sae_score": float(row["sae_score"]),
        }
    return scores


def _count_flips(
    scores: dict[tuple[str, str], dict[str, float]],
    models: list[str],
    metric_b: str,
) -> tuple[int, int, dict[str, tuple[int, int]]]:
    total_flips = 0
    total_pairs = 0
    by_dataset: dict[str, tuple[int, int]] = {}
    for dataset in DATASETS:
        flips = 0
        pairs = 0
        for left, right in combinations(models, 2):
            l_scores = scores.get((dataset, left))
            r_scores = scores.get((dataset, right))
            if l_scores is None or r_scores is None:
                continue
            auc_delta = l_scores["auc_roc"] - r_scores["auc_roc"]
            other_delta = l_scores[metric_b] - r_scores[metric_b]
            if auc_delta == 0 or other_delta == 0:
                continue
            pairs += 1
            flips += int((auc_delta > 0) != (other_delta > 0))
        by_dataset[dataset] = (flips, pairs)
        total_flips += flips
        total_pairs += pairs
    return total_flips, total_pairs, by_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate TAB RFR counts.")
    parser.add_argument("--no-strict", action="store_true", help="Print counts without failing on mismatch.")
    args = parser.parse_args()

    payload = json.loads(CANONICAL.read_text())
    scores = _score_map(payload["rows"])

    failures: list[str] = []
    cohorts = {"deep": DEEP_MODELS, "seven": SEVEN_MODELS}
    results: dict[str, dict] = defaultdict(dict)
    for cohort_name, models in cohorts.items():
        for metric_b in ["aff_f1", "sae_score"]:
            flips, pairs, by_dataset = _count_flips(scores, models, metric_b)
            results[cohort_name][metric_b] = {
                "flips": flips,
                "pairs": pairs,
                "by_dataset": {k: {"flips": v[0], "pairs": v[1]} for k, v in by_dataset.items()},
            }
            expected = EXPECTED[(cohort_name, metric_b)]
            if (flips, pairs) != expected:
                failures.append(f"{cohort_name}/{metric_b}: got {flips}/{pairs}, expected {expected[0]}/{expected[1]}")

    print(json.dumps(results, indent=2, sort_keys=True))
    if failures and not args.no_strict:
        raise SystemExit("RFR validation failed: " + "; ".join(failures))


if __name__ == "__main__":
    main()
