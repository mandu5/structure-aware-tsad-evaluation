# Benchmark tables (derived from `experiments/results/`)

All numbers below are recomputed from the shipped derived outputs; run the scripts in the README to regenerate.

## TAB benchmark — AUC-ROC vs Affiliation-F1 rank flips

| Subset | Models | Pairs | Flips | Flip rate | Random-ranking null (mean ± sd) |
|---|---|---|---|---|---|
| Deep models only | 5 | 60 | 14 | 0.233 | 0.500 ± 0.084 |
| Deep models only (AUC-ROC vs SAEScore) | 5 | 60 | 8 | 0.133 | 0.502 ± 0.083 |
| Deep + classical | 7 | 126 | 44 | 0.349 | 0.502 ± 0.064 |
| Deep + classical (AUC-ROC vs SAEScore) | 7 | 126 | 36 | 0.286 | 0.499 ± 0.064 |

Per-dataset α (share of non-short segments; 1.0 = no short anomalies): MSL 1.0, PSM 0.4861, SMAP 1.0, SMD 0.6147, SWaT 1.0, WADI 1.0

## TSB-AD-M audit — 25 models × 180 multivariate series

- Metric rows: 4498  ·  models: 25  ·  series with α < 1: 27
- Mean per-series RFR, AUC-ROC vs Aff-F1: **0.343**
- Overall pairwise flip rate, AUC-ROC vs SAEScore: **0.293** (95% bootstrap CI 0.276–0.312, n_boot=100, seed=42)

### Per collection (AUC-ROC vs Aff-F1)

| Collection | Series | Comparable pairs | Flips | Flip rate |
|---|---|---|---|---|
| GHL | 23 | 2917 | 1714 | 0.588 |
| CATSv2 | 5 | 1493 | 589 | 0.395 |
| Genesis | 1 | 222 | 86 | 0.387 |
| PSM | 1 | 300 | 116 | 0.387 |
| SMAP | 25 | 6730 | 2483 | 0.369 |
| SWaT | 2 | 600 | 218 | 0.363 |
| MITDB | 11 | 3230 | 1121 | 0.347 |
| MSL | 14 | 3729 | 1268 | 0.340 |
| CreditCard | 1 | 282 | 92 | 0.326 |
| Exathlon | 25 | 7500 | 2226 | 0.297 |
| SVDB | 28 | 8344 | 2415 | 0.289 |
| OPPORTUNITY | 7 | 1765 | 460 | 0.261 |
| SMD | 20 | 5996 | 1561 | 0.260 |
| LTDB | 4 | 1194 | 264 | 0.221 |
| Daphnet | 1 | 299 | 56 | 0.187 |
| GECCO | 1 | 300 | 52 | 0.173 |
| TAO | 11 | 3279 | 430 | 0.131 |

Models scored: AT, AutoEncoder, CBLOF, CNN, COPOD, Donut, EIF, FITS, HBOS, IForest, KMeansAD, KNN, LOF, LSTMAD, MCD, OCSVM, OFA, OmniAnomaly, PCA, PatchTST, RobustPCA, TimesNet, TranAD, USAD, xLSTMAD

Source files: `tsbad_rfr_auc_vs_aff.json`, `tsbad_scaleup_summary.json`, `rfr_bootstrap_ci.json`, `tab_null_and_ties.json`, `tsbad_sae_rows.csv` (4 498 rows).
