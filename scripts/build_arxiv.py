"""Build the de-anonymised preprint arXiv wants, without touching the submission.

``paper/main.pdf`` is pinned byte-for-byte by ``make verify``: it is the file
that went to TMLR, and rebuilding it with the author block revealed would break
that gate and leave the repository unable to prove the submitted PDF is the
committed one. So the preprint is built from a rewritten *copy* of the source in
``paper/arxiv/`` and nothing under ``paper/`` is modified.

Two edits are applied to the copy:

* ``\\usepackage{tmlr}`` gains the ``preprint`` option, which is what makes
  tmlr.sty emit the real author block instead of "Anonymous authors".
* ``\\email`` gets an address. The submission leaves it empty because the block
  is suppressed anyway; a preprint has to carry a contact.

The result is packed as ``arxiv-submission.tar.gz`` containing the source,
because arXiv wants LaTeX rather than a PDF. The ``.bbl`` tectonic produces is
included: arXiv uses a ``.bbl`` when one is present and only runs BibTeX itself
otherwise, so shipping ours pins the bibliography to what was built here.

Usage:
    python3 scripts/build_arxiv.py
    python3 scripts/build_arxiv.py --email you@example.com
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

# Copied verbatim: the vendored stylefiles, the generated macros, the bibliography.
SUPPORT = ("tmlr.sty", "tmlr.bst", "fancyhdr.sty", "numbers.tex", "refs.bib")

# What arXiv needs in the upload. refs.bib is deliberately absent: with main.bbl
# present arXiv skips its own BibTeX pass and uses ours, and shipping both
# invites the two to disagree.
PACKAGE = ("main.tex", "main.bbl", "tmlr.sty", "tmlr.bst", "fancyhdr.sty", "numbers.tex")

ANON_LINE = r"  \usepackage{tmlr}"
PREPRINT_LINE = r"  \usepackage[preprint]{tmlr}"
EMPTY_EMAIL = r"\email \\"


def rewrite(source: str, email: str) -> str:
    """Turn the anonymous submission source into a de-anonymised preprint source."""
    if source.count(ANON_LINE + " ") != 1:
        raise SystemExit(
            f"build_arxiv: expected exactly one uncommented {ANON_LINE.strip()!r} in main.tex. "
            "The stylefile invocation moved; re-read main.tex before trusting this script."
        )
    source = source.replace(ANON_LINE + " ", PREPRINT_LINE + " ", 1)

    if source.count(EMPTY_EMAIL) != 1:
        raise SystemExit(
            f"build_arxiv: expected exactly one empty {EMPTY_EMAIL!r} in main.tex. "
            "The author block changed; fill the address by hand instead."
        )
    return source.replace(EMPTY_EMAIL, rf"\email {email} \\", 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--email",
        default="ymk5292@psu.edu",
        help="contact address printed under the title (default: %(default)s)",
    )
    ap.add_argument("--skip-package", action="store_true", help="build the PDF but skip the tarball")
    args = ap.parse_args()

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    for name in SUPPORT:
        shutil.copy2(PAPER / name, OUT / name)
    (OUT / "main.tex").write_text(
        rewrite((PAPER / "main.tex").read_text(encoding="utf-8"), args.email), encoding="utf-8"
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
