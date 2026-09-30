"""T05 — blancs d'encre à l'intérieur des mots lus (L40) : un blanc intra-mot aussi large que
les blancs inter-mots de la même ligne signale un espace manquant (mot soudé à la lecture).
Frontières de caractères par alignement forcé CTC (W05) du texte lu, espaces compris."""
import os
import numpy as np
import cv2


def blanc(g, box, x):
    """largeur (px) de la plus longue suite de colonnes sans encre autour de x, dans la bande de la ligne"""
    x0, y0, x1, y1 = (int(v) for v in box)
    c = g[y0:y1, x0:x1]
    t = cv2.threshold(c, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1] > 0
    col = t[int(.2 * t.shape[0]):int(.9 * t.shape[0])].sum(0) == 0     # hors jambages et accents
    k = int(round(x - x0))
    if not (0 <= k < len(col)): return 0
    if not col[k]:
        # frontière posée sur de l'encre : cherche le blanc le plus proche (± 3 px)
        cand = [j for j in range(max(0, k - 3), min(len(col), k + 4)) if col[j]]
        if not cand: return 0
        k = min(cand, key=lambda j: abs(j - k))
    a = b = k
    while a > 0 and col[a - 1]: a -= 1
    while b < len(col) - 1 and col[b + 1]: b += 1
    return b - a + 1


def sonde(g, box, texte):
    """[(indice du caractère après la frontière, blanc px, intra?)] et médiane des blancs inter-mots"""
    from w05 import modele, emissions, encode, viterbi, _code
    m = modele(); lp, sc, rec = emissions(g, box)
    lab, qui = [], []
    for i, ch in enumerate(texte):
        e = (m.codec.encode(' ').tolist() if _code(m, ' ') else []) if ch == ' ' else encode(m, ch)
        lab += e; qui += [i] * len(e)
    if not lab or lp.shape[0] < len(lab): return None
    spans, _ = viterbi(lp, lab)
    deb, fin = {}, {}
    for (a, b), i in zip(spans, qui):
        if a is None: continue
        deb.setdefault(i, a); fin[i] = b
    out = []
    for i in range(1, len(texte)):
        if texte[i] == ' ' or texte[i - 1] == ' ': continue
        if i - 1 in fin and i in deb:
            x = box[0] + sc((fin[i - 1] + 1 + deb[i]) / 2)
            out.append((i, blanc(g, box, x), True))
    inter = []
    for i, ch in enumerate(texte):
        if ch == ' ' and i - 1 in fin and i + 1 in deb:
            x = box[0] + sc((fin[i - 1] + 1 + deb[i + 1]) / 2)
            inter.append(blanc(g, box, x))
    return out, (float(np.median(inter)) if inter else None), inter
