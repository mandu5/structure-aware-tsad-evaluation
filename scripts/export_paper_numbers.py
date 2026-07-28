"""Emit every numeric claim in the manuscript as a LaTeX macro.

The manuscript never hard-codes a number. It inputs ``paper/numbers.tex`` and
refers to macros, so a figure quoted in the text cannot drift from the artifact
it came from: rerunning the analysis scripts and then this exporter updates the
paper. Anything the paper needs that is not derivable from a committed JSON
artifact does not get a macro, which makes such cases obvious.

Usage:
    python3 scripts/export_paper_numbers.py
    python3 scripts/export_paper_numbers.py --output paper/numbers.tex

Reads:
    experiments/results/tsbad_scaleup_canonical_0000_0200/structure_robustness.json
    experiments/results/tsbad_scaleup_canonical_0000_0200/tsbad_alpha_stratified_rfr.json
    experiments/results/tab_null_and_ties.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "experiments" / "results" / "tsbad_scaleup_canonical_0000_0200"
TAB_JSON = ROOT / "experiments" / "results" / "tab_null_and_ties.json"
DEFAULT_OUT = ROOT / "paper" / "numbers.tex"

# LaTeX control sequences may only contain letters.
_DIGIT_WORDS = {"0": "Zero", "1": "One", "2": "Two", "3": "Three", "4": "Four",
                "5": "Five", "6": "Six", "7": "Seven", "8": "Eight", "9": "Nine"}


def _macroname(name: str) -> str:
    out = []
    for ch in name:
        if ch.isdigit():
            out.append(_DIGIT_WORDS[ch])
        elif ch.isalpha():
            out.append(ch)
    return "".join(out)


def _fmt(v: float | int | None, places: int = 4) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, int):
        return f"{v:,}".replace(",", "{,}")
    return f"{v:.{places}f}"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export manuscript numbers as LaTeX macros.")
    p.add_argument("--output", default=str(DEFAULT_OUT))
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    sr = json.loads((CANON / "structure_robustness.json").read_text())
    al = json.loads((CANON / "tsbad_alpha_stratified_rfr.json").read_text())
    tb = json.loads(TAB_JSON.read_text())

    M: dict[str, str] = {}

    # ---------- scale ----------
    M["TsbadSeries"] = _fmt(sr["n_series"])
    M["TsbadModels"] = _fmt(sr["n_models"])
    M["TsbadCollections"] = _fmt(sr["n_collections"])
    M["TsbadRows"] = _fmt(al["n_rows"])
    M["TabDatasets"] = _fmt(tb["n_datasets"])

    # ---------- TSB-AD flip rates and null ----------
    fr = sr["flip_rate"]
    M["TsbadFlipAff"] = _fmt(fr["auc_vs_aff_f1"])
    M["TsbadFlipSae"] = _fmt(fr["auc_vs_saescore"])
    M["TsbadNull"] = _fmt(fr["random_ranking_null_mean"])
    M["TsbadNullSd"] = _fmt(fr["random_ranking_null_sd"])
    M["TsbadNullPerm"] = _fmt(fr["n_perm"])
    M["TsbadAgreePct"] = _fmt(100 * fr["agreement_share"], 1)

    # ---------- TSB-AD gap stratification ----------
    for b in sr["gap_stratified"]:
        lo = f"{b['lo']:.2f}".replace("0.", "").replace(".", "")
        hi = "Inf" if b["hi"] is None else f"{b['hi']:.2f}".replace("0.", "").replace(".", "")
        M[f"TsbadGap{_macroname(lo)}To{_macroname(hi)}"] = _fmt(b["flip_rate"])
        M[f"TsbadGapPairs{_macroname(lo)}To{_macroname(hi)}"] = _fmt(b["pairs"])
        M[f"TsbadGapShare{_macroname(lo)}To{_macroname(hi)}"] = _fmt(100 * b["share_of_pairs"], 1)
    for b in sr["noise_band_sensitivity"]:
        key = _macroname(f"{b['excluded_below']:.2f}".replace("0.", ""))
        M[f"TsbadDrop{key}"] = _fmt(b["flip_rate"])
        M[f"TsbadDropShare{key}"] = _fmt(100 * b["share_retained"], 1)

    # symmetric stratification on the secondary metric's margin
    for b in sr["gap_stratified_secondary"]:
        lo = f"{b['lo']:.2f}".replace("0.", "").replace(".", "")
        hi = "Inf" if b["hi"] is None else f"{b['hi']:.2f}".replace("0.", "").replace(".", "")
        M[f"TsbadSec{_macroname(lo)}To{_macroname(hi)}"] = _fmt(b["flip_rate"])
        M[f"TsbadSecPairs{_macroname(lo)}To{_macroname(hi)}"] = _fmt(b["pairs"])

    # both metrics separate the pair
    for b in sr["gap_stratified_joint"]:
        key = _macroname(f"{b['both_at_least']:.2f}".replace("0.", ""))
        M[f"TsbadJoint{key}"] = _fmt(b["flip_rate"])
        M[f"TsbadJointPairs{key}"] = _fmt(b["pairs"])
        M[f"TsbadJointShare{key}"] = _fmt(100 * b["share_of_pairs"], 1)

    # ---------- TSB-AD predictors ----------
    label = {"alpha": "Alpha", "mean_segment_duration": "Dur", "segment_count": "Nseg",
             "anomaly_density": "Dens", "series_length": "Len"}
    for name, short in label.items():
        d = sr["predictors"][name]
        M[f"Ser{short}Rho"] = _fmt(d["series_level"]["rho"])
        M[f"Ser{short}P"] = _fmt(d["series_level"]["perm_p"])
        M[f"Col{short}Rho"] = _fmt(d["collection_level"]["rho"])
        M[f"Col{short}P"] = _fmt(d["collection_level"]["perm_p"], 3)
        M[f"Loco{short}Min"] = _fmt(d["leave_one_collection_out"]["min_rho"])
        M[f"Loco{short}Max"] = _fmt(d["leave_one_collection_out"]["max_rho"])
        M[f"Loco{short}Worst"] = str(d["leave_one_collection_out"]["worst_drop"])

    # ---------- identifiability ----------
    for name, short in (("alpha", "Alpha"), ("mean_segment_duration", "Dur"), ("segment_count", "Nseg")):
        d = sr["identifiability"][name]
        M[f"Const{short}"] = _fmt(d["collections_with_constant_value"])
        M[f"ConstBig{short}"] = _fmt(d["constant_among_collections_with_ge8_series"])
    M["NBigCollections"] = _fmt(sr["identifiability"]["alpha"]["n_collections_with_ge8_series"])

    # ---------- SAEScore reduction identity ----------
    ident = sr["saescore_reduction_identity"]
    M["IdentAlphaZero"] = _fmt(ident["max_abs_diff_saescore_minus_auc_at_alpha_0"], 1)
    M["IdentAlphaOne"] = _fmt(ident["max_abs_diff_saescore_minus_afff1_at_alpha_1"], 1)

    # ---------- alpha strata (both comparisons) ----------
    for blk, short in (("auc_roc_vs_sae_score", "Sae"), ("auc_roc_vs_aff_f1", "Aff")):
        bins = al[blk]["by_alpha_bin"]
        for key, nm in (("alpha=0", "AZero"), ("0<alpha<1", "AMid"), ("alpha=1", "AOne")):
            M[f"Strat{short}{nm}"] = _fmt(bins[key]["pairwise_flip_rate"])
            M[f"Strat{short}{nm}Flips"] = _fmt(bins[key]["flips"])
            M[f"Strat{short}{nm}Pairs"] = _fmt(bins[key]["comparable_pairs"])
            M[f"Strat{short}{nm}Series"] = _fmt(bins[key]["n_series"])

    # ---------- TSB-AD CIs ----------
    ci = sr["bootstrap_ci"]
    M["TsbadCiClusterLo"] = _fmt(ci["cluster_over_collections"][0])
    M["TsbadCiClusterHi"] = _fmt(ci["cluster_over_collections"][1])
    M["TsbadCiSeriesLo"] = _fmt(ci["resample_series"][0])
    M["TsbadCiSeriesHi"] = _fmt(ci["resample_series"][1])

    # ---------- six-dataset TAB study ----------
    for key, short in (("deep_only__auc_roc_vs_aff_f1", "DeepAff"),
                       ("deep_only__auc_roc_vs_sae_score", "DeepSae"),
                       ("all_models__auc_roc_vs_aff_f1", "AllAff"),
                       ("all_models__auc_roc_vs_sae_score", "AllSae")):
        r = tb["results"][key]
        M[f"Tab{short}Flips"] = _fmt(r["n_flips"])
        M[f"Tab{short}Pairs"] = _fmt(r["n_pairs"])
        M[f"Tab{short}Rate"] = _fmt(r["flip_rate"])
        M[f"Tab{short}Null"] = _fmt(r["random_ranking_null"]["mean"])
        M[f"Tab{short}NullSd"] = _fmt(r["random_ranking_null"]["sd"])
        M[f"Tab{short}AgreePct"] = _fmt(100 * r["agreement_share"], 1)
        M[f"Tab{short}CiClusterLo"] = _fmt(r["ci"]["cluster_over_datasets"][0])
        M[f"Tab{short}CiClusterHi"] = _fmt(r["ci"]["cluster_over_datasets"][1])
        M[f"Tab{short}CiPairLo"] = _fmt(r["ci"]["pair_level"][0])
        M[f"Tab{short}CiPairHi"] = _fmt(r["ci"]["pair_level"][1])

    cls = tb["by_model_class"]["auc_roc_vs_aff_f1"]
    for k, short in (("deep-deep", "DD"), ("deep-classical", "DC"), ("classical-classical", "CC")):
        M[f"Cls{short}Rate"] = _fmt(cls[k]["flip_rate"])
        M[f"Cls{short}Flips"] = _fmt(cls[k]["flips"])
        M[f"Cls{short}Pairs"] = _fmt(cls[k]["pairs"])

    for e in tb["near_random_exclusion"]["auc_roc_vs_aff_f1"]:
        key = _macroname(f"{e['delta']:.2f}".replace("0.", ""))
        M[f"NrRate{key}"] = _fmt(e["flip_rate"])
        M[f"NrFlips{key}"] = _fmt(e["flips"])
        M[f"NrPairs{key}"] = _fmt(e["pairs"])
        M[f"NrDeep{key}"] = _fmt(e["n_deep_excluded"])
        M[f"NrCls{key}"] = _fmt(e["n_classical_excluded"])
        M[f"NrCiLo{key}"] = _fmt(e["ci_cluster_over_datasets"][0])
        M[f"NrCiHi{key}"] = _fmt(e["ci_cluster_over_datasets"][1])

    for ds, a in tb["alpha_by_dataset"].items():
        M[f"Alpha{_macroname(ds)}"] = _fmt(a, 4)
    M["TabAlphaLtOne"] = _fmt(tb["structure_support"]["n_datasets_with_alpha_lt_1"])

    for d in tb["results"]["deep_only__auc_roc_vs_aff_f1"]["per_dataset"]:
        M[f"Deep{_macroname(d['dataset'])}Flips"] = _fmt(d["flips"])
        M[f"Deep{_macroname(d['dataset'])}Pairs"] = _fmt(d["pairs"])

    # per-collection pooled flip rate extremes (TSB-AD)
    per = {}
    for r in al["auc_roc_vs_aff_f1"]["per_series"]:
        c = r["collection"]
        p, f = per.get(c, (0, 0))
        per[c] = (p + r["comparable_pairs"], f + r["flips"])
    rates = {c: f / p for c, (p, f) in per.items() if p}
    lo_c = min(rates, key=rates.get)
    hi_c = max(rates, key=rates.get)
    M["CollMinName"], M["CollMinRate"] = lo_c, _fmt(rates[lo_c])
    M["CollMaxName"], M["CollMaxRate"] = hi_c, _fmt(rates[hi_c])
    # alpha = 1 collections only, to show within-regime spread
    a1 = {c: v for c, v in rates.items()
          if all(r["alpha"] == 1.0 for r in al["auc_roc_vs_aff_f1"]["per_series"] if r["collection"] == c)}
    lo1, hi1 = min(a1, key=a1.get), max(a1, key=a1.get)
    M["AOneCollMinName"], M["AOneCollMinRate"] = lo1, _fmt(a1[lo1])
    M["AOneCollMaxName"], M["AOneCollMaxRate"] = hi1, _fmt(a1[hi1])

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "% Generated by scripts/export_paper_numbers.py -- do not edit by hand.",
        "% Every numeric claim in the manuscript resolves through these macros.",
        "",
    ]
    for k in sorted(M):
        lines.append(f"\\newcommand{{\\{_macroname(k)}}}{{{M[k]}}}")
    out.write_text("\n".join(lines) + "\n")
    print(f"Wrote {out} with {len(M)} macros")


if __name__ == "__main__":
    main()
