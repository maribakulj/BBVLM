"""SR — segmentation par reconnaissance guidée par le texte connu (L36).

score(texte, région) = −log p(texte | région) / (nb de caractères + 1), par la perte CTC
du modèle W05 (CATMuS-Print) ; plus bas = la région explique mieux la ligne lue.
"""
import numpy as np


def etiquettes(texte):
    from w05 import modele, encode
    m = modele(); lab = []
    for ch in texte:
        lab += encode(m, ch)
    return lab


def score(gray, box, texte):
    import torch
    from w05 import emissions
    try: lp = emissions(gray, box)[0]
    except Exception: return float('inf')        # région illisible pour le modèle (kraken : net_scale absent)
    lab = etiquettes(texte)
    if not lab or lp.shape[0] < len(lab): return float('inf')
    t = torch.from_numpy(np.ascontiguousarray(lp, dtype=np.float32)).unsqueeze(1)      # (T, 1, C)
    lab_t = torch.tensor([lab], dtype=torch.long)
    L = torch.nn.functional.ctc_loss(t, lab_t, torch.tensor([lp.shape[0]]), torch.tensor([len(lab)]),
                                     blank=0, reduction='sum', zero_infinity=False)
    return float(L) / (len(texte) + 1)


def _meme_bande(a, b):
    return min(a[3], b[3]) - max(a[1], b[1]) >= .5 * min(a[3] - a[1], b[3] - b[1])


def _union(p, q):
    return [min(p[0], q[0]), min(p[1], q[1]), max(p[2], q[2]), max(p[3], q[3])]


def _recouvre(a, b, f=.5):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return ix * iy > f * min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))


def scissions(gray, boites, fh=1.6, creux=.1):
    """boîtes trop hautes (≥ fh × hauteur médiane) coupées à tous les creux profonds du profil
    d'encre horizontal (< creux × max) : chaque bande et chaque suite contiguë de bandes
    (hors la boîte entière), resserrées à l'encre"""
    import cv2
    B = [list(map(int, b)) for b in boites]
    if not B: return []
    hm = float(np.median([b[3] - b[1] for b in B])); out = []
    for b in B:
        h = b[3] - b[1]
        if h < fh * hm: continue
        c = gray[max(0, b[1]):b[3], max(0, b[0]):b[2]]
        if c.size == 0: continue
        t = cv2.threshold(c, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1] > 0
        p = np.convolve(t.sum(1).astype(float), np.ones(5) / 5, mode='same')
        bas = p < creux * p.max()
        coupes, y = [], 0
        while y < h:
            if bas[y]:
                z = y
                while z < h and bas[z]: z += 1
                if 0 < y and z < h: coupes.append((y + z) // 2)
                y = z
            else: y += 1
        bords = [0] + coupes + [h]
        for a in range(len(bords) - 1):
            for e in range(a + 1, len(bords)):
                if a == 0 and e == len(bords) - 1: continue
                y0, y1 = bords[a], bords[e]
                r = np.where(t[y0:y1].any(1))[0]
                if len(r) < 3 or r[-1] - r[0] < .4 * hm: continue
                out.append((b[0], b[1] + y0 + int(r[0]), b[2], b[1] + y0 + int(r[-1]) + 1))
    return list(dict.fromkeys(out))


def candidates(boites, nmax=3, extra=()):
    """boîtes + unions de 2..nmax boîtes voisines d'une même bande (aucune boîte entre elles)
    + candidates supplémentaires (scissions)"""
    B = [list(map(int, b)) for b in boites]
    C = [tuple(b) for b in B] + [tuple(map(int, e)) for e in extra]
    for i, a in enumerate(B):
        chaine, cur = [i], a
        for _ in range(nmax - 1):
            v = [j for j in range(len(B)) if j not in chaine and B[j][0] >= cur[2] - 2 and _meme_bande(cur, B[j])]
            if not v: break
            j = min(v, key=lambda j: B[j][0])
            if any(k not in chaine + [j] and _meme_bande(cur, B[k]) and B[k][0] < B[j][0] and B[k][2] > cur[2] for k in range(len(B))): break
            chaine.append(j); cur = _union(cur, B[j]); C.append(tuple(cur))
    return list(dict.fromkeys(C))


def choisit(gray, textes, boites, tau=4.5):
    """rend {indice texte: boîte choisie} — choix glouton global : paires (ligne lue, candidate)
    triées par score croissant ; une paire est prise si la ligne est libre et la candidate ne
    recouvre aucune candidate déjà prise"""
    import os
    C = candidates(boites, extra=scissions(gray, boites) if os.environ.get('BBVLM_SR_SCINDE', '0') == '1' else ())
    if not textes or not C: return {}
    paires = sorted((s, i, k) for i, t in enumerate(textes) for k, c in enumerate(C)
                    for s in [score(gray, c, t)] if s <= tau)
    res, pris = {}, []
    for s, i, k in paires:
        if i in res or any(_recouvre(C[k], C[k2]) for k2 in pris): continue
        res[i] = C[k]; pris.append(k)
    return res
