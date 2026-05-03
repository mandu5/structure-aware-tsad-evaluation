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
pytest -q
```

## Expected headline outputs

- AUC-ROC vs Affiliation-F1 rank flips: 14/60 and 44/126.
- AUC-ROC vs SAEScore rank flips: 8/60 and 36/126.
- TSB-AD-M audit scale: 25 models, 180 multivariate series, 4,498 rows.
- Project page figure assets are served from `docs/assets/`.

## Scope of this public artifact

- Includes: derived summaries, validation scripts, and curated project-page figure assets.
- Excludes: raw SWaT/WADI and other access-controlled raw benchmark data.
- Full training/rerun pipelines require obtaining upstream datasets under their original licenses.
