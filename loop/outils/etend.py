"""S09 — lignes courtes à éléments espacés complétées par l'encre (L19).

Kraken ne détecte parfois qu'un fragment d'une ligne courte aux éléments très
espacés (folio « ) 152 ( », titre « j. Jsop », « §.VI. ») : la ligne de
référence n'a alors aucune ligne appariée (IoU < 0,5). Pour chaque boîte courte
(largeur < COURT·h), on ajoute de proche en proche les composantes connexes
dont le centre est dans la bande verticale de la ligne, de hauteur ≤ 1,6 h,
à moins de ECART·h horizontalement, et qui ne touchent aucune autre ligne ;
la boîte étendue ne doit chevaucher aucune autre ligne de sa bande.
"""
import os
import cv2
import numpy as np

COURT = float(os.environ.get('BBVLM_ETEND_COURT', '6'))
ECART = float(os.environ.get('BBVLM_ETEND_ECART', '2'))


def etend(gray, boites):
    if not boites: return boites
    _, bw = cv2.threshold(gray, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    n, lab, st, _ = cv2.connectedComponentsWithStats(bw, 8)
    hm = float(np.median([b[3] - b[1] for b in boites]))
    cc = [(x, y, x + w - 1, y + h - 1) for x, y, w, h, a in st[1:] if a >= 6 and float(os.environ.get('BBVLM_ETEND_HMIN', '0.35')) * hm <= h <= 1.6 * hm and w <= 8 * hm and h <= 4 * w]   # lettres ; ni filets, ni tirets ornementaux (« — 14 — », dalarie), ni poussières
    def touche(c, b, m=2):
        return c[0] <= b[2] + m and c[2] >= b[0] - m and c[1] <= b[3] + m and c[3] >= b[1] - m
    out = [list(map(int, b)) for b in boites]
    for i, b in enumerate(out):
        h = b[3] - b[1]
        if b[2] - b[0] >= COURT * h: continue
        autres = [o for j, o in enumerate(out) if j != i]
        cand = [c for c in cc if b[1] <= (c[1] + c[3]) / 2 <= b[3] and not any(touche(c, o) for o in autres)]
        ch = True
        while ch:
            ch = False
            for c in cand:
                if c[0] >= b[0] and c[2] <= b[2]: continue
                gap = max(c[0] - b[2], b[0] - c[2])
                if gap > ECART * h: continue
                nb = [min(b[0], c[0]), min(b[1], c[1]), max(b[2], c[2]), max(b[3], c[3])]
                # garde-fou (hackherz) : ne pas avancer sous une autre ligne de la même bande
                if any(min(nb[2], o[2]) > max(nb[0], o[0]) and min(nb[3], o[3]) - max(nb[1], o[1]) > .3 * h for o in autres):
                    continue
                b[:] = nb; ch = True
    return out
