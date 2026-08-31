# Reproduce the analysis, the manuscript numbers, and the manuscript.
#
#   make            regenerate artifacts, numbers and the PDF
#   make analysis   rerun the analysis scripts
#   make numbers    regenerate paper/numbers.tex from the artifacts
#   make paper      build paper/main.pdf
#   make arxiv      build the de-anonymised preprint + arXiv tarball
#   make verify     tests + prove nothing drifted (what CI runs)

PYTHON ?= python3
CANON  := experiments/results/tsbad_scaleup_canonical_0000_0200

# Pin the timestamp tectonic embeds so an unchanged manuscript rebuilds
# byte-identically and does not show up as a spurious diff.
export SOURCE_DATE_EPOCH ?= 1700000000

.PHONY: all analysis numbers paper arxiv verify test clean

all: paper

analysis:
	$(PYTHON) scripts/compute_structure_robustness.py
	$(PYTHON) scripts/compute_tab_null_and_ties.py

numbers: analysis
	$(PYTHON) scripts/export_paper_numbers.py

paper: numbers
	tectonic -X compile paper/main.tex
	$(PYTHON) scripts/check_anonymity.py

# The preprint arXiv wants is the same source de-anonymised. It builds into
# paper/arxiv/ rather than over paper/main.pdf, which verify pins byte-for-byte
# as the PDF that was submitted. ARXIV_EMAIL overrides the printed contact.
ARXIV_EMAIL ?= ymk5292@psu.edu

arxiv: numbers
	$(PYTHON) scripts/build_arxiv.py --email $(ARXIV_EMAIL)

test:
	$(PYTHON) -m pytest -q

# Regenerating must not change anything that is committed.
verify: test
	$(PYTHON) scripts/validate_tab_rfr_counts.py
	$(PYTHON) scripts/compute_structure_robustness.py
	$(PYTHON) scripts/compute_tab_null_and_ties.py
	git diff --exit-code -- experiments/results
	$(PYTHON) scripts/export_paper_numbers.py
	git diff --exit-code -- paper/numbers.tex
	tectonic -X compile paper/main.tex
	$(PYTHON) scripts/check_anonymity.py
	git diff --exit-code -- paper/main.pdf
	@echo "verify: artifacts, manuscript numbers and PDF are consistent"

clean:
	rm -f paper/*.aux paper/*.log paper/*.blg paper/*.bbl paper/*.out
