"""Fail if the built manuscript leaks author identity.

TMLR is double blind and states that non-anonymous submissions are rejected
without review. The submission build relies on tmlr.sty suppressing the author
block whenever the ``accepted`` and ``preprint`` options are absent, which is
easy to break by accident -- passing an option, switching stylefile version, or
pasting a repository URL into the text. This turns that assumption into a check.

Note that the repository itself is public and carries the author's name, so the
repository URL and project-page host are treated as identifying strings too.

Usage:
    python3 scripts/check_anonymity.py
    python3 scripts/check_anonymity.py --pdf paper/main.pdf --allow-identified
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = ROOT / "paper" / "main.pdf"

# Strings that must not appear in a double-blind submission.
IDENTIFYING = {
    "Youngmin": "author given name",
    "Pennsylvania State": "affiliation",
    "psu.edu": "institutional email",
    "mandu5": "GitHub handle",
    "structure-aware-tsad": "repository name",
    "tsad-eval-site": "project page host",
}

# Markers tmlr.sty emits only when the author block is correctly suppressed.
REQUIRED = {
    "Anonymous authors": "anonymous author block",
    "double-blind review": "double-blind notice",
}


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Check the built manuscript for anonymity leaks.")
    p.add_argument("--pdf", default=str(DEFAULT_PDF))
    p.add_argument("--allow-identified", action="store_true",
                   help="For camera-ready or preprint builds: skip the required "
                        "anonymous markers but still report identifying strings.")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    pdf = Path(args.pdf)
    if not pdf.exists():
        print(f"check_anonymity: {pdf} not found; build the manuscript first.", file=sys.stderr)
        return 2
    try:
        from pypdf import PdfReader
    except ImportError:
        print("check_anonymity: pypdf is required.", file=sys.stderr)
        return 2

    text = "\n".join((page.extract_text() or "") for page in PdfReader(str(pdf)).pages)
    # Line-wrapping can split a name across lines; compare on collapsed whitespace.
    flat = re.sub(r"\s+", " ", text)

    leaks = [(s, why) for s, why in sorted(IDENTIFYING.items()) if s in flat]
    missing = [] if args.allow_identified else [
        (s, why) for s, why in sorted(REQUIRED.items()) if s not in flat
    ]

    for s, why in leaks:
        print(f"  LEAK    {why}: {s!r} appears in {pdf.name}")
    for s, why in missing:
        print(f"  MISSING {why}: expected {s!r} in {pdf.name}")

    if leaks or missing:
        print(f"\ncheck_anonymity: FAILED ({len(leaks)} leak(s), {len(missing)} missing marker(s)).")
        if missing and not leaks:
            print("The stylefile is probably absent or was passed [accepted]/[preprint]; "
                  "use --allow-identified for those builds.")
        return 1

    print(f"check_anonymity: {pdf.name} is anonymous "
          f"({len(IDENTIFYING)} identifying strings absent, "
          f"{len(REQUIRED)} required markers present).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
