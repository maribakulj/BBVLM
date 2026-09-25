"""Extraction du masque d'encre d'une ligne, à l'échelle de la ligne.

Leçon d'un échec : calibrer l'échelle globalement (autocorrélation sur la page)
a donné un pas de 11 px sur un in-folio dont les lignes font 230 px. La boîte de
ligne donne l'échelle directement et sans détour — on s'en sert.
"""
from __future__ import annotations
import cv2
import numpy as np


def line_scale(line_box) -> dict:
    x0, y0, x1, y1 = line_box
    h = max(4, y1 - y0)
    return {
        'h': h,
        'sigma': max(2.0, h * 0.45),      # fond à diviser ~ hauteur de ligne
        'cc_h_max': int(h * 1.30),
        'cc_h_min': max(1, int(h * 0.04)),
        'cc_w_max': int(h * 4.0),
        'cc_area_min': max(3, int((h * 0.06) ** 2)),
        'run_area_min': max(2, int(h * 0.10)),
        'rule_w': max(2, int(h * 0.05)),
    }


def line_mask(gray: np.ndarray, line_box, pad: float = 0.12) -> tuple[np.ndarray, int, int]:
    """Masque binaire des glyphes. Rend (masque, x_offset, y_offset)."""
    H, W = gray.shape
    x0, y0, x1, y1 = line_box
    s = line_scale(line_box)
    dy = int(s['h'] * pad)
    ax0, ay0 = max(0, x0), max(0, y0 - dy)
    ax1, ay1 = min(W, x1), min(H, y1 + dy)
    if ax1 - ax0 < 4 or ay1 - ay0 < 4:
        return np.zeros((1, 1), np.uint8), ax0, ay0
    crop = gray[ay0:ay1, ax0:ax1]
    blur = cv2.GaussianBlur(crop, (0, 0), s['sigma'])
    norm = cv2.divide(crop, blur, scale=255)
    _, bw = cv2.threshold(norm, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    n, lab, st, _ = cv2.connectedComponentsWithStats(bw, 8)
    keep = np.zeros_like(bw)
    cy = (ay0 + ay1) / 2 - ay0
    strong = []
    cand = []
    for k in range(1, n):
        x, y, w, h, a = (int(st[k, i]) for i in range(5))
        if not (a >= s['cc_area_min'] and h >= s['cc_h_min']
                and h <= s['cc_h_max'] and w <= s['cc_w_max']):
            continue
        if abs((y + h/2) - cy) > s['h'] * 0.85:
            continue
        if (x <= 1 or x + w >= bw.shape[1] - 1) and w <= s['rule_w'] and h > s['h'] * 0.6:
            continue                               # filet de colonne
        cand.append((k, x, y, w, h, a))
        if h >= s['h'] * 0.22 and a >= s['cc_area_min'] * 3:
            strong.append((x, y, w, h))
    ks = set()
    for k, x, y, w, h, a in cand:
        if h >= s['h'] * 0.22 and a >= s['cc_area_min'] * 3:
            ks.add(k); continue
        for sx, sy, sw, sh in strong:            # accents, points, apostrophes
            if max(0, max(sx-(x+w), x-(sx+sw))) <= s['h']*0.22 and \
               abs((y+h/2)-(sy+sh/2)) <= s['h']*0.75:
                ks.add(k); break
    for k in ks:
        keep[lab == k] = 255
    return keep, ax0, ay0


def x_runs(mask: np.ndarray, min_area: int) -> list[tuple[int, int, int]]:
    """Plages d'encre : intervalles maximaux en x contenant de l'encre."""
    if mask.size <= 1:
        return []
    occ = (mask > 0).any(axis=0)
    out, st = [], None
    for x, v in enumerate(occ):
        if v and st is None:
            st = x
        elif not v and st is not None:
            a = int((mask[:, st:x] > 0).sum())
            if a >= min_area: out.append((st, x-1, a))
            st = None
    if st is not None:
        a = int((mask[:, st:] > 0).sum())
        if a >= min_area: out.append((st, mask.shape[1]-1, a))
    return out


def vertical_extent(mask: np.ndarray, a: int, b: int) -> tuple[int, int]:
    sub = mask[:, max(0, a):b+1]
    rows = np.where((sub > 0).any(axis=1))[0]
    if not len(rows): return 0, mask.shape[0]-1
    return int(rows.min()), int(rows.max())
