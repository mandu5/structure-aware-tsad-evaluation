"""How much of a model leaderboard survives resampling of source collections?

For each metric, the 25 TSB-AD-M models are ranked on their mean score over
series. The series come from 17 source collections and are not independent, so
the bootstrap resamples whole collections (`rank_retention` in
src/evaluation/robustness.py). A model's rank retention is the share of
resamples in which it keeps the rank it holds on the full data.

Usage:
    python3 scripts/compute_rank_retention.py
    python3 scripts/compute_rank_retention.py --n-boot 20000 --seed 7

Output:
    experiments/results/tsbad_scaleup_canonical_*/rank_retention.json
    + a readable summary printed to stdout.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.robustness import rank_retention  # noqa: E402

DEFAULT_CANONICAL = ROOT / "experiments" / "results" / "tsbad_scaleup_canonical_0000_0200"
METRICS = ("auc_roc", "aff_f1")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Cluster-bootstrap rank retention of TSB-AD-M models.")
    p.add_argument("--canonical-dir", default=str(DEFAULT_CANONICAL),
                   help="Directory containing tsbad_sae_rows.csv.")
    p.add_argument("--n-boot", type=int, default=10000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--ci-level", type=float, default=0.95)
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    canon = Path(args.canonical_dir)
    rows = pd.read_csv(canon / "tsbad_sae_rows.csv")
    collection = rows.drop_duplicates("file_name").set_index("file_name")["collection"]

    out: dict = {
        "n_boot": args.n_boot,
        "seed": args.seed,
        "ci_level": args.ci_level,
        "resampling_unit": "source collection",
        "metrics": {},
    }
    for metric in METRICS:
        wide = rows.pivot(index="file_name", columns="model", values=metric)
        res = rank_retention(
            wide.to_numpy(),
            collection.loc[wide.index].to_numpy(),
            args.n_boot,
            np.random.default_rng(args.seed),
            ci_level=args.ci_level,
        )
        models = []
        for i, name in enumerate(wide.columns):
            models.append({
                "model": name,
                "mean_score": round(float(wide[name].mean()), 6),
                "point_rank": int(res["point_rank"][i]),
                "retention": float(res["retention"][i]),
                "rank_lo": float(res["rank_lo"][i]),
                "rank_hi": float(res["rank_hi"][i]),
                "top1_frequency": float(res["top1_freq"][i]),
            })
        models.sort(key=lambda m: (m["point_rank"], m["model"]))
        top, bottom = models[0], models[-1]
        out["metrics"][metric] = {
            "n_series": int(len(wide)),
            "n_models": int(wide.shape[1]),
            "n_collections": int(collection.loc[wide.index].nunique()),
            "top": {k: top[k] for k in ("model", "point_rank", "retention")},
            "bottom": {k: bottom[k] for k in ("model", "point_rank", "retention")},
            "models": models,
        }
        print(f"\n{metric}: {len(wide)} series, {wide.shape[1]} models, "
              f"{out['metrics'][metric]['n_collections']} collections")
        print(f"  {'rank':>4}  {'model':<22}{'mean':>7}{'retention':>11}{'rank CI':>10}")
        for m in models:
            print(f"  {m['point_rank']:>4}  {m['model']:<22}{m['mean_score']:>7.3f}"
                  f"{m['retention']:>11.1%}{'':>2}[{m['rank_lo']:.0f},{m['rank_hi']:.0f}]")

    path = canon / "rank_retention.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(f"\nwrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
