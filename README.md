# Structure-Aware Evaluation for Time Series Anomaly Detection

Public artifact for the paper:

**When Point Metrics Mislead: Structure-Aware Evaluation Reveals Conditional Ranking Shifts in Time Series Anomaly Detection**

Author: Youngmin Ko

TL;DR: Point-wise metrics can change TSAD model rankings when benchmark anomalies are sustained segments rather than isolated spikes.

Project page: https://tsad-eval-site.onrender.com/

## Key findings

- AUC-ROC vs Affiliation-F1 ranking flips: **14/60** (deep-model set), **44/126** (with classical baselines).
- Four audited industrial benchmarks contain no short anomaly segments under processed labels.
- SAEScore is a reporting composite, not a universal leaderboard replacement.
- TSB-AD-M audit scale: 25 models, 180 multivariate series, 4,498 recomputed model-series rows.

## Repository structure

```text
.
├── src/
│   ├── evaluation/               # Metric utilities used by validation
│   └── analysis/                 # Taxonomy helper
├── scripts/
│   ├── validate_tab_rfr_counts.py
│   ├── compute_tsbad_alpha_stratified_rfr.py
│   └── compute_rfr_bootstrap_ci.py
├── experiments/results/          # Derived summaries only (no raw datasets)
├── docs/
│   ├── index.html                # Project page (static site source)
│   ├── reproduction.md
│   ├── dataset_access.md
│   ├── artifact_manifest.md
│   └── assets/
├── tests/                        # Lightweight validation tests
├── requirements.txt
├── Dockerfile
├── CITATION.cff
└── LICENSE
```

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run headline validation:

```bash
python scripts/validate_tab_rfr_counts.py
python scripts/compute_tsbad_alpha_stratified_rfr.py
python scripts/compute_rfr_bootstrap_ci.py --n-boot 100
```

## Reproduction notes

- This public repository is optimized for **derived-output verification** of headline claims.
- Full raw-data reruns require obtaining datasets from their original providers.
- See `docs/reproduction.md` for details and expected outputs.

## Data access policy

Raw SWaT/WADI and other access-controlled raw datasets are not redistributed here.  
Users are responsible for complying with upstream licenses and access terms.

## Project page

The public site is built from `docs/` and deployed on [Render](https://render.com/) as a static site ([live URL](https://tsad-eval-site.onrender.com/)). Blueprint config lives in [`render.yaml`](render.yaml) at the repository root (`runtime: static`, `staticPublishPath: docs`, `SKIP_INSTALL_DEPS=true` so the artifact’s root `requirements.txt` is not installed during deploy).

You can still host the same files with **GitHub Pages** if you prefer: `Settings -> Pages -> Deploy from a branch -> main -> /docs` (mirror of the Render site).

## Citation

If you use this artifact, please cite the paper. GitHub citation metadata is in `CITATION.cff`.

## License

This repository is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.
