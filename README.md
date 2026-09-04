# tsad-eval — Structure-Aware Evaluation for Time Series Anomaly Detection

[![package-install](https://github.com/mandu5/structure-aware-tsad-evaluation/actions/workflows/package-install.yml/badge.svg)](https://github.com/mandu5/structure-aware-tsad-evaluation/actions/workflows/package-install.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-3670A0?logo=python&logoColor=ffdd54)
![License](https://img.shields.io/badge/license-Apache--2.0-blue)

**Does your anomaly-detection leaderboard survive a change of metric?**

Point-wise scores such as AUC-ROC treat every timestep alike. Segment-aware
scores such as Affiliation-F1 treat a sustained anomaly as one event. On real
industrial benchmarks the two disagree about *which model is better* for roughly
a third of all model pairs — and that disagreement is not a near-tie artifact.
`tsad-eval` gives you the metrics, the rank-flip statistics, the null baseline
and the significance tests to report both views honestly, plus the audited
results for 25 models × 180 series so you can check ours.

> Paper: **When Point Metrics Mislead: Structure-Aware Evaluation Reveals
> Conditional Ranking Shifts in Time Series Anomaly Detection** — Youngmin Ko
> (sole author). Revised after conference review and resubmitted to TMLR
> (under review). Project page: https://tsad-eval-site.onrender.com/

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
| `compute_sae_score(point, segment, alpha)` | SAEScore = (1−α)·point + α·segment, a *reporting composite* (not a leaderboard replacement) |
| `compute_alpha_from_counts(n_short, n_total)` | Structure weight α from the share of short anomaly segments |
| `rank_by_metric(rows, metric_key)` | Dense 1-based ranks per (model, dataset) |
| `wilcoxon_pairwise`, `friedman_test`, `average_ranks`, `build_cd_diagram_data` | Demšar-style multi-model comparison and critical-difference diagram data |

All functions are pure numpy/pandas; nothing reads your datasets.

## Audited results (what you can reproduce)

Headline numbers from the paper, recomputable from the derived outputs shipped
in `experiments/results/` (raw datasets are **not** redistributed — see
[data access](docs/dataset_access.md)). Full tables: [`docs/benchmarks.md`](docs/benchmarks.md).

| Setting | Models × datasets | AUC-ROC vs Aff-F1 flips | Random-ranking null |
|---|---|---|---|
| TAB, deep models only | 5 × 6 | **14 / 60** pairs (23.3%) | 0.500 (2 000 permutations) |
| TAB, deep + classical | 7 × 6 | **44 / 126** pairs (34.9%) | 0.500 |
| TSB-AD-M audit | 25 × 180 series (4 498 rows) | mean per-series RFR **0.343** | 0.500 |

- The metrics *agree* on ~69 % of pairs, so this is disagreement against a
  0.50 chance baseline, not chaos.
- Disagreement is not a tie artifact: RFR falls with the AUC-ROC gap (0.47 for
  gaps < 0.01) but stays at **0.20 for gaps ≥ 0.20**.
- Bootstrap 95 % CI (n = 100, seed 42) for the TSB-AD-M pairwise flip rate
  AUC-ROC vs SAEScore: **0.293 [0.276, 0.312]**.
- Four widely used industrial benchmarks (SWaT, WADI, MSL, SMAP) contain **no
  short anomaly segments** under their processed labels — α = 1.0 — so
  point-wise metrics there are measuring something the benchmarks cannot resolve.
- Series are not independent units: α is constant within 16 of 17 TSB-AD
  collections, and series-level correlations shrink at collection level. We
  report cluster-aware statistics for that reason (`scripts/compute_structure_robustness.py`).

Reproduce the headline numbers (no dataset download needed):

```bash
python scripts/validate_tab_rfr_counts.py            # 14/60, 44/126
python scripts/compute_tsbad_alpha_stratified_rfr.py  # 25 models × 180 series
python scripts/compute_rfr_bootstrap_ci.py --n-boot 100
python scripts/compute_structure_robustness.py        # null, tie sensitivity, cluster-aware
python -m pytest -q tests
```

Or in Docker: `docker build -t tsad-eval . && docker run --rm tsad-eval python scripts/validate_tab_rfr_counts.py`.
See [`docs/reproduction.md`](docs/reproduction.md) for expected outputs.

## Why report both views (and not just switch metrics)

Replacing AUC-ROC with a range-aware metric does not end the problem. Lyu (2026,
[arXiv:2607.11969](https://arxiv.org/abs/2607.11969)) stress-tests post-point-adjustment
metrics with random detectors and finds that under best-of-*N* reporting
Affiliation-F1 and VUS-ROC inflate steeply (Affiliation becomes gameable by
*N* = 3) while PR-based metrics stay near the prevalence baseline. Our audit
shows the complementary failure: point-wise metrics silently reorder models
when anomalies are sustained. The defensible protocol is therefore to **report
point-level and segment-level performance side by side, state the anomaly
structure of the benchmark (α), and test whether the ranking is stable** —
which is what this toolkit automates.

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
  note   = {Under review. Code: https://github.com/mandu5/structure-aware-tsad-evaluation}
}
```

Machine-readable metadata: [`CITATION.cff`](CITATION.cff).

## License

Apache-2.0. See [LICENSE](LICENSE).
