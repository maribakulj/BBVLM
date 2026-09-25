"""B11 — DTW gabarit + recalage des boîtes sur l'encre observée.

B3 place les frontières remarquablement bien (pire cas 2,25c contre 5,93c) mais
son IoU plafonne à 0,789 : les intervalles viennent des avances de la fonte
rendue, approches latérales comprises, et débordent donc l'encre réelle du mot.

On garde les frontières du DTW — c'est ce qu'il fait le mieux — et on rétracte
chaque boîte sur l'encre effectivement présente dans son intervalle, sans jamais
franchir une frontière voisine.
"""
from __future__ import annotations
import numpy as np
import ink
from dtw import RenderDTW


class DTWSnap(RenderDTW):
    name = 'dtw_snap'

    def boxes(self, gray: np.ndarray, line):
        brut = super().boxes(gray, line)
        mask, ox, oy = ink.line_mask(gray, line.line_box)
        if mask.size <= 1: return brut
        occ = (mask > 0).any(axis=0)
        out = []
        for (x0, y0, x1, y1) in brut:
            a, b = x0-ox, x1-ox
            a = max(0, min(len(occ)-1, a)); b = max(0, min(len(occ)-1, b))
            seg = occ[a:b+1]
            nz = np.nonzero(seg)[0]
            if len(nz) == 0:                       # aucun pixel d'encre : on garde
                out.append((x0, y0, x1, y1)); continue
            na, nb = a+int(nz.min()), a+int(nz.max())
            ya, yb = ink.vertical_extent(mask, na, nb)
            out.append((ox+na, oy+ya, ox+nb, oy+yb))
        return out
