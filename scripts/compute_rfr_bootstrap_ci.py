"""Bootstrap confidence intervals for RFR(AUC-ROC vs SAEScore) on TSB-AD.

Reads a canonical TSB-AD snapshot (tsbad_sae_rows.csv) and resamples
series with replacement to estimate 95% CIs for:
  (a) overall pairwise flip rate (sum_flips / sum_pairs)
  (b) mean per-series RFR (averaged across series with comparable pairs)

Usage:
    python3 scripts/compute_rfr_bootstrap_ci.py
    python3 scripts/compute_rfr_bootstrap_ci.py --n-boot 5000 --seed 42

Output:
    experiments/results/tsbad_scaleup_canonical_*/rfr_bootstrap_ci.json
    + a one-line summary printed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from collections import defaultdict
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANONICAL = ROOT / "experiments" / "results" / "tsbad_scaleup_canonical_0000_0200"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Bootstrap RFR CIs from a canonical TSB-AD snapshot.")
    p.add_argument("--canonical-dir", default=str(DEFAULT_CANONICAL),
                   help="Directory containing tsbad_sae_rows.csv; output is written there.")
    p.add_argument("--n-boot", type=int, default=1000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--ci-level", type=float, default=0.95)
    return p.parse_args()


def _series_pair_stats(df_series: pd.DataFrame) -> tuple[int, int]:
    """For one series, return (n_pairs_non_tied, n_pairs_flipped)."""
    auc = df_series["auc_roc"].to_numpy()
    sae = df_series["saescore"].to_numpy()
    n = len(auc)
    if n < 2:
        return 0, 0
    # All unordered model pairs
    i, j = np.triu_indices(n, k=1)
    auc_diff = auc[i] - auc[j]
    sae_diff = sae[i] - sae[j]
    # Non-tied = both differences non-zero
    non_tied = (auc_diff != 0) & (sae_diff != 0)
    # Flipped = sign disagreement on the non-tied pairs
    flipped = non_tied & (np.sign(auc_diff) != np.sign(sae_diff))
    return int(non_tied.sum()), int(flipped.sum())


def main() -> None:
    args = _parse_args()
    canonical = Path(args.canonical_dir).expanduser().resolve()
    sae_rows_path = canonical / "tsbad_sae_rows.csv"
    out_path = canonical / "rfr_bootstrap_ci.json"
    if not sae_rows_path.exists():
        raise FileNotFoundError(
            f"{sae_rows_path} not found. Provide --canonical-dir with a directory containing tsbad_sae_rows.csv."
        )
    df = pd.read_csv(sae_rows_path)

    # Accept both legacy and current column names.
    rename_map = {}
    if "series" not in df.columns and "file_name" in df.columns:
        rename_map["file_name"] = "series"
    if "saescore" not in df.columns and "sae_score" in df.columns:
        rename_map["sae_score"] = "saescore"
    if rename_map:
        df = df.rename(columns=rename_map)

    needed = {"series", "model", "auc_roc", "saescore"}
    missing = needed - set(df.columns)
    if missing:
        raise RuntimeError(
            f"tsbad_sae_rows.csv missing columns: {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    # Group by series; precompute (pairs, flips) per series so resampling is fast.
    per_series: dict[str, tuple[int, int]] = {}
    for series, df_s in df.groupby("series"):
        per_series[series] = _series_pair_stats(df_s)

    series_list = list(per_series.keys())
    pairs_arr = np.array([per_series[s][0] for s in series_list])
    flips_arr = np.array([per_series[s][1] for s in series_list])

    # Point estimates
    point_pair_rate = (flips_arr.sum() / pairs_arr.sum()) if pairs_arr.sum() else 0.0
    rfr_per_series = np.where(pairs_arr > 0, flips_arr / np.maximum(pairs_arr, 1), 0.0)
    point_mean_rfr = rfr_per_series[pairs_arr > 0].mean() if (pairs_arr > 0).any() else 0.0

    # Bootstrap
    rng = np.random.default_rng(args.seed)
    n_series = len(series_list)
    pair_rates = np.empty(args.n_boot)
    mean_rfrs = np.empty(args.n_boot)

    for b in range(args.n_boot):
        idx = rng.integers(0, n_series, size=n_series)
        p_b = pairs_arr[idx].sum()
        f_b = flips_arr[idx].sum()
        pair_rates[b] = (f_b / p_b) if p_b else 0.0
        rfr_b = rfr_per_series[idx]
        # weighted-by-having-pairs mean
        mask = pairs_arr[idx] > 0
        mean_rfrs[b] = rfr_b[mask].mean() if mask.any() else 0.0

    alpha = (1 - args.ci_level) / 2
    pair_lo, pair_hi = np.quantile(pair_rates, [alpha, 1 - alpha])
    rfr_lo, rfr_hi = np.quantile(mean_rfrs, [alpha, 1 - alpha])

    payload = {
        "n_boot": int(args.n_boot),
        "seed": int(args.seed),
        "ci_level": float(args.ci_level),
        "n_series": int(n_series),
        "n_models": int(df["model"].nunique()),
        "point_estimates": {
            "overall_pairwise_flip_rate": float(point_pair_rate),
            "mean_per_series_rfr": float(point_mean_rfr),
        },
        "bootstrap_ci": {
            "overall_pairwise_flip_rate": [float(pair_lo), float(pair_hi)],
            "mean_per_series_rfr": [float(rfr_lo), float(rfr_hi)],
        },
        "bootstrap_se": {
            "overall_pairwise_flip_rate": float(pair_rates.std(ddof=1)),
            "mean_per_series_rfr": float(mean_rfrs.std(ddof=1)),
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))

    print(f"Wrote {out_path}")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    sys.exit(main())
