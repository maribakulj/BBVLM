"""Détache les manchettes fusionnées par kraken avec la ligne du texte courant.

Constat O07-O09 : la manchette est collée au texte (10-15 px, moins qu'une
espace), aucun blanc ne la sépare. Indice de mise en page : le texte justifié
finit au même bord droit (et commence au même bord gauche). Bords du texte
courant = mode des extrémités des lignes (regroupées à ± une hauteur). Une
ligne qui dépasse nettement un bord est coupée au creux d'encre le plus
profond près de ce bord ; chaque morceau est resserré sur son encre.
"""
import json, sys
import numpy as np, cv2


def mode(vals, tol):
    vals = sorted(vals); best, bestn = None, 0
    for v in vals:
        n = sum(1 for w in vals if abs(w-v) <= tol)
        if n > bestn: best, bestn = v, n
    return best, bestn


def coupe_page(gray, boites):
    if len(boites) < 5: return boites
    h = float(np.median([b[3]-b[1] for b in boites]))
    droit, nd = mode([b[2] for b in boites], h)
    gauche, ng = mode([b[0] for b in boites], h)
    out = []
    for b in boites:
        morceaux = [b]
        if nd >= 5 and b[2] > droit + 1.5*h and b[0] < droit - 3*h:
            morceaux = _coupe(gray, b, droit, h) or morceaux
        res = []
        for m in morceaux:
            if ng >= 5 and m[0] < gauche - 1.5*h and m[2] > gauche + 3*h:
                res += _coupe(gray, m, gauche, h) or [m]
            else:
                res.append(m)
        out += res
    return out


def _coupe(gray, b, x_bord, h):
    x0, y0, x1, y1 = b
    crop = gray[y0:y1+1, x0:x1+1]
    _, bw = cv2.threshold(crop, 0, 1, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    prof = bw.sum(axis=0).astype(float)
    a = int(max(0, x_bord - x0 - .5*h)); z = int(min(len(prof)-1, x_bord - x0 + 2.0*h))
    if z <= a: return None
    # un vrai blanc : ≥ 3 colonnes consécutives sans encre ; on coupe en son milieu
    vide = prof[a:z+1] == 0
    meilleur, run, deb = None, 0, None
    for i, v in enumerate(vide):
        if v:
            run += 1; deb = i if run == 1 else deb
            if run >= 3 and (meilleur is None or run > meilleur[1]): meilleur = (deb, run)
        else:
            run = 0
    if meilleur is None: return None
    xc = a + meilleur[0] + meilleur[1]//2
    parts = []
    for (u, v) in ((0, xc), (xc+1, len(prof)-1)):
        sub = bw[:, u:v+1]
        ys, xs = np.nonzero(sub)
        if len(xs) < 10: continue
        parts.append([int(x0+u+xs.min()), int(y0+ys.min()), int(x0+u+xs.max()), int(y0+ys.max())])
    return parts if len(parts) == 2 else None


if __name__ == '__main__':
    for d in sys.argv[1:]:
        d = d.rstrip('/')
        k = json.load(open(f'{d}/kraken_serre.json')); g = cv2.imread(f'{d}/page.png', cv2.IMREAD_GRAYSCALE)
        nb = coupe_page(g, [l['bbox'] for l in k['lignes']])
        print(d.split('/')[-1][:10], len(k['lignes']), '->', len(nb))
        json.dump({**k, 'lignes': [{'bbox': x} for x in nb]}, open(f'{d}/kraken_coupe.json', 'w'))
