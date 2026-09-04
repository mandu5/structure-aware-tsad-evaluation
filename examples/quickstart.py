"""60-second demo: do point-wise and segment-aware metrics rank your models the same way?

Runs on synthetic data (no dataset download). Three toy detectors are scored on
three series with sustained anomaly segments; AUC-ROC (point-wise) and
Affiliation-F1 (segment-aware) are computed per (series, model), then the
rank-flip rate between the two metrics is reported.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_auc_score

from tsad_eval import (
    compute_affiliation_f1,
    compute_rank_flip_rate_by_dataset,
    threshold_by_rate,
)


def make_series(rng: np.random.Generator, n: int = 2000, n_segments: int = 3, seg_len: int = 60):
    x = rng.normal(size=n)
    y = np.zeros(n, dtype=int)
    for _ in range(n_segments):
        s = rng.integers(0, n - seg_len)
        x[s : s + seg_len] += rng.normal(2.5, 0.5)  # sustained level shift
        y[s : s + seg_len] = 1
    return x, y


def detectors(x: np.ndarray, rng: np.random.Generator) -> dict[str, np.ndarray]:
    """Toy detectors returning an anomaly score per timestep."""
    abs_dev = np.abs(x - np.median(x))
    kernel = np.ones(25) / 25
    smoothed = np.convolve(abs_dev, kernel, mode="same")
    return {
        "PointDeviation": abs_dev,                       # reacts to single points
        "WindowMean": smoothed,                          # reacts to sustained shifts
        "NoisyWindow": smoothed + rng.normal(0, 0.6, x.size),
    }


def main() -> None:
    rng = np.random.default_rng(0)
    rows = []
    for d in range(3):
        x, y = make_series(rng)
        for name, score in detectors(x, rng).items():
            pred = threshold_by_rate(score, y)  # threshold at the true anomaly rate
            rows.append(
                {
                    "dataset": f"series_{d}",
                    "model": name,
                    "auc_roc": float(roc_auc_score(y, score)),
                    "aff_f1": compute_affiliation_f1(y, pred),
                }
            )

    print(f"{'series':<10}{'model':<16}{'AUC-ROC':>9}{'Aff-F1':>9}")
    for r in rows:
        print(f"{r['dataset']:<10}{r['model']:<16}{r['auc_roc']:>9.3f}{r['aff_f1']:>9.3f}")

    report = compute_rank_flip_rate_by_dataset(rows, metric_a="auc_roc", metric_b="aff_f1")
    print("\nRank-flip rate (AUC-ROC vs Affiliation-F1):")
    for ds, v in report["by_dataset"].items():
        print(f"  {ds}: {v['n_flips']}/{v['n_comparable_pairs']} pairs flipped  (RFR={v['rfr']:.2f})")
    print(f"  mean RFR = {report['mean_rfr_over_datasets_with_pairs']:.2f}")


if __name__ == "__main__":
    main()
