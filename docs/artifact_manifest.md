# Artifact Manifest

## Purpose

This public repository is a curated reproducibility artifact for validating headline findings from:

**When Point Metrics Mislead: Structure-Aware Evaluation Reveals Conditional Ranking Shifts in Time Series Anomaly Detection**

## Included components

- `scripts/validate_tab_rfr_counts.py`  
  Recomputes and validates reported rank-flip counts from canonical derived rows.

- `scripts/compute_tsbad_alpha_stratified_rfr.py`  
  Produces alpha-stratified TSB-AD-M rank-flip summaries from canonical derived rows.

- `scripts/compute_rfr_bootstrap_ci.py`  
  Re-estimates bootstrap confidence intervals for TSB-AD-M rank stability.

- `experiments/results/sae_metrics_canonical.json`  
  Canonical model-dataset metrics used by rank-flip validation.

- `experiments/results/tsbad_scaleup_canonical_0000_0200/`  
  Canonical TSB-AD-M derived summaries and rows used for alpha-stratified and bootstrap checks.

- `experiments/results/bootstrap_rank_ci.json`  
  Precomputed rank bootstrap summary used for optional visualization.

- `docs/index.html` and `docs/assets/`  
  Static project page and figure assets for GitHub Pages.

## Intentionally excluded

- Raw SWaT/WADI and other access-controlled raw datasets.
- Legacy/failed experiments, staging scripts, upload tooling, and private workflow helpers.
- Model training pipelines and full benchmark execution stacks not required for headline verification.
- Venue-specific submission artifacts and internal packaging files.
