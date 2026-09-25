"""B19 — frontières du CTC, étendue des boîtes donnée par l'encre.

B6 a produit les meilleures frontières du banc — pire cas 0,66c sur le Petit
Parisien, contre 1,32c pour le champion — et le pire IoU : 0,635.

Mesuré sur une ligne : « le » fait 11 px de large contre 29 dans la VT, « Bon »
40 contre 68. Les `cuts` de kraken sont des tranches au centre des caractères,
pas leur étendue ; et mon recalage sur l'encre ne pouvait que **rétrécir** une
boîte, jamais l'élargir.

On change donc le rôle du CTC : il ne donne plus les boîtes, il donne les
**séparateurs**. Chaque boîte couvre ensuite toute l'encre comprise entre deux
séparateurs — exactement ce que fait le champion avec les frontières du DTW.
Le CTC apporte ce qu'il sait faire (placer les coupures), l'encre apporte le
reste (l'étendue).
"""
from __future__ import annotations
import numpy as np
import ink
from ctc import CTCBoxer


class CTCSpan(CTCBoxer):
    name = 'ctc_span'

    def boxes(self, gray: np.ndarray, line):
        brut = super().boxes(gray, line)
        mask, ox, oy = ink.line_mask(gray, line.line_box)
        if mask.size <= 1: return brut
        occ = (mask > 0).any(axis=0)
        W = len(occ)
        # séparateurs = milieux entre deux boîtes CTC consécutives
        sep = [0]
        for i in range(len(brut)-1):
            sep.append(max(0, min(W-1, ((brut[i][2] + brut[i+1][0])//2) - ox)))
        sep.append(W-1)
        out = []
        for i in range(len(brut)):
            a, b = sep[i], sep[i+1]
            if b <= a: b = min(W-1, a+1)
            nz = np.nonzero(occ[a:b+1])[0]
            if len(nz) == 0:
                out.append(brut[i]); continue
            xa, xb = a+int(nz.min()), a+int(nz.max())
            ya, yb = ink.vertical_extent(mask, xa, xb)
            out.append((ox+xa, oy+ya, ox+xb, oy+yb))
        return out
