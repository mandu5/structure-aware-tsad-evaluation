"""Contiguous anomaly-segment taxonomy (Short / Medium / Long) from binary labels.

Thresholds match the paper: Short <= 5 steps, Medium 6--50, Long > 50.
"""

from __future__ import annotations

from typing import TypedDict


class TaxonomySummary(TypedDict, total=False):
    Short: int
    Medium: int
    Long: int
    Total: int


def summarize_segments_from_labels(labels: list[int] | object) -> TaxonomySummary:
    """Count anomaly segments by duration bucket.

    Parameters
    ----------
    labels
        1D array-like of 0/1 (or bool) test labels.
    """
    import numpy as np

    arr = np.asarray(labels).astype(np.int8).ravel()
    segs: list[int] = []
    active = False
    start = 0
    for i, v in enumerate(arr):
        if v == 1 and not active:
            start = int(i)
            active = True
        elif v == 0 and active:
            segs.append(int(i - start))
            active = False
    if active:
        segs.append(int(len(arr) - start))

    if not segs:
        return {"Short": 0, "Medium": 0, "Long": 0, "Total": 0}

    counts = {"Short": 0, "Medium": 0, "Long": 0}
    for s in segs:
        if s <= 5:
            counts["Short"] += 1
        elif s <= 50:
            counts["Medium"] += 1
        else:
            counts["Long"] += 1
    counts["Total"] = len(segs)
    return counts  # type: ignore[return-value]
