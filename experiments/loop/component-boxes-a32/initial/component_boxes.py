"""Development ink refinement of existing word cells; no recognition or GT input."""
from __future__ import annotations

import cv2
import numpy as np


PARAMETERS = {
    "band_height_fraction": .4,
    "band_start_min_fraction": .15,
    "band_start_max_fraction": .5,
    "min_area_height_squared": .001,
    "core_min_height_fraction": .2,
    "core_min_overlap_fraction": .2,
    "satellite_max_horizontal_gap_fraction": .3,
    "satellite_max_vertical_gap_fraction": .25,
}


def selected_ink(ink: np.ndarray, mode: str) -> tuple[np.ndarray, dict]:
    """Retain whole components, including stems outside the inferred body band.

    The band is a projection heuristic, not a detected baseline. Satellites
    attach only to original core components, never recursively to other noise.
    """
    if mode not in {"area", "body", "satellites"}:
        raise ValueError(mode)
    h, w = ink.shape
    if h == 0 or w == 0:
        return ink.astype(bool), {"empty": True}
    n, labels, stats, _ = cv2.connectedComponentsWithStats((ink > 0).astype("uint8"), 8)
    minimum = max(2, int(np.ceil(PARAMETERS["min_area_height_squared"] * h*h)))
    viable = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= minimum]
    band_h = max(1, round(PARAMETERS["band_height_fraction"] * h))
    mass = (ink > 0).sum(axis=1)
    sums = np.convolve(mass, np.ones(band_h), mode="valid")
    lo = min(len(sums)-1, round(PARAMETERS["band_start_min_fraction"] * h))
    hi = min(len(sums)-1, round(PARAMETERS["band_start_max_fraction"] * h))
    top = lo + int(np.argmax(sums[lo:hi+1]))
    bottom = top + band_h
    core = []
    for i in viable:
        x, y, bw, bh, area = stats[i]
        overlap = max(0, min(y+bh, bottom)-max(y, top))
        if bh >= PARAMETERS["core_min_height_fraction"] * h and overlap >= PARAMETERS["core_min_overlap_fraction"] * bh:
            core.append(i)
    kept = set(viable if mode == "area" else core)
    if mode == "satellites":
        for i in viable:
            if i in kept:
                continue
            x, y, bw, bh, area = stats[i]
            # Punctuation in the body band is not required to be tall.
            if top <= y + bh/2 <= bottom:
                kept.add(i)
                continue
            for j in core:
                cx, cy, cw, ch, _ = stats[j]
                dx = max(0, cx-(x+bw), x-(cx+cw))
                dy = max(0, cy-(y+bh), y-(cy+ch))
                if dx <= PARAMETERS["satellite_max_horizontal_gap_fraction"]*h and dy <= PARAMETERS["satellite_max_vertical_gap_fraction"]*h:
                    kept.add(i)
                    break
    return np.isin(labels, list(kept)), {
        "components": n-1, "kept_components": len(kept), "core_components": len(core),
        "minimum_area": minimum, "body_band": [top, bottom],
        "removed_ink_pixels": int(np.count_nonzero(ink)-np.count_nonzero(np.isin(labels, list(kept)))),
    }


def refine_cells(gray: np.ndarray, line_bbox: list[int], forced: list[list[int]], mode: str):
    x0, y0, x1, y1 = line_bbox
    crop = gray[y0:y1, x0:x1]
    if not crop.size:
        return [list(b) for b in forced], {"fallback_cells": len(forced), "empty": True}
    _, ink = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    mask, diagnostic = selected_ink(ink, mode)
    separators = [x0] + [int(round((a[2]+b[0])/2)) for a, b in zip(forced, forced[1:])] + [x1]
    result, fallback = [], 0
    for i, box in enumerate(forced):
        a, b = max(0, separators[i]-x0), min(crop.shape[1], separators[i+1]-x0)
        ys, xs = np.nonzero(mask[:, a:b]) if b > a else ([], [])
        if len(xs):
            result.append([x0+a+int(min(xs)), y0+int(min(ys)), x0+a+int(max(xs))+1, y0+int(max(ys))+1])
        else:
            # Conservative fallback to unfiltered ink in this same cell.
            ys, xs = np.nonzero(ink[:, a:b]) if b > a else ([], [])
            result.append([x0+a+int(min(xs)), y0+int(min(ys)), x0+a+int(max(xs))+1, y0+int(max(ys))+1] if len(xs) else list(box))
            fallback += 1
    return result, {**diagnostic, "fallback_cells": fallback}
