"""S10 — blancs de mots vérifiés par l'encre (L21).

La lecture VLM normalise parfois les blancs : « ſolibus » pour l'imprimé
« ſolib us » (écart aussi large qu'entre deux mots, ferrepit), « traher e » pour
« trahere ». Une fois les boîtes de mots placées sur la ligne :
- fusion : deux mots lus séparés par un écart < FUS × l'écart médian entre mots
  de la ligne sont réunis ;
- scission : un mot dont la boîte contient un blanc d'encre ≥ SCI × l'écart
  médian, et ≥ 1,5 × son deuxième plus grand blanc (épargne le texte espacé),
  est coupé ; la position dans le texte suit la position du blanc dans la boîte.
Rien n'est fait sur les lignes de moins de 3 mots (pas d'écart médian fiable).
"""
import os
import cv2
import numpy as np

FUS = float(os.environ.get('BBVLM_BLANCS_FUS', '0'))      # 0,3 : fusions fausses (écarts de boîtes ≠ écarts d'encre)
SCI = float(os.environ.get('BBVLM_BLANCS_SCI', '1.0'))


def _blancs(bw):
    v = bw.sum(0) == 0; runs = []; i = 0
    while i < len(v):
        if v[i]:
            j = i
            while j < len(v) and v[j]: j += 1
            if i > 0 and j < len(v): runs.append((j - i, i, j))
            i = j
        else: i += 1
    return sorted(runs, reverse=True)


def corrige(gray, mots, bs):
    if len(mots) < 3 or len(bs) != len(mots): return mots, bs
    G = [bs[k+1][0] - bs[k][2] - 1 for k in range(len(bs) - 1)]
    g = float(np.median(G))
    if g < 3: return mots, bs
    M, B = [mots[0]], [list(bs[0])]
    for k in range(1, len(mots)):
        if G[k-1] < FUS * g:
            M[-1] += mots[k]; b = B[-1]
            B[-1] = [min(b[0], bs[k][0]), min(b[1], bs[k][1]), max(b[2], bs[k][2]), max(b[3], bs[k][3])]
        else:
            M.append(mots[k]); B.append(list(bs[k]))
    M2, B2 = [], []
    for m, b in zip(M, B):
        x0, y0, x1, y1 = map(int, b)
        crop = gray[y0:y1+1, x0:x1+1]
        if len(m) >= 4 and crop.size:
            _, bw = cv2.threshold(crop, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            r = _blancs(bw)
            if r and r[0][0] >= SCI * g and (len(r) == 1 or r[0][0] >= 1.5 * r[1][0]):
                _, i, j = r[0]
                c = min(len(m) - 1, max(1, round(len(m) * ((i + j) / 2) / max(1, x1 - x0))))
                if not (m[c-1].isalpha() and m[c].isalpha()):     # jamais devant/après une ponctuation (« odor . »)
                    M2.append(m); B2.append(b); continue
                M2 += [m[:c], m[c:]]; B2 += [[x0, y0, x0 + i - 1, y1], [x0 + j, y0, x1, y1]]
                continue
        M2.append(m); B2.append(b)
    return M2, [tuple(b) for b in B2]
