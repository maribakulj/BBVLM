"""B1 — blancs mesurés dans la bande ligne-de-base → ligne-médiane.

Tesseract (Smith, *An Overview of the Tesseract OCR Engine*) mesure les blancs
inter-mots dans une bande verticale limitée, entre ligne de base et ligne
médiane. La raison est géométrique : une hampe (l, h, b) ou un jambage (p, q, g)
du mot voisin traverse le blanc et le comble. Projeter toute la hauteur de la
ligne détruit donc exactement le signal qu'on cherche.

B2 y est joint : les seuils de composantes sont déjà relatifs à la hauteur de
ligne, mais à 15 px de haut (BNL) l'érosion implicite d'Otsu emporte les
lettres fines. On abaisse le plancher d'aire et on n'exige plus qu'une
composante soit « forte » pour être gardée quand la ligne est basse.
"""
from __future__ import annotations
import numpy as np
import ink
from inkgap import partition


def core_band(mask: np.ndarray, frac: float = 0.55) -> tuple[int, int]:
    """Bande dense = corps des minuscules. Lignes dont la densité d'encre
    dépasse `frac` du maximum lissé."""
    if mask.size <= 1: return 0, max(0, mask.shape[0]-1)
    prof = (mask > 0).sum(axis=1).astype(float)
    if prof.max() <= 0: return 0, mask.shape[0]-1
    k = max(1, mask.shape[0]//12)
    ker = np.ones(k)/k
    sm = np.convolve(prof, ker, mode='same')
    thr = sm.max()*frac
    rows = np.where(sm >= thr)[0]
    if len(rows) < 2: return 0, mask.shape[0]-1
    return int(rows.min()), int(rows.max())


class BandGaps:
    name = 'band_gaps'

    def boxes(self, gray: np.ndarray, line):
        mask, ox, oy = ink.line_mask(gray, line.line_box)
        s = ink.line_scale(line.line_box)
        a, b = core_band(mask)
        band = mask[a:b+1, :]
        # plages calculées DANS LA BANDE, seuil d'aire proportionnel à sa hauteur
        area = max(1, int((b-a+1)*0.10))
        runs = ink.x_runs(band, area)
        if not runs:
            runs = ink.x_runs(mask, s['run_area_min'])
        got = partition(line.words, runs)
        if got is None: raise ValueError('dp échoue')
        out = []
        for x0, x1 in got:
            ya, yb = ink.vertical_extent(mask, x0, x1)   # étendue sur le masque COMPLET
            out.append((ox+x0, oy+ya, ox+x1, oy+yb))
        return out
