"""S14 — lettrine incluse dans la première ligne et le premier mot (L24).

La VT SBB met la lettrine (initiale haute de plusieurs lignes) dans la boîte du
premier mot et de la première ligne (« ES war », « DA der ») ; kraken fait
commencer la ligne après elle. Une composante connexe haute (≥ HMIN × hauteur
médiane des lignes), placée juste à gauche du début d'une ligne et hors de toute
autre ligne, est rattachée à la plus haute des lignes qu'elle recouvre.
"""
import os
import cv2
import numpy as np

HMIN = float(os.environ.get('BBVLM_S14_HMIN', '1.8'))


def detecte(gray, boites):
    """{indice de ligne: boîte de la lettrine}"""
    if not boites: return {}
    _, bw = cv2.threshold(gray, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    n, lab, st, _ = cv2.connectedComponentsWithStats(bw, 8)
    hm = float(np.median([b[3] - b[1] for b in boites]))
    out = {}
    for x, y, w, h, a in st[1:]:
        if not (HMIN * hm <= h <= 8 * hm and .6 * hm <= w <= 4 * hm and h <= 3 * w and a >= .1 * w * h): continue   # pas de filets
        c = (x, y, x + w - 1, y + h - 1)
        cx, cy = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2
        if any(b[0] <= cx <= b[2] and b[1] <= cy <= b[3] for b in boites): continue      # dans une ligne
        cand = [i for i, b in enumerate(boites)
                if b[0] - 1.5 * hm <= c[2] <= b[0] + .5 * hm and min(c[3], b[3]) > max(c[1], b[1])]
        if not cand: continue
        i = min(cand, key=lambda i: boites[i][1])
        if i not in out: out[i] = [int(v) for v in c]
    return out


def union(a, b):
    return [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
