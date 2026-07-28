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
DEFAULT_CANONICAL = ROOT / "experiments" / "results" / "tsbad_scaleup_canonical_0000_0200"

GAP_EDGES = [0.0, 0.01, 0.02, 0.05, 0.10, 0.20, np.inf]
NOISE_BANDS = [0.01, 0.02, 0.05]


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


# --------------------------------------------------------------------------
# statistics (numpy only; scipy is deliberately not a dependency of this repo)
# --------------------------------------------------------------------------

def _rankdata(a: np.ndarray) -> np.ndarray:
    """Average ranks, matching scipy.stats.rankdata(method='average')."""
    a = np.asarray(a, dtype=float)
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(len(a), dtype=float)
    ranks[order] = np.arange(1, len(a) + 1, dtype=float)
    # average ranks within tie groups
    sorted_a = a[order]
    i = 0
    while i < len(a):
        j = i
        while j + 1 < len(a) and sorted_a[j + 1] == sorted_a[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = ranks[order[i:j + 1]].mean()
        i = j + 1
    return ranks


def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rho = Pearson correlation of average ranks."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3:
        return float("nan")
    rx, ry = _rankdata(x[ok]), _rankdata(y[ok])
    sx, sy = rx.std(), ry.std()
    if sx == 0 or sy == 0:
        return float("nan")
    return float(((rx - rx.mean()) * (ry - ry.mean())).mean() / (sx * sy))


def _spearman_perm_p(x: np.ndarray, y: np.ndarray, n_perm: int, rng: np.random.Generator) -> float:
    """Two-sided permutation p-value for Spearman rho.

    Preferred over the asymptotic p-value here because the collection-level
    tests have n = 17.
    """
    obs = _spearman(x, y)
    if not np.isfinite(obs):
        return float("nan")
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    count = 0
    for _ in range(n_perm):
        if abs(_spearman(x, rng.permutation(y))) >= abs(obs) - 1e-12:
            count += 1
    return float((count + 1) / (n_perm + 1))


# --------------------------------------------------------------------------
# pairwise flip machinery
# --------------------------------------------------------------------------

def _series_pairs(auc: np.ndarray, other: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (auc_gap, flipped) over all non-tied model pairs within one series."""
    n = len(auc)
    if n < 2:
        return np.empty(0), np.empty(0, dtype=bool)
    i, j = np.triu_indices(n, k=1)
    da = auc[i] - auc[j]
    do = other[i] - other[j]
    keep = (da != 0) & (do != 0)
    return np.abs(da[keep]), (np.sign(da[keep]) != np.sign(do[keep]))


def _collect(groups: list[tuple[str, str, np.ndarray, np.ndarray]]) -> dict:
    """Aggregate pairwise stats across series.

    groups: list of (series, collection, auc, other).
    """
    per_series = []
    gaps_all, flip_all = [], []
    for series, collection, auc, other in groups:
        gap, flipped = _series_pairs(auc, other)
        per_series.append({
            "series": series,
            "collection": collection,
            "pairs": int(gap.size),
            "flips": int(flipped.sum()),
            "rfr": float(flipped.mean()) if gap.size else float("nan"),
        })
        gaps_all.append(gap)
        flip_all.append(flipped)
    return {
        "per_series": per_series,
        "gap": np.concatenate(gaps_all) if gaps_all else np.empty(0),
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

    df = pd.read_csv(rows_path)
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
    null_rates = np.empty(args.n_perm)
    for b in range(args.n_perm):
        shuffled = [(s, c, auc, rng.permutation(other)) for s, c, auc, other in groups_aff]
        null_rates[b] = float(_collect(shuffled)["flip"].mean())

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
            loco.append({"dropped": drop, "rho": _spearman(sub[name], sub["rfr"])})
        finite = [d["rho"] for d in loco if np.isfinite(d["rho"])]
        predictors[name] = {
            "series_level": {
                "n": int(len(ps)),
                "rho": _spearman(ps[name], ps["rfr"]),
                "perm_p": _spearman_perm_p(ps[name].to_numpy(), ps["rfr"].to_numpy(), args.n_perm_rho, rng),
            },
            "collection_level": {
                "n": int(len(coll)),
                "rho": _spearman(coll[name], coll["flip_rate"]),
                "perm_p": _spearman_perm_p(coll[name].to_numpy(), coll["flip_rate"].to_numpy(),
                                           args.n_perm_rho, rng),
            },
            "leave_one_collection_out": {
                "min_rho": float(np.min(finite)) if finite else None,
                "max_rho": float(np.max(finite)) if finite else None,
                "worst_drop": min(loco, key=lambda d: abs(d["rho"]) if np.isfinite(d["rho"]) else np.inf)["dropped"],
                "all": loco,
            },
        }

    # within-collection variance of each predictor: is it a series variable at all?
    identifiability = {}
    for name in ["alpha", "mean_segment_duration", "segment_count"]:
        nunique = ps.groupby("collection")[name].nunique()
        sizes = ps.groupby("collection").size()
        big = sizes[sizes >= 8].index
        identifiability[name] = {
            "collections_with_constant_value": int((nunique <= 1).sum()),
            "n_collections": int(len(nunique)),
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
        "noise_band_sensitivity": noise_band,
        "predictors": predictors,
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
