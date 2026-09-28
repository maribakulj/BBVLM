"""S07 — couper les lignes kraken qui franchissent une gouttière (L13).

Une gouttière (Breuel 2002 ; taquets de Smith 2009) est un blanc vertical
aligné sur plusieurs lignes ; une espace de mot ne l'est pas. Pour chaque
ligne, profil d'encre des colonnes (Otsu sur la ligne) → blancs ≥ LARG·h.
Un blanc est une gouttière s'il chevauche (en x) un blanc ≥ LARG·h d'une
ligne voisine (verticalement adjacente, recouvrement horizontal) ; la ligne
est coupée au milieu de l'intersection, chaque morceau ≥ 2 h et resserré sur
son encre.
"""
import os
import numpy as np, cv2

LARG = float(os.environ.get('BBVLM_GOUT_LARG', '0.5'))   # × hauteur de la ligne elle-même
RAPPORT = float(os.environ.get('BBVLM_GOUT_RAPPORT', '2.0'))  # × espace de mot médiane
BRUIT = float(os.environ.get('BBVLM_GOUT_BRUIT', '0.06'))  # colonne « vide » : encre ≤ BRUIT·h px


def _blancs(gray, b, h):
    x0, y0, x1, y1 = b
    crop = gray[y0:y1+1, x0:x1+1]
    if crop.size == 0: return [], None
    _, bw = cv2.threshold(crop, 0, 1, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    vide = bw.sum(axis=0) <= BRUIT*(y1-y0)
    out, i, n = [], 0, len(vide)
    while i < n:
        if vide[i]:
            j = i
            while j < n and vide[j]: j += 1
            if i > 0 and j < n and j - i >= 0.15*h: out.append((x0+i, x0+j-1))
            i = j
        else: i += 1
    # une gouttière dépasse nettement les espaces de mots de sa ligne
    # (titres espacés, lignes justifiées lâches : blancs tous larges)
    med = float(np.median([z-a+1 for a, z in out])) if out else 0
    return [(a, z) for a, z in out if z-a+1 >= LARG*h and z-a+1 >= RAPPORT*med], bw


def coupe_gouttieres(gray, boites):
    if len(boites) < 2: return boites
    h = float(np.median([b[3]-b[1] for b in boites]))
    B = [list(map(int, b)) for b in boites]
    info = [_blancs(gray, b, b[3]-b[1]) for b in B]
    out = []
    for i, b in enumerate(B):
        coupes = []
        for (a, z) in info[i][0]:
            for j, c in enumerate(B):
                if j == i or c[0] > z or c[2] < a: continue
                # voisine : écart vertical < 1,5 h
                if not (abs(c[1]-b[3]) < 1.5*h or abs(b[1]-c[3]) < 1.5*h or (c[1] < b[3] and b[1] < c[3])): continue
                for (a2, z2) in info[j][0]:
                    u, v = max(a, a2), min(z, z2)
                    if v - u >= 0.3*h: coupes.append((u+v)//2); break
                else: continue
                break
        if not coupes: out.append(b); continue
        bw = info[i][1]; x0, y0 = b[0], b[1]
        bornes = [b[0]] + sorted(set(coupes)) + [b[2]]
        parts = []
        for u, v in zip(bornes, bornes[1:]):
            sub = bw[:, u-x0:v-x0+1]; ys, xs = np.nonzero(sub)
            if len(xs) < 10: continue
            parts.append([int(u+xs.min()), int(y0+ys.min()), int(u+xs.max()), int(y0+ys.max())])
        out += parts if len(parts) >= 2 and all(p[2]-p[0] >= 2*h for p in parts) else [b]
    return out
