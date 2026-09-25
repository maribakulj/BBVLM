"""B23 — l'étendue verticale vient du profil d'encre, pas de la boîte déclarée.

B22 bornait la hauteur des boîtes à la boîte de ligne. Insuffisant sur Newseye :
mesuré, ses boîtes de lignes font **1,5 fois la hauteur des mots** (43 px contre
27) et **28 lignes sur 40 se chevauchent verticalement**. Épouser la boîte
revient donc encore à capter l'encre des lignes voisines — les boîtes restent
1,30× trop hautes sur une des pages.

La boîte de ligne est une déclaration, le profil d'encre est une observation. On
prend donc la seconde : on projette l'encre en lignes, on cherche la région
dense **contiguë autour du centre**, et on s'arrête au premier creux franc de
part et d'autre. L'encre d'une ligne voisine forme un pic séparé par un creux :
elle tombe d'elle-même hors de la région retenue.

C'est le même principe que B1 (Tesseract, blancs mesurés dans une bande
verticale limitée), appliqué cette fois à la hauteur des boîtes.
"""
from __future__ import annotations
import numpy as np
import ink
from compose import Compose


def bande_propre(mask: np.ndarray, creux: float = 0.18) -> tuple[int, int]:
    """Région d'encre contiguë autour du centre, arrêtée aux creux francs."""
    if mask.size <= 1: return 0, max(0, mask.shape[0]-1)
    prof = (mask > 0).sum(axis=1).astype(float)
    if prof.max() <= 0: return 0, mask.shape[0]-1
    k = max(1, mask.shape[0]//16)
    sm = np.convolve(prof, np.ones(k)/k, mode='same')
    c = int(np.argmax(sm))                       # le pic le plus fort = notre ligne
    seuil = sm[c]*creux
    a = c
    while a > 0 and sm[a-1] > seuil: a -= 1
    b = c
    while b < len(sm)-1 and sm[b+1] > seuil: b += 1
    return a, b


class Profil:
    name = 'profil'

    def __init__(self):
        self.base = Compose()

    def boxes(self, gray: np.ndarray, line):
        brut = self.base.boxes(gray, line)
        mask, ox, oy = ink.line_mask(gray, line.line_box, pad=0.10)
        if mask.size <= 1: return brut
        ha, hb = bande_propre(mask)               # bornes propres à CETTE ligne
        out = []
        for (x0, y0, x1, y1) in brut:
            a = max(0, min(mask.shape[1]-1, x0-ox))
            b = max(0, min(mask.shape[1]-1, x1-ox))
            sub = mask[ha:hb+1, a:b+1]
            rows = np.where((sub > 0).any(axis=1))[0]
            if len(rows) == 0:
                out.append((x0, oy+ha, x1, oy+hb)); continue
            out.append((x0, oy+ha+int(rows.min()), x1, oy+ha+int(rows.max())))
        return out
