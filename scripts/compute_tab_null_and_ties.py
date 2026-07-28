"""Null model, tie sensitivity and cluster-aware CIs for the six-dataset TAB study.

The headline flip counts of the paper -- 14/60 on five deep models and 44/126
once IForest and LOF are added -- are reported without three things:

  (1) a null model.  Under independent rankings the expected pairwise flip rate
      is 0.5, so a rate below that means the metrics agree more than chance.
  (2) a tie treatment.  Pairs of models separated by a negligible AUC-ROC margin
      flip at close to the chance rate by construction.
  (3) a cluster unit.  There are only six datasets, so pair-level uncertainty
      badly understates how much the estimate can move.

It also splits pairs by model class, because the 60 -> 126 increase comes
entirely from pairs involving a classical baseline: if those flip far more
often, the higher headline number describes the instability of weak detectors
rather than a property of the metrics.

Usage:
    python3 scripts/compute_tab_null_and_ties.py
    python3 scripts/compute_tab_null_and_ties.py --n-perm 5000 --seed 7

Output:
    experiments/results/tab_null_and_ties.json
    + a readable summary printed to stdout.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.robustness import flip_rate_null, pairwise_flips  # noqa: E402

DEFAULT_INPUT = ROOT / "experiments" / "results" / "sae_metrics_canonical.json"
DEFAULT_OUTPUT = ROOT / "experiments" / "results" / "tab_null_and_ties.json"

DEEP_MODELS = ("AT", "CATCH", "DADA", "MOMENT", "TranAD")
CLASSICAL_MODELS = ("IForest", "LOF")

GAP_EDGES = [0.0, 0.05, 0.10, 0.20, np.inf]
NOISE_BANDS = [0.02, 0.05, 0.10]


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Null/tie/cluster analysis for the six-dataset TAB study.")
    p.add_argument("--input", default=str(DEFAULT_INPUT))
    p.add_argument("--output", default=str(DEFAULT_OUTPUT))
    p.add_argument("--n-perm", type=int, default=2000)
    p.add_argument("--n-boot", type=int, default=5000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--ci-level", type=float, default=0.95)
    return p.parse_args()


def _analyse(by_dataset: dict[str, list[dict]], models: tuple[str, ...], secondary: str,
             n_perm: int, n_boot: int, ci_level: float, rng: np.random.Generator) -> dict:
    """Flip statistics for one model set and one comparison metric."""
    groups, per_dataset, gaps, flips = [], [], [], []
    for ds in sorted(by_dataset):
        rows = {r["model"]: r for r in by_dataset[ds]}
        present = [m for m in models if m in rows]
        auc = np.array([rows[m]["auc_roc"] for m in present], dtype=float)
        sec = np.array([rows[m][secondary] for m in present], dtype=float)
        groups.append((auc, sec))
        gap, flipped = pairwise_flips(auc, sec)
        gaps.append(gap)
        flips.append(flipped)
        per_dataset.append({
            "dataset": ds,
            "alpha": float(rows[present[0]]["alpha"]),
            "pairs": int(gap.size),
            "flips": int(flipped.sum()),
            "flip_rate": float(flipped.mean()) if gap.size else None,
        })

    gap_all = np.concatenate(gaps)
    flip_all = np.concatenate(flips)
    n_pairs, n_flips = int(flip_all.size), int(flip_all.sum())
    observed = n_flips / n_pairs if n_pairs else float("nan")

    null = flip_rate_null(groups, n_perm, rng)

    gap_buckets = []
    for lo, hi in zip(GAP_EDGES[:-1], GAP_EDGES[1:]):
        m = (gap_all >= lo) & (gap_all < hi)
        gap_buckets.append({
            "lo": float(lo), "hi": (None if np.isinf(hi) else float(hi)),
            "pairs": int(m.sum()),
            "flip_rate": float(flip_all[m].mean()) if m.any() else None,
        })

    noise_band = []
    for thr in NOISE_BANDS:
        m = gap_all >= thr
        noise_band.append({
            "excluded_below": float(thr),
            "pairs_retained": int(m.sum()),
            "share_retained": float(m.mean()) if gap_all.size else None,
            "flip_rate": float(flip_all[m].mean()) if m.any() else None,
        })

    # cluster bootstrap over datasets vs naive bootstrap over pairs
    names = [d["dataset"] for d in per_dataset]
    pairs_by_ds = {d["dataset"]: d["pairs"] for d in per_dataset}
    flips_by_ds = {d["dataset"]: d["flips"] for d in per_dataset}
    cb = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.choice(names, size=len(names), replace=True)
        p = sum(pairs_by_ds[c] for c in pick)
        cb[b] = sum(flips_by_ds[c] for c in pick) / p if p else np.nan
    pb = rng.binomial(n_pairs, observed, size=n_boot) / n_pairs if n_pairs else np.full(n_boot, np.nan)

    q = (1 - ci_level) / 2
    return {
        "n_models": len(models),
        "n_pairs": n_pairs,
        "n_flips": n_flips,
        "flip_rate": observed,
        "agreement_share": 1.0 - observed if n_pairs else None,
        "random_ranking_null": {
            "mean": float(np.nanmean(null)),
            "sd": float(np.nanstd(null, ddof=1)),
            "n_perm": int(n_perm),
        },
        "per_dataset": per_dataset,
        "gap_stratified": gap_buckets,
        "noise_band_sensitivity": noise_band,
        "ci": {
            "level": ci_level,
            "cluster_over_datasets": [float(np.nanquantile(cb, q)), float(np.nanquantile(cb, 1 - q))],
            "pair_level": [float(np.nanquantile(pb, q)), float(np.nanquantile(pb, 1 - q))],
        },
    }


def _by_model_class(by_dataset: dict[str, list[dict]], secondary: str) -> dict:
    """Flip rate split by whether a pair involves a classical baseline."""
    buckets: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for ds in sorted(by_dataset):
        rows = {r["model"]: r for r in by_dataset[ds]}
        for m1, m2 in combinations([m for m in DEEP_MODELS + CLASSICAL_MODELS if m in rows], 2):
            a1, s1 = rows[m1]["auc_roc"], rows[m1][secondary]
            a2, s2 = rows[m2]["auc_roc"], rows[m2][secondary]
            if a1 == a2 or s1 == s2:
                continue
            n_classical = (m1 in CLASSICAL_MODELS) + (m2 in CLASSICAL_MODELS)
            key = ("deep-deep", "deep-classical", "classical-classical")[n_classical]
            buckets[key][1] += 1
            if (a1 > a2) != (s1 > s2):
                buckets[key][0] += 1
    return {k: {"pairs": v[1], "flips": v[0], "flip_rate": v[0] / v[1] if v[1] else None}
            for k, v in buckets.items()}


def main() -> None:
    args = _parse_args()
    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"{src} not found.")
    payload_in = json.loads(src.read_text())
    rows = payload_in["rows"] if isinstance(payload_in, dict) else payload_in

    by_dataset: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r.get("auc_roc") is None or r.get("aff_f1") is None:
            continue
        by_dataset[r["dataset"]].append(r)

    rng = np.random.default_rng(args.seed)
    out: dict = {
        "source": src.name,
        "n_datasets": len(by_dataset),
        "seed": args.seed,
        "alpha_by_dataset": {ds: float(rs[0]["alpha"]) for ds, rs in sorted(by_dataset.items())},
        "results": {},
        "by_model_class": {},
    }
    for set_name, models in (("deep_only", DEEP_MODELS), ("all_models", DEEP_MODELS + CLASSICAL_MODELS)):
        for secondary in ("aff_f1", "sae_score"):
            out["results"][f"{set_name}__auc_roc_vs_{secondary}"] = _analyse(
                by_dataset, models, secondary, args.n_perm, args.n_boot, args.ci_level, rng
            )
    for secondary in ("aff_f1", "sae_score"):
        out["by_model_class"][f"auc_roc_vs_{secondary}"] = _by_model_class(by_dataset, secondary)

    n_alpha_lt1 = sum(1 for v in out["alpha_by_dataset"].values() if v < 1.0)
    out["structure_support"] = {
        "n_datasets_with_alpha_lt_1": n_alpha_lt1,
        "n_datasets": len(by_dataset),
        "note": ("Any structure-conditioned claim in this study is supported by the datasets with "
                 f"alpha < 1, of which there are {n_alpha_lt1} of {len(by_dataset)}. With SAEScore "
                 "reducing to Aff-F1 at alpha = 1, the remaining datasets carry no blend information."),
    }

    Path(args.output).write_text(json.dumps(out, indent=2))

    # ---------------- summary ----------------
    print(f"Wrote {args.output}\n")
    print(f"datasets={out['n_datasets']}  alpha<1 in {n_alpha_lt1} of {out['n_datasets']}: "
          f"{ {k: v for k, v in out['alpha_by_dataset'].items() if v < 1.0} }\n")
    for key, r in out["results"].items():
        null = r["random_ranking_null"]
        print(f"--- {key}  ({r['n_models']} models) ---")
        print(f"  flips {r['n_flips']}/{r['n_pairs']} = {r['flip_rate']:.4f}   "
              f"null {null['mean']:.4f} (sd {null['sd']:.4f})   agree {100 * r['agreement_share']:.1f}%")
        strat = "  ".join(
            f"[{b['lo']:.2f},{'inf' if b['hi'] is None else format(b['hi'], '.2f')})="
            + (f"{b['flip_rate']:.3f}(n={b['pairs']})" if b["flip_rate"] is not None else "n/a")
            for b in r["gap_stratified"]
        )
        print(f"  by |dAUC|: {strat}")
        nb = r["noise_band_sensitivity"][1]
        print(f"  drop |dAUC|<{nb['excluded_below']:.2f}: {nb['flip_rate']:.4f} "
              f"({100 * nb['share_retained']:.0f}% pairs kept)")
        ci = r["ci"]
        print(f"  95% CI  cluster-over-datasets [{ci['cluster_over_datasets'][0]:.4f}, "
              f"{ci['cluster_over_datasets'][1]:.4f}]   pair-level "
              f"[{ci['pair_level'][0]:.4f}, {ci['pair_level'][1]:.4f}]")
        print("  per-dataset: " + "  ".join(
            f"{d['dataset']}(a={d['alpha']:.2f}){d['flips']}/{d['pairs']}" for d in r["per_dataset"]))
        print()
    print("--- pairs by model class (all 7 models) ---")
    for metric, d in out["by_model_class"].items():
        print(f"  {metric}")
        for k in ("deep-deep", "deep-classical", "classical-classical"):
            if k in d:
                print(f"    {k:22s} {d[k]['flips']:3d}/{d[k]['pairs']:3d} = {d[k]['flip_rate']:.4f}")


if __name__ == "__main__":
    sys.exit(main())
