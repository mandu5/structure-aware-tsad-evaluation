# Rank explorer implementation

The selected A rank-crossing scene is implemented directly in the existing
static `docs/index.html`. Render still serves `docs/` with the same `true` build
command; hosting settings were not changed. The public page is
<https://tsad-eval-site.onrender.com/> and follows the repository's `main` branch.

## Preview and evidence refresh

```sh
python3 scripts/build_site_data.py --check
python3 -m http.server 19307 --bind 127.0.0.1 --directory docs
```

Open <http://127.0.0.1:19307/>. The site reads `assets/recorded-ranks.json`,
packaged from committed `rank_retention.json` and `structure_robustness.json`
in `experiments/results/tsbad_scaleup_canonical_0000_0200/`. The package stores
source SHA-256 hashes. `python3 scripts/build_site_data.py` refreshes it without
running an analysis, bootstrap, detector, or model call. Review the source
artifact changes before accepting any resulting site-data diff.

## Interpretation

- Curves show the 25 aggregate model ranks by mean score over 180 series.
  CNN moves from AUC-ROC rank 1 to Affiliation-F1 rank 6. USAD moves from 3 to 1.
- The 31.4% headline is the recorded 0.31446658364466584 within-series pairwise
  flip rate. It is not a rate computed from the aggregate curves. The random
  null remains 0.5001820972845061, displayed as 50.0%.
- Selecting a curve shows both mean scores and the stored rank intervals.
  Swapping metrics reverses the comparison, preserving the selected model.
- The accessible rank table has both metric controls, exact mean scores, stored
  rank intervals, and retention frequencies. The 10,000 collection resamples
  are existing recorded results; selecting a control does not resample data.
- Rank retention is a supplementary repository artifact, separate from the
  manuscript numbers. Rank intervals are not pairwise significance tests.

The complete pre-existing study text, protocol, chance baseline, margin
analysis, composite-metric caveat, data-access restriction, reproduction
command and both citations are retained. Existing `#cite`, document paths,
assets and source links remain available. Added anchors are `#findings`,
`#rank-records`, `#study`, `#chance`, `#near-ties`, `#collections`, `#our-metric`,
`#protocol` and `#reproduce`.

## Design and font provenance

This implements the A scene selected on 2026-11-06 from the local Design Studio
study `design-studio-20261106/tsad.html?dir=a` (`src/upgraded-scenes.js` / `.css`).
It is native HTML, CSS, SVG and JavaScript, without the study shell or an iframe.

Design Studio's starter and reference studies originated in company design
work. The user confirmed personal-project reuse review/approval on 2026-11-05.
That provenance is retained; the source design bundle is not being relicensed
under this project's Apache-2.0 license. No company data or proprietary
fonts are included. Research data and claims are from this repository.

Pretendard and Archivo are served locally with their original SIL Open Font
License files in `assets/fonts/`. The Latin/common-glyph subset and Archivo
variable font were carried from the selected study. There are no external
JavaScript or font requests.
