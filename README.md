# tsad-eval — Structure-Aware Evaluation for Time Series Anomaly Detection

[![package-install](https://github.com/mandu5/structure-aware-tsad-evaluation/actions/workflows/package-install.yml/badge.svg)](https://github.com/mandu5/structure-aware-tsad-evaluation/actions/workflows/package-install.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-3670A0?logo=python&logoColor=ffdd54)
![License](https://img.shields.io/badge/license-Apache--2.0-blue)

**Does your anomaly-detection leaderboard survive a change of metric?**

Point-wise scores such as AUC-ROC treat every timestep alike. Segment-aware
scores such as Affiliation-F1 treat a sustained anomaly as one event. On TSB-AD-M
(25 models × 180 series) the two order a model pair differently 31 % of the
time — but the chance level for that statistic is 50 %, not 0 %, and once both
metrics have to separate a pair by a clear margin the disagreement is about
2 %. Most of what gets reported as metric disagreement is agreement plus
near-ties. `tsad-eval` gives you the metrics, the rank-flip statistic with its
chance level, cluster-aware intervals and the significance tests to report both
views honestly, plus the audited results so you can check ours.

> Paper: **When Point Metrics Mislead: Structure-Aware Evaluation Reveals
> Conditional Ranking Shifts in Time Series Anomaly Detection** — Youngmin Ko
> (sole author), conference version. A reframed manuscript that audits this
> statistic (chance level, margin treatment, cluster-aware inference) is under
> review at TMLR; the numbers below come from that audit.
> Project page: https://tsad-eval-site.onrender.com/

## Install

```bash
pip install "tsad-eval[affiliation] @ git+https://github.com/mandu5/structure-aware-tsad-evaluation"
# or, from a clone:
pip install -e ".[affiliation]"
```

`affiliation` pulls in [`prts`](https://github.com/CompML/PRTS) for Affiliation-F1.
Python 3.10+; numpy, pandas, scikit-learn, scipy.

## 60-second demo

```python
import numpy as np
from sklearn.metrics import roc_auc_score
from tsad_eval import compute_affiliation_f1, compute_rank_flip_rate_by_dataset, threshold_by_rate

rows = []
for dataset, (y_true, scores_by_model) in your_runs.items():        # your data
    for model, score in scores_by_model.items():
        pred = threshold_by_rate(score, y_true)                       # threshold at the true anomaly rate
        rows.append({"dataset": dataset, "model": model,
                     "auc_roc": roc_auc_score(y_true, score),          # point-wise
                     "aff_f1": compute_affiliation_f1(y_true, pred)})  # segment-aware

report = compute_rank_flip_rate_by_dataset(rows, metric_a="auc_roc", metric_b="aff_f1")
print(report["mean_rfr_over_datasets_with_pairs"])   # share of model pairs whose order flips
```

A self-contained version with synthetic data is in
[`examples/quickstart.py`](examples/quickstart.py) (`python examples/quickstart.py`).
It builds three toy detectors, scores them on three series with sustained
anomaly segments, and prints the per-series rank-flip rate.

## What is in the box

| Import | What it does |
|---|---|
| `compute_affiliation_f1(labels, preds)` | Affiliation-F1 (Huet et al., 2022) with compatibility across `prts` versions |
| `threshold_by_rate(scores, labels)` | Binarise scores at the ground-truth anomaly rate (the protocol used in the paper) |
| `evaluate(y_true, y_pred, y_proba)` | F1 / ROC-AUC / precision / recall / average precision in one call |
| `compute_rank_flip_rate_by_dataset(rows, metric_a, metric_b)` | Rank-flip rate (RFR): share of comparable model pairs whose ordering differs between two metrics, per dataset and averaged. Ties are excluded from numerator and denominator |
| `compute_sae_score(point, segment, alpha)` | SAEScore = (1−α)·point + α·segment. Kept so the conference-version numbers reproduce; the audit shows it is uninformative by construction at α = 0 and α = 1 (it collapses to one of its inputs), so do not report it as a standalone metric |
| `compute_alpha_from_counts(n_short, n_total)` | Structure weight α from the share of short anomaly segments |
| `rank_by_metric(rows, metric_key)` | Dense 1-based ranks per (model, dataset) |
| `wilcoxon_pairwise`, `friedman_test`, `average_ranks`, `build_cd_diagram_data` | Demšar-style multi-model comparison and critical-difference diagram data |

All functions are pure numpy/pandas; nothing reads your datasets.

## Audited results (what you can reproduce)

Headline numbers from the audit, recomputable from the derived outputs shipped
in `experiments/results/` (raw datasets are **not** redistributed — see
[data access](docs/dataset_access.md)). Every number below is also a macro in
`paper/numbers.tex`, regenerated from the artifacts by `make numbers` and
checked for drift in CI. Full tables: [`docs/benchmarks.md`](docs/benchmarks.md).

**TSB-AD-M — AUC-ROC vs Affiliation-F1, 25 models × 180 series from 17 source collections**

| Statistic | Value |
|---|---|
| Pairwise rank-flip rate, as usually reported | **0.3145** |
| Random-ranking null (the chance level) | 0.5002 |
| … so the two metrics *agree* on | **68.6 %** of pairs |
| Share of pairs that *both* metrics separate by ≥ 0.20 | 13.3 % |
| Flip rate among those confidently separated pairs | **0.0220** |
| 95 % interval, resampling series (treats series as independent) | [0.2979, 0.3312] |
| 95 % interval, clustering over source collections | [0.2695, 0.3715] |

**TAB — 6 datasets.** Deep models only: 14 / 60 pairs flip (0.2333) against a
null of 0.5004; deep + classical: 44 / 126 (0.3492) against 0.5021. The
collection-clustered 95 % interval for the deep-only grid is
**[0.0667, 0.4167]**: six datasets cannot resolve the magnitude.

What the audit found, in order:

- **State the chance level.** A flip rate of 0.31 is not "a third of pairs
  disagree"; against a null of 0.50 it is mostly agreement.
- **Most of the rest is a margin artifact.** Conditioning on the AUC-ROC gap
  alone misleads: pairs with |ΔAUC-ROC| < 0.01 flip at 0.4743 (chance) and
  pairs with |ΔAUC-ROC| ≥ 0.20 still flip at 0.2015 — but those surviving
  flips sit where the *other* metric barely separates the pair. Requiring both
  metrics to separate by ≥ 0.20 leaves 0.0220.
- **Series are not independent units.** The short-anomaly ratio α, the
  covariate usually invoked to explain disagreement, is constant within 11 of
  the 12 collections that contain more than one series: it is a collection
  label. Its rank correlation with the flip rate falls from 0.3241 at series
  level to 0.0563 (p = 0.827) with collections as the unit, and to 0.0898 when
  one collection is removed.
- **What survives.** With collections as the unit, one covariate stands:
  segment count, ρ = −0.6225 (p = 0.008).
- SWaT, WADI, MSL and SMAP contain no short anomaly segments under their
  processed labels (α = 1.0), so an α-stratified analysis cannot be run on them.

Reproduce (no dataset download needed):

```bash
python scripts/compute_structure_robustness.py   # null, margin strata, cluster-aware intervals
python scripts/compute_tab_null_and_ties.py      # TAB null and tie sensitivity
python scripts/validate_tab_rfr_counts.py        # 14/60, 44/126
python scripts/export_paper_numbers.py           # regenerates paper/numbers.tex from the above
python -m pytest -q tests
make verify                                      # all of the above; fails on any drift from the committed artifacts
```

Or in Docker: `docker build -t tsad-eval . && docker run --rm tsad-eval python scripts/validate_tab_rfr_counts.py`.
See [`docs/reproduction.md`](docs/reproduction.md) for expected outputs.

## Why report both views (and not just switch metrics)

Replacing AUC-ROC with a range-aware metric does not end the problem. Lyu (2026,
[arXiv:2607.11969](https://arxiv.org/abs/2607.11969)) stress-tests post-point-adjustment
metrics with random detectors and finds that under best-of-*N* reporting
Affiliation-F1 and VUS-ROC inflate steeply (Affiliation becomes gameable by
*N* = 3) while PR-based metrics stay near the prevalence baseline. Our audit
shows the other half: the disagreement *between* point-level and segment-level
rankings is far smaller than the raw flip rate suggests once the chance level
and the margins are stated, and the structural covariate usually blamed for it
(α) is a property of collections, not of series. The defensible protocol is
therefore to **report point-level and segment-level performance side by side,
state the chance level and the margin at which pairs are compared, and use the
source collection as the unit of inference** — which is what this toolkit
automates.

Related: TSB-AD (Liu & Paparrizos, 2024), VUS (Paparrizos et al., 2022),
Affiliation metrics (Huet et al., 2022), TimeEval (Wenig et al., 2022) for
large-scale execution infrastructure — `tsad-eval` is metric/analysis-side and
composes with it.

## Repository layout

```text
src/evaluation/     # the tsad_eval package (metrics, rank-flip, SAEScore, statistical tests)
src/analysis/       # anomaly-duration taxonomy helper
examples/           # quickstart.py
scripts/            # reproduction scripts for the paper's numbers
experiments/results # derived summaries only (no raw datasets)
docs/               # benchmarks.md, reproduction.md, dataset_access.md, project page
tests/              # pytest suite (25 tests)
paper/              # manuscript sources
```

## Data access

Raw SWaT/WADI and other access-controlled datasets are not redistributed here;
comply with the upstream licences. Details in [`docs/dataset_access.md`](docs/dataset_access.md).

## Citation

```bibtex
@misc{ko2026pointmetrics,
  title  = {When Point Metrics Mislead: Structure-Aware Evaluation Reveals Conditional Ranking Shifts in Time Series Anomaly Detection},
  author = {Ko, Youngmin},
  year   = {2026},
  note   = {Conference version. A reframed audit of this statistic is under review at TMLR. Code: https://github.com/mandu5/structure-aware-tsad-evaluation}
}
```

Machine-readable metadata: [`CITATION.cff`](CITATION.cff).

## License

Apache-2.0. See [LICENSE](LICENSE).
