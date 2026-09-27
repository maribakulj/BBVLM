"""Cheap continuation merging for conservative visual reading streams."""
from __future__ import annotations

from collections.abc import Mapping, Sequence


Box = tuple[float, float, float, float]


def horizontal_overlap(a: Box, b: Box) -> float:
    """Intersection width divided by the narrower box width."""
    width = min(a[2] - a[0], b[2] - b[0])
    if width <= 0:
        return 0.0
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) / width


def merge_conservative_streams(
    streams: Sequence[Sequence[str]],
    boxes: Mapping[str, Box],
    page_width: float,
    *,
    max_gap_width_ratio: float = 0.007,
    min_horizontal_overlap: float = 0.60,
) -> list[list[str]]:
    """Merge adjacent stream fragments only across a small same-column gap.

    Stream and token order are preserved.  The rule deliberately does not infer
    a new global order: the visual reader supplies that order and the CPU step
    only closes high-confidence typographic continuations.
    """
    if page_width <= 0:
        raise ValueError("page_width must be positive")
    clean = [list(stream) for stream in streams if stream]
    for stream in clean:
        missing = [token for token in stream if token not in boxes]
        if missing:
            raise KeyError(f"missing boxes for tokens: {missing}")
    if not clean:
        return []
    max_gap = max_gap_width_ratio * page_width
    merged = [clean[0]]
    for stream in clean[1:]:
        previous = merged[-1]
        end_box = boxes[previous[-1]]
        start_box = boxes[stream[0]]
        gap = start_box[1] - end_box[3]
        same_column = horizontal_overlap(end_box, start_box) >= min_horizontal_overlap
        if same_column and gap <= max_gap:
            previous.extend(stream)
        else:
            merged.append(stream)
    return merged
