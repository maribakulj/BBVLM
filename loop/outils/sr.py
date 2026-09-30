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


def candidates(boites, nmax=3):
    """boîtes + unions de 2..nmax boîtes voisines d'une même bande (aucune boîte entre elles)"""
    B = [list(map(int, b)) for b in boites]
    C = [tuple(b) for b in B]
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
    """rend {indice texte: boîte choisie} — affectation globale sans chevauchement"""
    from scipy.optimize import linear_sum_assignment
    C = candidates(boites)
    T = [t for t in textes]
    if not T or not C: return {}
    M = np.array([[score(gray, c, t) for c in C] for t in T])
    M = np.where(np.isfinite(M), M, 1e6)
    interdit = set(); res = {}
    for _ in range(10):
        X = M.copy()
        for (i, k) in interdit: X[i, k] = 1e6
        ri, ki = linear_sum_assignment(X)
        paires = sorted([(X[i, k], i, k) for i, k in zip(ri, ki) if X[i, k] <= tau])
        res, pris, conflit = {}, [], False
        for s, i, k in paires:
            if any(_recouvre(C[k], C[k2]) for k2 in pris):
                interdit.add((i, k)); conflit = True; continue
            res[i] = C[k]; pris.append(k)
        if not conflit: break
    return res
