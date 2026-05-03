"""Compute alpha-stratified TSB-AD rank-flip summaries.

The canonical TSB-AD audit reports an overall within-series pairwise RFR.
This script splits that same computation by taxonomy weight:

- alpha = 1: segment-dominant series where SAEScore collapses to Aff-F1
- 0 < alpha < 1: genuine blend series
- alpha = 0: point-like series where SAEScore collapses to AUC-ROC
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANONICAL_DIR = ROOT / "experiments" / "results" / "tsbad_scaleup_canonical_0000_0200"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute TSB-AD alpha-stratified RFR summaries.")
    parser.add_argument("--canonical-dir", default=str(DEFAULT_CANONICAL_DIR))
    return parser.parse_args()


def strict_pair_stats(group: pd.DataFrame, metric_b: str) -> tuple[int, int]:
    auc = group["auc_roc"].to_numpy()
    other = group[metric_b].to_numpy()
    if len(group) < 2:
        return 0, 0
    i, j = np.triu_indices(len(group), k=1)
    auc_diff = auc[i] - auc[j]
    other_diff = other[i] - other[j]
    comparable = (auc_diff != 0) & (other_diff != 0)
    flipped = comparable & (np.sign(auc_diff) != np.sign(other_diff))
    return int(comparable.sum()), int(flipped.sum())


def alpha_bin(alpha: float) -> str:
    if np.isclose(alpha, 1.0):
        return "alpha=1"
    if np.isclose(alpha, 0.0):
        return "alpha=0"
    return "0<alpha<1"


def summarize(df: pd.DataFrame, metric_b: str) -> dict[str, object]:
    per_series: list[dict[str, object]] = []
    for file_name, group in df.groupby("file_name", sort=True):
        pairs, flips = strict_pair_stats(group, metric_b)
        alpha = float(group["alpha"].iloc[0])
        per_series.append(
            {
                "file_name": file_name,
                "collection": str(group["collection"].iloc[0]),
                "alpha": alpha,
                "alpha_bin": alpha_bin(alpha),
                "valid_model_rows": int(len(group)),
                "comparable_pairs": pairs,
                "flips": flips,
                "rfr": float(flips / pairs) if pairs else None,
            }
        )

    per_df = pd.DataFrame(per_series)
    summaries: dict[str, dict[str, object]] = {}
    for bin_name in ["alpha=1", "0<alpha<1", "alpha=0", "alpha<1", "all"]:
        if bin_name == "all":
            subset = per_df
        elif bin_name == "alpha<1":
            subset = per_df[per_df["alpha"] < 1.0]
        else:
            subset = per_df[per_df["alpha_bin"] == bin_name]
        pairs = int(subset["comparable_pairs"].sum())
        flips = int(subset["flips"].sum())
        rfr_values = subset["rfr"].dropna()
        summaries[bin_name] = {
            "n_series": int(len(subset)),
            "valid_model_rows": int(subset["valid_model_rows"].sum()),
            "comparable_pairs": pairs,
            "flips": flips,
            "pairwise_flip_rate": float(flips / pairs) if pairs else None,
            "mean_per_series_rfr": float(rfr_values.mean()) if len(rfr_values) else None,
        }

    return {
        "metric_a": "auc_roc",
        "metric_b": metric_b,
        "definition": "Within-series strict pairwise rank flips; tied pairs on either metric are excluded.",
        "by_alpha_bin": summaries,
        "per_series": per_series,
    }


def main() -> int:
    args = parse_args()
    canonical_dir = Path(args.canonical_dir).expanduser().resolve()
    rows_path = canonical_dir / "tsbad_sae_rows.csv"
    if not rows_path.exists():
        raise FileNotFoundError(rows_path)
    df = pd.read_csv(rows_path)
    try:
        canonical_dir_public = str(canonical_dir.relative_to(ROOT))
    except ValueError:
        canonical_dir_public = str(canonical_dir.name)

    out = {
        "canonical_dir": canonical_dir_public,
        "n_rows": int(len(df)),
        "n_series": int(df["file_name"].nunique()),
        "n_models": int(df["model"].nunique()),
        "auc_roc_vs_sae_score": summarize(df, "sae_score"),
        "auc_roc_vs_aff_f1": summarize(df, "aff_f1"),
    }
    out_path = canonical_dir / "tsbad_alpha_stratified_rfr.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k.startswith("n_")}, indent=2))
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
