"""W03 — coupure entre mots par le CTC de Calamari (GT4HistOCR), bords à l'encre (L28).

Positions votées des caractères pré-calculées par ligne (DOSSIER/calamari.json,
`cala_page.py`, environnement Calamari séparé). Sans appariement mot à mot (le
texte de Calamari est imparfait) : pour chaque frontière, les blancs d'encre
entre le début du mot k et la fin du mot k+1 sont candidats ; si le blanc de
notre coupure ne contient aucune espace Calamari et qu'un seul autre candidat en
contient une, la coupure y passe (bords recalés sur l'encre, hauteurs gardées).
"""
import cv2
import numpy as np


def blancs(occ):
    """[(début, fin)] des suites de colonnes vides, en coordonnées locales"""
    out, d = [], None
    for i, v in enumerate(occ):
        if not v and d is None: d = i
        if v and d is not None: out.append((d, i - 1)); d = None
    return out


def ajuste(gray, box, bs, cal):
    if not cal or len(bs) < 2: return bs
    x0, y0, x1, y1 = (int(v) for v in box)
    esp = [x0 + g for c, g in zip(cal['s'], cal['g']) if c == ' ']
    if not esp: return bs
    crop = gray[max(0, y0):y1 + 1, max(0, x0):x1 + 1]
    if not crop.size: return bs
    _, bw = cv2.threshold(crop, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    occ = bw.any(axis=0); ox = max(0, x0)
    B = [(a + ox, b + ox) for a, b in blancs(occ)]
    out = [list(b) for b in bs]
    for k in range(len(out) - 1):
        lo, hi = out[k][0] + 1, out[k + 1][2] - 1
        cand = [(a, b) for a, b in B if a > lo and b < hi]
        sep = (out[k][2] + out[k + 1][0]) / 2
        cur = [c for c in cand if c[0] - 1 <= sep <= c[1] + 1]
        avec = [c for c in cand if any(c[0] - 2 <= e <= c[1] + 2 for e in esp)]
        if not avec or (cur and cur[0] in avec) or len(avec) != 1: continue
        a, b = avec[0]
        out[k][2], out[k + 1][0] = a - 1, b + 1
    return [tuple(v) for v in out]


STAT = {'lignes': 0, 'egales': 0, 'deplacees': 0, 'frontieres': 0}


def ajuste_b(gray, box, bs, cal):
    """W03b : espaces Calamari (entrée binarisée) appariées par rang aux
    frontières lues, seulement si leur nombre est égal ; frontière k déplacée
    vers le blanc d'encre qui contient l'espace k, s'il est entre le début du
    mot k et la fin du mot k+1."""
    if not cal or len(bs) < 2: return bs
    x0, y0, x1, y1 = (int(v) for v in box)
    s = cal['s'].strip()
    dec = len(cal['s']) - len(cal['s'].lstrip())
    g = cal['g'][dec:dec + len(s)]
    esp = [x0 + gg for c, gg in zip(s, g) if c == ' ']
    STAT['lignes'] += 1
    if len(esp) != len(bs) - 1: return bs
    STAT['egales'] += 1
    crop = gray[max(0, y0):y1 + 1, max(0, x0):x1 + 1]
    if not crop.size: return bs
    _, bw = cv2.threshold(crop, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    occ = bw.any(axis=0); ox = max(0, x0)
    B = [(a + ox, b + ox) for a, b in blancs(occ)]
    out = [list(b) for b in bs]
    for k, e in enumerate(esp):
        lo, hi = out[k][0] + 1, out[k + 1][2] - 1
        c = [(a, b) for a, b in B if a > lo and b < hi and a - 2 <= e <= b + 2]
        if len(c) != 1: continue
        a, b = c[0]
        STAT['frontieres'] += 1
        STAT['deplacees'] += (out[k][2], out[k + 1][0]) != (a - 1, b + 1)
        out[k][2], out[k + 1][0] = a - 1, b + 1
    return [tuple(v) for v in out]
