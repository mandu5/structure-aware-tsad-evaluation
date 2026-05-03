"""Segment-Aware Prediction Smoothing (SAPS).

SAPS is a lightweight post-processing step for binary anomaly predictions.
It uses anomaly-duration priors to:
  1) remove tiny fragmented predicted segments, and
  2) merge close-by anomaly islands into contiguous events.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SAPSConfig:
    """Hyperparameters controlling SAPS post-processing."""

    min_segment_length: int
    merge_gap: int


def _binary_to_segments(binary: np.ndarray) -> list[tuple[int, int]]:
    """Convert a 1D binary array into anomaly segments (start, end-exclusive)."""
    segs: list[tuple[int, int]] = []
    in_seg = False
    start = 0
    for i, v in enumerate(binary):
        if v == 1 and not in_seg:
            start = i
            in_seg = True
        elif v == 0 and in_seg:
            segs.append((start, i))
            in_seg = False
    if in_seg:
        segs.append((start, len(binary)))
    return segs


def _segments_to_binary(length: int, segments: list[tuple[int, int]]) -> np.ndarray:
    """Convert anomaly segments back into a 1D binary prediction array."""
    out = np.zeros(length, dtype=int)
    for s, e in segments:
        out[s:e] = 1
    return out


def _merge_close_segments(
    segments: list[tuple[int, int]], merge_gap: int
) -> list[tuple[int, int]]:
    """Merge adjacent segments when their inter-gap is <= merge_gap."""
    if not segments:
        return []

    merged: list[tuple[int, int]] = [segments[0]]
    for s, e in segments[1:]:
        prev_s, prev_e = merged[-1]
        if s - prev_e <= merge_gap:
            merged[-1] = (prev_s, max(prev_e, e))
        else:
            merged.append((s, e))
    return merged


def apply_saps(predictions: np.ndarray, config: SAPSConfig) -> np.ndarray:
    """Apply SAPS smoothing to binary anomaly predictions.

    Args:
        predictions: Binary 1D array with values in {0, 1}.
        config: SAPS hyperparameter configuration.

    Returns:
        Smoothed binary prediction array.
    """
    preds = np.asarray(predictions).astype(int).ravel()
    if preds.size == 0:
        return preds

    segments = _binary_to_segments(preds)

    # Step 1: remove segments that are shorter than duration prior.
    kept = [
        (s, e)
        for s, e in segments
        if (e - s) >= max(1, int(config.min_segment_length))
    ]

    # Step 2: merge adjacent islands that likely belong to one event.
    merged = _merge_close_segments(kept, max(0, int(config.merge_gap)))
    return _segments_to_binary(len(preds), merged)


def suggest_saps_config_from_lengths(lengths: list[int]) -> SAPSConfig:
    """Suggest SAPS configuration from anomaly segment lengths.

    Heuristic:
      - min_segment_length = max(1, 5% of median GT anomaly length).
        Using a small fraction rather than the GT minimum prevents SAPS from
        over-pruning detectors (e.g. AT, TranAD) whose predictions are shorter
        than the true anomaly duration.  For CATCH-style fragmented outputs the
        merge step already handles coalescing; the min-length filter just
        eliminates isolated 1–2-step noise spikes.
      - merge_gap = max(1, 10% of median GT anomaly length).
        Merges nearby prediction islands that likely belong to one event.
    """
    if not lengths:
        return SAPSConfig(min_segment_length=1, merge_gap=1)

    arr = np.asarray(lengths, dtype=int)
    arr = arr[arr > 0]
    if arr.size == 0:
        return SAPSConfig(min_segment_length=1, merge_gap=1)

    med_len = int(np.median(arr))
    min_segment_length = max(1, round(0.05 * med_len))
    merge_gap = max(1, round(0.10 * med_len))
    return SAPSConfig(min_segment_length=min_segment_length, merge_gap=merge_gap)

