"""Robustness re-analysis of structure-conditioned ranking disagreement on TSB-AD.

This script replaces the alpha-stratified analysis with three checks it was
missing, all computed from the canonical snapshot already on disk:

  (1) Null model.  A pairwise flip rate is uninterpretable without a baseline.
      Permuting model labels of the second metric within each series gives the
      random-ranking reference (~0.5).

  (2) Tie sensitivity.  Flip rates are stratified by |dAUC-ROC| so that
      disagreement among near-tied models is separated from disagreement among
      clearly separated models.

  (3) Cluster-aware inference.  The structure weight alpha = 1 - short_ratio is
      almost constant within a dataset collection, so series are not independent
      units.  Every structural predictor is evaluated at series level AND at
      collection level, with leave-one-collection-out and a cluster bootstrap.

It also records the SAEScore reduction identity, which makes the alpha-stratified
table non-informative: SAEScore = (1 - alpha) * AUC-ROC + alpha * Aff-F1, so at
alpha = 0 it is identically AUC-ROC and at alpha = 1 it is identically Aff-F1.

Usage:
    python3 scripts/compute_structure_robustness.py
    python3 scripts/compute_structure_robustness.py --n-perm 500 --seed 7

Output:
    experiments/results/tsbad_scaleup_canonical_*/structure_robustness.json
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

from src.evaluation.robustness import (  # noqa: E402
    flip_rate_null,
    pairwise_flips,
    spearman,
    spearman_perm_p,
)

DEFAULT_CANONICAL = ROOT / "experiments" / "results" / "tsbad_scaleup_canonical_0000_0200"

GAP_EDGES = [0.0, 0.01, 0.02, 0.05, 0.10, 0.20, np.inf]
SEC_GAP_EDGES = [0.0, 0.02, 0.05, 0.10, 0.20, 0.40, np.inf]
NOISE_BANDS = [0.01, 0.02, 0.05]
JOINT_THRESHOLDS = [0.05, 0.10, 0.20]


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Cluster-aware robustness re-analysis of TSB-AD flip rates.")
    p.add_argument("--canonical-dir", default=str(DEFAULT_CANONICAL),
                   help="Directory containing tsbad_sae_rows.csv and tsbad_taxonomy_summary.json.")
    p.add_argument("--n-perm", type=int, default=200,
                   help="Permutations for the random-ranking null of the flip rate.")
    p.add_argument("--n-perm-rho", type=int, default=10000,
                   help="Permutations for correlation p-values.")
    p.add_argument("--n-boot", type=int, default=2000,
                   help="Cluster-bootstrap resamples over collections.")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--ci-level", type=float, default=0.95)
    return p.parse_args()


def _collect(groups: list[tuple[str, str, np.ndarray, np.ndarray]]) -> dict:
    """Aggregate pairwise stats across series.

    groups: list of (series, collection, auc, other).

    Records the margin on *both* metrics for every pair. Stratifying on the
    primary margin alone is one-sided: it selects pairs the primary metric
    separates confidently while saying nothing about whether the secondary
    metric separates them at all, so the surviving "flips" are concentrated
    where the secondary margin is negligible.
    """
    per_series = []
    gaps_all, gaps_b_all, flip_all = [], [], []
    for series, collection, auc, other in groups:
        gap, flipped = pairwise_flips(auc, other)
        gap_b, _ = pairwise_flips(other, auc)  # same pair set, margin on the secondary metric
        rec = {
            "series": series,
            "collection": collection,
            "pairs": int(gap.size),
            "flips": int(flipped.sum()),
            "rfr": float(flipped.mean()) if gap.size else float("nan"),
        }
        for thr in JOINT_THRESHOLDS:
            m = (gap >= thr) & (gap_b >= thr)
            key = f"{thr:.2f}".replace("0.", "")
            rec[f"pairs_joint{key}"] = int(m.sum())
            rec[f"flips_joint{key}"] = int(flipped[m].sum())
            rec[f"rfr_joint{key}"] = float(flipped[m].mean()) if m.any() else float("nan")
        per_series.append(rec)
        gaps_all.append(gap)
        gaps_b_all.append(gap_b)
        flip_all.append(flipped)
    return {
        "per_series": per_series,
        "gap": np.concatenate(gaps_all) if gaps_all else np.empty(0),
        "gap_secondary": np.concatenate(gaps_b_all) if gaps_b_all else np.empty(0),
        "flip": np.concatenate(flip_all) if flip_all else np.empty(0, dtype=bool),
    }


def main() -> None:
    args = _parse_args()
    canonical = Path(args.canonical_dir).expanduser().resolve()
    rows_path = canonical / "tsbad_sae_rows.csv"
    tax_path = canonical / "tsbad_taxonomy_summary.json"
    out_path = canonical / "structure_robustness.json"
    for p in (rows_path, tax_path):
        if not p.exists():
            raise FileNotFoundError(f"{p} not found. Pass --canonical-dir pointing at a canonical snapshot.")

    # Default float parsing collapses values such as 0.9999999999999999 to 1.0,
    # inventing ties that the exact-equality tie rule then drops.
    df = pd.read_csv(rows_path, float_precision="round_trip")
    if "sae_score" in df.columns and "saescore" not in df.columns:
        df = df.rename(columns={"sae_score": "saescore"})
    needed = {"file_name", "collection", "model", "auc_roc", "aff_f1", "alpha", "saescore"}
    missing = needed - set(df.columns)
    if missing:
        raise RuntimeError(f"{rows_path.name} missing columns: {missing}")

    tax = {r["file_name"]: r for r in json.loads(tax_path.read_text())}

    df = df[np.isfinite(df["auc_roc"]) & np.isfinite(df["aff_f1"])]

    groups_aff, groups_sae = [], []
    for series, g in df.groupby("file_name", sort=True):
        coll = str(g["collection"].iloc[0])
        auc = g["auc_roc"].to_numpy(dtype=float)
        groups_aff.append((series, coll, auc, g["aff_f1"].to_numpy(dtype=float)))
        groups_sae.append((series, coll, auc, g["saescore"].to_numpy(dtype=float)))

    aff = _collect(groups_aff)
    sae = _collect(groups_sae)

    rng = np.random.default_rng(args.seed)

    # ---------------- (0) SAEScore reduction identity ----------------
    # alpha = 0 -> SAEScore == AUC-ROC ; alpha = 1 -> SAEScore == Aff-F1.
    a = df["alpha"].to_numpy(dtype=float)
    max_err_a0 = float(np.max(np.abs(df["saescore"].to_numpy()[a == 0] - df["auc_roc"].to_numpy()[a == 0]))) \
        if (a == 0).any() else None
    max_err_a1 = float(np.max(np.abs(df["saescore"].to_numpy()[a == 1] - df["aff_f1"].to_numpy()[a == 1]))) \
        if (a == 1).any() else None

    obs_aff = float(aff["flip"].mean())
    obs_sae = float(sae["flip"].mean())

    # ---------------- (1) random-ranking null ----------------
    null_rates = flip_rate_null(
        [(auc, other) for _, _, auc, other in groups_aff], args.n_perm, rng
    )

    # ---------------- (2) gap stratification ----------------
    gap, flip = aff["gap"], aff["flip"]
    gap_buckets = []
    for lo, hi in zip(GAP_EDGES[:-1], GAP_EDGES[1:]):
        m = (gap >= lo) & (gap < hi)
        gap_buckets.append({
            "lo": float(lo), "hi": (None if np.isinf(hi) else float(hi)),
            "pairs": int(m.sum()),
            "share_of_pairs": float(m.mean()),
            "flip_rate": float(flip[m].mean()) if m.any() else None,
        })
    noise_band = []
    for thr in NOISE_BANDS:
        m = gap >= thr
        noise_band.append({
            "excluded_below": float(thr),
            "pairs_retained": int(m.sum()),
            "share_retained": float(m.mean()),
            "flip_rate": float(flip[m].mean()) if m.any() else None,
        })

    # Stratifying on the primary margin alone is one-sided. Repeat on the
    # secondary margin, and then require both metrics to separate the pair.
    gap_b = aff["gap_secondary"]
    sec_buckets = []
    for lo, hi in zip(SEC_GAP_EDGES[:-1], SEC_GAP_EDGES[1:]):
        m = (gap_b >= lo) & (gap_b < hi)
        sec_buckets.append({
            "lo": float(lo), "hi": (None if np.isinf(hi) else float(hi)),
            "pairs": int(m.sum()),
            "share_of_pairs": float(m.mean()),
            "flip_rate": float(flip[m].mean()) if m.any() else None,
        })
    joint = []
    for thr in JOINT_THRESHOLDS:
        m = (gap >= thr) & (gap_b >= thr)
        joint.append({
            "both_at_least": float(thr),
            "pairs": int(m.sum()),
            "share_of_pairs": float(m.mean()),
            "flip_rate": float(flip[m].mean()) if m.any() else None,
        })

    # ---------------- (3) structural predictors ----------------
    ps = pd.DataFrame(aff["per_series"])
    ps = ps[ps["pairs"] > 0].copy()
    ps["alpha"] = [float(tax[s]["alpha"]) for s in ps["series"]]
    ps["segment_count"] = [int(tax[s]["Total"]) for s in ps["series"]]
    ps["mean_segment_duration"] = [
        float(tax[s]["n_anomaly_points"]) / int(tax[s]["Total"]) if int(tax[s]["Total"]) else np.nan
        for s in ps["series"]
    ]
    ps["anomaly_density"] = [float(tax[s]["n_anomaly_points"]) / int(tax[s]["n_points"]) for s in ps["series"]]
    ps["series_length"] = [int(tax[s]["n_points"]) for s in ps["series"]]

    coll = ps.groupby("collection").apply(
        lambda g: pd.Series({
            "flip_rate": g["flips"].sum() / g["pairs"].sum(),
            "n_series": len(g),
            **{k: g[k].mean() for k in
               ["alpha", "segment_count", "mean_segment_duration", "anomaly_density", "series_length"]},
        }),
        include_groups=False,
    ).reset_index()

    collections = sorted(ps["collection"].unique())
    predictors = {}
    for name in ["alpha", "mean_segment_duration", "segment_count", "anomaly_density", "series_length"]:
        loco = []
        for drop in collections:
            sub = ps[ps["collection"] != drop]
            loco.append({"dropped": drop, "rho": spearman(sub[name], sub["rfr"])})
        finite = [d["rho"] for d in loco if np.isfinite(d["rho"])]
        predictors[name] = {
            "series_level": {
                "n": int(len(ps)),
                "rho": spearman(ps[name], ps["rfr"]),
                "perm_p": spearman_perm_p(ps[name].to_numpy(), ps["rfr"].to_numpy(), args.n_perm_rho, rng),
            },
            "collection_level": {
                "n": int(len(coll)),
                "rho": spearman(coll[name], coll["flip_rate"]),
                "perm_p": spearman_perm_p(coll[name].to_numpy(), coll["flip_rate"].to_numpy(),
                                           args.n_perm_rho, rng),
            },
            "leave_one_collection_out": {
                "min_rho": float(np.min(finite)) if finite else None,
                "max_rho": float(np.max(finite)) if finite else None,
                "worst_drop": min(loco, key=lambda d: abs(d["rho"]) if np.isfinite(d["rho"]) else np.inf)["dropped"],
                "all": loco,
            },
        }

    # The predictor block above uses the one-sided pooled rate, which Section on
    # margins shows is mostly contaminated by near-ties on the secondary metric.
    # Re-run it against the paper's own preferred two-sided estimand.
    predictors_joint = {}
    for thr in JOINT_THRESHOLDS:
        key = f"{thr:.2f}".replace("0.", "")
        sub = ps[ps[f"pairs_joint{key}"] > 0].copy()
        colj = sub.groupby("collection").apply(
            lambda g: pd.Series({
                "flip_rate": g[f"flips_joint{key}"].sum() / g[f"pairs_joint{key}"].sum(),
                **{k: g[k].mean() for k in ["alpha", "segment_count", "mean_segment_duration"]},
            }),
            include_groups=False,
        ).reset_index()
        entry = {"threshold": float(thr), "n_series_retained": int(len(sub)),
                 "n_collections": int(len(colj)), "predictors": {}}
        for name in ["alpha", "mean_segment_duration", "segment_count"]:
            entry["predictors"][name] = {
                "series_rho": spearman(sub[name], sub[f"rfr_joint{key}"]),
                "series_perm_p": spearman_perm_p(sub[name].to_numpy(),
                                                 sub[f"rfr_joint{key}"].to_numpy(),
                                                 args.n_perm_rho, rng),
                "collection_rho": spearman(colj[name], colj["flip_rate"]),
                "collection_perm_p": spearman_perm_p(colj[name].to_numpy(),
                                                     colj["flip_rate"].to_numpy(),
                                                     args.n_perm_rho, rng),
            }
        predictors_joint[key] = entry

    # within-collection variance of each predictor: is it a series variable at all?
    identifiability = {}
    for name in ["alpha", "mean_segment_duration", "segment_count"]:
        nunique = ps.groupby("collection")[name].nunique()
        sizes = ps.groupby("collection").size()
        big = sizes[sizes >= 8].index
        multi = sizes[sizes >= 2].index
        identifiability[name] = {
            "collections_with_constant_value": int((nunique <= 1).sum()),
            "n_collections": int(len(nunique)),
            "constant_among_multi_series_collections": int((nunique[multi] <= 1).sum()),
            "n_multi_series_collections": int(len(multi)),
            "constant_among_collections_with_ge8_series": int((nunique[big] <= 1).sum()),
            "n_collections_with_ge8_series": int(len(big)),
        }

    # ---------------- (4) cluster bootstrap over collections ----------------
    by_coll = {c: g for c, g in ps.groupby("collection")}
    boot = np.empty(args.n_boot)
    for b in range(args.n_boot):
        pick = rng.choice(collections, size=len(collections), replace=True)
        f = sum(int(by_coll[c]["flips"].sum()) for c in pick)
        p = sum(int(by_coll[c]["pairs"].sum()) for c in pick)
        boot[b] = f / p if p else np.nan
    lo_q = (1 - args.ci_level) / 2
    cluster_ci = [float(np.nanquantile(boot, lo_q)), float(np.nanquantile(boot, 1 - lo_q))]

    series_boot = np.empty(args.n_boot)
    idx_pairs = ps["pairs"].to_numpy()
    idx_flips = ps["flips"].to_numpy()
    for b in range(args.n_boot):
        k = rng.integers(0, len(ps), size=len(ps))
        p = idx_pairs[k].sum()
        series_boot[b] = idx_flips[k].sum() / p if p else np.nan
    series_ci = [float(np.nanquantile(series_boot, lo_q)), float(np.nanquantile(series_boot, 1 - lo_q))]

    # The two-sided rate is the paper's headline number; instrument it the same
    # way as the pooled rate (protocol items 1 and 3).
    joint_instrumented = []
    for thr in JOINT_THRESHOLDS:
        key = f"{thr:.2f}".replace("0.", "")
        nulls = np.empty(args.n_perm)
        for b in range(args.n_perm):
            fl = tot = 0
            for _, _, auc_v, other_v in groups_aff:
                perm = rng.permutation(other_v)
                g1, fp = pairwise_flips(auc_v, perm)
                g2, _ = pairwise_flips(perm, auc_v)
                m = (g1 >= thr) & (g2 >= thr)
                fl += int(fp[m].sum()); tot += int(m.sum())
            nulls[b] = fl / tot if tot else np.nan
        sub = ps[ps[f"pairs_joint{key}"] > 0]
        names_j = sorted(sub["collection"].unique())
        bycj = {c: g for c, g in sub.groupby("collection")}
        cb = np.empty(args.n_boot)
        for b in range(args.n_boot):
            pick = rng.choice(names_j, size=len(names_j), replace=True)
            pp = sum(int(bycj[c][f"pairs_joint{key}"].sum()) for c in pick)
            cb[b] = sum(int(bycj[c][f"flips_joint{key}"].sum()) for c in pick) / pp if pp else np.nan
        joint_instrumented.append({
            "both_at_least": float(thr),
            "random_ranking_null_mean": float(np.nanmean(nulls)),
            "random_ranking_null_sd": float(np.nanstd(nulls, ddof=1)),
            "ci_cluster_over_collections": [float(np.nanquantile(cb, lo_q)),
                                            float(np.nanquantile(cb, 1 - lo_q))],
            "n_collections_with_zero_flips": int(sum(
                1 for c in names_j if int(bycj[c][f"flips_joint{key}"].sum()) == 0)),
            "n_collections": int(len(names_j)),
        })

    payload = {
        "canonical_dir": canonical.name,
        "n_series": int(len(ps)),
        "n_models": int(df["model"].nunique()),
        "n_collections": int(len(collections)),
        "seed": args.seed,
        "saescore_reduction_identity": {
            "definition": "SAEScore = (1 - alpha) * AUC-ROC + alpha * Aff-F1",
            "max_abs_diff_saescore_minus_auc_at_alpha_0": max_err_a0,
            "max_abs_diff_saescore_minus_afff1_at_alpha_1": max_err_a1,
            "note": ("At alpha=0 SAEScore is identically AUC-ROC and at alpha=1 it is identically Aff-F1, "
                     "so alpha-stratified AUC-ROC-vs-SAEScore flip rates interpolate between "
                     "self-comparison and the AUC-ROC-vs-Aff-F1 comparison and are not evidence "
                     "of a structural regime split."),
        },
        "flip_rate": {
            "auc_vs_aff_f1": obs_aff,
            "auc_vs_saescore": obs_sae,
            "random_ranking_null_mean": float(null_rates.mean()),
            "random_ranking_null_sd": float(null_rates.std(ddof=1)),
            "n_perm": int(args.n_perm),
            "agreement_share": 1.0 - obs_aff,
        },
        "gap_stratified": gap_buckets,
        "gap_stratified_secondary": sec_buckets,
        "gap_stratified_joint": joint,
        "gap_stratified_joint_instrumented": joint_instrumented,
        "noise_band_sensitivity": noise_band,
        "predictors": predictors,
        "predictors_two_sided": predictors_joint,
        "identifiability": identifiability,
        "bootstrap_ci": {
            "level": args.ci_level,
            "cluster_over_collections": cluster_ci,
            "resample_series": series_ci,
            "note": "Series resampling understates uncertainty because alpha is near-constant within a collection.",
        },
    }

    out_path.write_text(json.dumps(payload, indent=2))

    # ---------------- summary ----------------
    print(f"Wrote {out_path}\n")
    print(f"series={payload['n_series']}  models={payload['n_models']}  collections={payload['n_collections']}\n")
    print("SAEScore reduction identity (why the alpha-stratified table is not evidence):")
    print(f"  max |SAEScore - AUC-ROC|  at alpha=0 : {max_err_a0:.3e}")
    print(f"  max |SAEScore - Aff-F1|   at alpha=1 : {max_err_a1:.3e}\n")
    print("Flip rate vs null:")
    print(f"  observed AUC-ROC vs Aff-F1 : {obs_aff:.4f}   (metrics agree on {100 * (1 - obs_aff):.1f}% of pairs)")
    print(f"  random-ranking null        : {null_rates.mean():.4f} (sd {null_rates.std(ddof=1):.4f})\n")
    print("Flip rate by |dAUC-ROC| (is disagreement just near-ties?):")
    for b in gap_buckets:
        hi = "inf" if b["hi"] is None else f"{b['hi']:.2f}"
        print(f"  [{b['lo']:.2f}, {hi:>4})  pairs={b['pairs']:6d} ({100 * b['share_of_pairs']:5.1f}%)  flip={b['flip_rate']:.4f}")
    print()
    print("Flip rate by |dAff-F1| (the symmetric check):")
    for b in sec_buckets:
        hi = "inf" if b["hi"] is None else f"{b['hi']:.2f}"
        print(f"  [{b['lo']:.2f}, {hi:>4})  pairs={b['pairs']:6d}  flip={b['flip_rate']:.4f}")
    print()
    print("Flip rate when BOTH metrics separate the pair (the two-sided check):")
    for b in joint:
        print(f"  both margins >= {b['both_at_least']:.2f}:  pairs={b['pairs']:6d} "
              f"({100 * b['share_of_pairs']:4.1f}% of pairs)  flip={b['flip_rate']:.4f}")
    print()
    print("Excluding near-tied pairs:")
    for b in noise_band:
        print(f"  drop |dAUC| < {b['excluded_below']:.2f} : flip={b['flip_rate']:.4f} "
              f"({100 * b['share_retained']:.1f}% of pairs retained)")
    print()
    print(f"{'predictor':<24} {'series rho':>11} {'p':>8} {'coll rho':>10} {'p':>8}   LOCO rho range")
    for name, d in predictors.items():
        s, c, l = d["series_level"], d["collection_level"], d["leave_one_collection_out"]
        print(f"  {name:<22} {s['rho']:+11.4f} {s['perm_p']:>8.4f} {c['rho']:+10.4f} {c['perm_p']:>8.4f}   "
              f"[{l['min_rho']:+.4f}, {l['max_rho']:+.4f}] (worst: drop {l['worst_drop']})")
    print()
    print("Within-collection identifiability:")
    for name, d in identifiability.items():
        print(f"  {name:<22} constant in {d['collections_with_constant_value']}/{d['n_collections']} collections; "
              f"{d['constant_among_collections_with_ge8_series']}/{d['n_collections_with_ge8_series']} of those with >=8 series")
    print()
    print(f"{int(100 * args.ci_level)}% CI on the flip rate:")
    print(f"  cluster bootstrap (collections) : [{cluster_ci[0]:.4f}, {cluster_ci[1]:.4f}]")
    print(f"  series bootstrap                : [{series_ci[0]:.4f}, {series_ci[1]:.4f}]  <- too narrow")


if __name__ == "__main__":
    sys.exit(main())
