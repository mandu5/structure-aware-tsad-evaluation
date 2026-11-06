"""Copy committed rank and audit artifacts into the static site's publish directory.

No analysis or bootstrap is run. --check verifies bytes against the source records.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = Path("experiments/results/tsbad_scaleup_canonical_0000_0200")


def snapshot() -> str:
    data = {"sources": {}}
    for key, filename in [("retention", "rank_retention.json"), ("robustness", "structure_robustness.json")]:
        path = CANON / filename
        raw = (ROOT / path).read_bytes()
        data[key] = json.loads(raw)
        data["sources"][str(path)] = hashlib.sha256(raw).hexdigest()
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = ROOT / "docs/assets/recorded-ranks.json"
    expected = snapshot()
    if args.check:
        if not target.exists() or target.read_text() != expected:
            raise SystemExit("Site evidence is stale. Run python3 scripts/build_site_data.py")
        print("Site evidence matches rank_retention.json and structure_robustness.json.")
    else:
        target.write_text(expected)
        print(f"Wrote {target.relative_to(ROOT)} from committed artifacts.")
