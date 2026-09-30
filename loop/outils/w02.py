"""W02 — coupure entre deux mots choisie par Tesseract, bords gardés à l'encre (L25).

Le placeur (DTW seul faute de CTC) coupe parfois dans un petit blanc interne au
mot ; Tesseract situe bien la coupure même si ses boîtes sont lâches (W01,
rejeté, prenait ses bords). Pour chaque frontière dont les deux mots sont
appariés à deux mots Tesseract consécutifs, si notre séparateur n'est pas dans
le blanc Tesseract, la coupure passe au milieu de ce blanc ; les bords sont
recalés sur l'encre, les hauteurs gardées.
"""
import cv2
import numpy as np
from mots_tess import mots_ligne, aligne


def ajuste(gray, box, mots, bs, lang, cache, cle):
    eux = mots_ligne(gray, box, lang, cache, cle)
    if len(eux) < 2 or len(bs) < 2: return bs
    al = aligne(mots, eux)
    x0, y0, x1, y1 = (int(v) for v in box)
    crop = gray[max(0, y0):y1 + 1, max(0, x0):x1 + 1]
    if not crop.size: return bs
    _, bw = cv2.threshold(crop, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    occ = bw.any(axis=0); ox = max(0, x0)
    out = [list(b) for b in bs]
    for k in range(len(out) - 1):
        a, b = al.get(k), al.get(k + 1)
        if a is None or b is None or b != a + 1: continue
        g, d = eux[a][2], eux[b][1]                  # blanc Tesseract [g, d]
        if d <= g: continue
        sep = (out[k][2] + out[k + 1][0]) / 2
        if g <= sep <= d: continue
        s = int(round((g + d) / 2))
        lo, hi = out[k][0] + 1, out[k + 1][2] - 1    # jamais au-delà des mots voisins
        if not lo < s < hi: continue
        cols = np.nonzero(occ[max(0, lo - ox):max(0, s - ox)])[0]
        r = lo + int(cols[-1]) if cols.size else None
        cols = np.nonzero(occ[max(0, s - ox):max(0, hi - ox) + 1])[0]
        l = s + int(cols[0]) if cols.size else None
        if r is None or l is None or r < out[k][0] or l > out[k + 1][2]: continue
        out[k][2], out[k + 1][0] = r, l
    return [tuple(b) for b in out]
