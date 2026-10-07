"""Pack the manuscript source for arXiv.

Since the move to DMLR (single-blind) the manuscript is built with the DMLR
template's own [preprint] option and names its author, so the arXiv version is
the same source: this script copies it into paper/arxiv/, compiles it there so
the .bbl exists, and packs a tarball. paper/main.pdf is never touched.

Both main.bbl and refs.bib ship. arXiv uses a .bbl when present, but a
processor that reruns BibTeX regardless (tectonic does) needs the .bib or it
silently drops the whole bibliography; with both present either behaviour
yields the same bibliography.

Usage:
    python3 scripts/build_arxiv.py
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
OUT = PAPER / "arxiv"

# Copied verbatim: the vendored stylefile, the generated macros, the bibliography.
SUPPORT = ("dmlr2e.sty", "numbers.tex", "refs.bib")

# What goes in the upload. refs.bib is not optional: a processor that reruns
# BibTeX ignores the shipped .bbl, and without the .bib it emits an empty
# bibliography and unresolved citations rather than an error.
PACKAGE = ("main.tex", "main.bbl", "refs.bib", "dmlr2e.sty", "numbers.tex")

PREPRINT_LINE = r"\usepackage[preprint]{dmlr2e}"


def check_source(source: str) -> str:
    """The source must already be the preprint build; nothing is rewritten."""
    if source.count(PREPRINT_LINE) != 1:
        raise SystemExit(
            f"build_arxiv: expected exactly one {PREPRINT_LINE!r} in main.tex; "
            "the stylefile invocation changed, re-read main.tex before trusting this script."
        )
    return source


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--skip-package", action="store_true", help="build the PDF but skip the tarball")
    args = ap.parse_args()

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    for name in SUPPORT:
        shutil.copy2(PAPER / name, OUT / name)
    (OUT / "main.tex").write_text(
        check_source((PAPER / "main.tex").read_text(encoding="utf-8")), encoding="utf-8"
    )

    # --keep-intermediates is what leaves main.bbl behind for the upload.
    subprocess.run(
        ["tectonic", "-X", "compile", "--keep-intermediates", str(OUT / "main.tex")],
        check=True,
    )

    # The preprint is meant to be identified, so this reports rather than gates;
    # it is still worth running to catch a build that silently stayed anonymous.
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_anonymity.py"),
         "--pdf", str(OUT / "main.pdf"), "--allow-identified"],
        check=True,
    )

    missing = [n for n in PACKAGE if not (OUT / n).exists()]
    if missing:
        raise SystemExit(f"build_arxiv: tectonic did not produce {', '.join(missing)}.")

    if not args.skip_package:
        tarball = OUT / "arxiv-submission.tar.gz"
        with tarfile.open(tarball, "w:gz") as tar:
            for name in PACKAGE:
                tar.add(OUT / name, arcname=name)
        print(f"build_arxiv: wrote {tarball.relative_to(ROOT)} ({len(PACKAGE)} files)")

    print(f"build_arxiv: preprint PDF at {(OUT / 'main.pdf').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
