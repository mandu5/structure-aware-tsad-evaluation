"""Tests for contiguous anomaly segment taxonomy helpers."""

from __future__ import annotations

import numpy as np

from src.analysis.taxonomy_segments import summarize_segments_from_labels


def test_summarize_short_medium_long() -> None:
    labels = np.array([0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0], dtype=np.int8)
    # segments: len 3 (short), len 6 (medium), total 2
    s = summarize_segments_from_labels(labels)
    assert s["Short"] == 1
    assert s["Medium"] == 1
    assert s["Long"] == 0
    assert s["Total"] == 2


def test_summarize_empty() -> None:
    s = summarize_segments_from_labels(np.zeros(10, dtype=int))
    assert s["Total"] == 0

