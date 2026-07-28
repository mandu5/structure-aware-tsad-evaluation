# Reproduction Guide

This artifact targets lightweight verification of headline paper claims from derived outputs.

## Environment setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional Docker path:

```bash
docker build -t structure-aware-tsad-eval .
docker run --rm structure-aware-tsad-eval
```

## Validation commands

Run from repository root:

```bash
python scripts/validate_tab_rfr_counts.py
python scripts/compute_tsbad_alpha_stratified_rfr.py
python scripts/compute_rfr_bootstrap_ci.py --n-boot 100
python scripts/compute_structure_robustness.py
python scripts/compute_tab_null_and_ties.py
pytest -q
```

## Expected headline outputs

- AUC-ROC vs Affiliation-F1 rank flips: 14/60 and 44/126.
- AUC-ROC vs SAEScore rank flips: 8/60 and 36/126.
- TSB-AD-M audit scale: 25 models, 180 multivariate series, 4,498 rows.
- Project page figure assets are served from `docs/assets/`.

## Robustness re-analysis

`scripts/compute_structure_robustness.py` writes `structure_robustness.json` and
supplies three checks the alpha-stratified analysis did not include.

- **SAEScore reduction identity.** `SAEScore = (1 - alpha) * AUC-ROC + alpha * Aff-F1`,
  so at `alpha = 0` it is identically AUC-ROC and at `alpha = 1` it is identically
  Aff-F1 (both verified to exactly 0 absolute difference). Alpha-stratified
  AUC-ROC-vs-SAEScore flip rates therefore interpolate between a self-comparison
  and the AUC-ROC-vs-Aff-F1 comparison, and are not evidence of a regime split.
- **Random-ranking null.** Observed AUC-ROC vs Aff-F1 flip rate is 0.3145 against a
  permutation null of 0.5002; the metrics agree on 68.6% of model pairs. Flip rates
  must be read against this baseline, not against zero.
- **Tie sensitivity.** Flip rate falls monotonically with the AUC-ROC gap
  (0.474 below 0.01, 0.202 at or above 0.20) but does not vanish: disagreement
  persists among clearly separated models and is not a near-tie artifact.
- **Cluster-aware inference.** `alpha` is constant within 16 of 17 collections, so
  series are not independent units. Series-level Spearman(alpha, flip rate) = +0.324
  collapses to +0.056 at collection level and to +0.090 when TAO is dropped. Mean
  segment duration (+0.372 series, +0.375 collection) and segment count
  (-0.378, -0.412) are stable under leave-one-collection-out. The 95% CI on the flip
  rate is [0.267, 0.371] under a cluster bootstrap over collections versus
  [0.297, 0.332] when resampling series, which understates uncertainty.

`scripts/compute_tab_null_and_ties.py` applies the same treatment to the
six-dataset TAB study and writes `tab_null_and_ties.json`. It reproduces the
headline counts (14/60 and 8/60 on five deep models; 44/126 and 36/126 with
IForest and LOF) and adds:

- **Null.** 14/60 = 0.233 and 44/126 = 0.349 sit against a random-ranking null
  of 0.500. Read against that baseline both describe agreement (76.7% and 65.1%
  of pairs ordered identically), not ranking instability.
- **Model class.** The 60 -> 126 increase consists entirely of pairs involving a
  classical baseline, and those flip at close to chance: deep-deep 14/60 = 0.233,
  deep-classical 27/60 = 0.450, classical-classical 3/6 = 0.500. The higher
  headline number is driven by detectors that rank near-randomly, not by metric
  semantics.
- **Cluster uncertainty.** With six datasets the 95% CI on the deep-model flip
  rate is [0.067, 0.417] clustering over datasets versus [0.133, 0.350] at pair
  level. The study cannot resolve the flip rate to better than that interval.
- **Structure support.** Only PSM (alpha = 0.486) and SMD (alpha = 0.615) have
  alpha < 1, so two of six datasets carry any structure-conditioned claim. Per
  dataset, 11 of the 14 deep-model flips come from PSM (6/10) and SWaT (5/10) --
  and SWaT has alpha = 1.00, the opposite of what the structure account predicts.
- **Tie sensitivity is underpowered here.** Gap-stratified rates are non-monotone
  with 12-19 pairs per bucket; the 180-series TSB-AD snapshot is where this
  check has power.

## Scope of this public artifact

- Includes: derived summaries, validation scripts, and curated project-page figure assets.
- Excludes: raw SWaT/WADI and other access-controlled raw benchmark data.
- Full training/rerun pipelines require obtaining upstream datasets under their original licenses.
