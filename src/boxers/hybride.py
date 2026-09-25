"""B5+B10 — classification des blancs par Otsu, et garde sur les mots courts.

Deux constats de l'itération 2 :

1. **B10** : sur 3516 frontières, seules 22 dépassent 3 caractères, et 55 %
   d'entre elles impliquent un mot de ≤2 caractères. Un mot court offre peu
   d'encre : le coût de largeur du DP y est plat, et la frontière glisse. On
   contraint donc ces mots par leur encre observée plutôt que par un ratio.

2. **Tesseract** rend flous les espaces proches du seuil et tranche après
   reconnaissance. Ici la reconnaissance est déjà faite (le VLM a le texte) :
   on peut donc trancher *avec* le texte. On classe les blancs par Otsu sur
   leur distribution — inter-mot contre intra-mot — et on n'autorise une
   frontière de mot que sur un blanc de la classe haute.
"""
from __future__ import annotations
import math
import numpy as np
import ink
from band import core_band
from inkgap import FONT


def otsu_seuil(v: np.ndarray) -> float:
    """Seuil d'Otsu 1-D sur la distribution des largeurs de blancs."""
    v = np.asarray(v, float)
    if len(v) < 3: return float(v.mean()) if len(v) else 0.0
    lo, hi = v.min(), v.max()
    if hi <= lo: return float(lo)
    best, bt = None, lo
    for t in np.linspace(lo, hi, 48):
        a, b = v[v <= t], v[v > t]
        if len(a) == 0 or len(b) == 0: continue
        s = len(a)*len(b)*(a.mean()-b.mean())**2
        if best is None or s > best: best, bt = s, t
    return float(bt)


def partition_contrainte(tokens, runs, gaps_inter: set[int]):
    """DP identique, mais une frontière de mot ne peut tomber que sur un blanc
    classé inter-mot (sauf s'il n'y en a pas assez — on relâche alors)."""
    N, M = len(tokens), len(runs)
    if not runs or N == 0: return None
    ews = np.array([max(1.0, FONT.getlength(t)) for t in tokens], float)
    if M < N: return None
    gaps = [runs[j+1][0]-runs[j][1]-1 for j in range(M-1)]
    libre = len(gaps_inter) < N-1          # pas assez de blancs francs
    bidx = sorted(sorted(range(len(gaps)), key=lambda j: gaps[j], reverse=True)[:N-1])
    groups, j = [], 0
    for b in bidx+[M-1]:
        k = b+1; groups.append((j, k)); j = k
    ratios = [(runs[b-1][1]-runs[a][0]+1)/ew for (a, b), ew in zip(groups, ews)]
    scale = max(.05, min(.6, float(np.median(ratios)) if ratios else .2))
    INF = 1e18
    dp = np.full((N+1, M+1), INF); prev = np.full((N+1, M+1), -1, int); dp[0, 0] = 0
    for i in range(N):
        for j in range(M):
            if dp[i, j] >= INF: continue
            maxk = M-(N-i-1)
            for k in range(j+1, min(maxk, j+23)+1):
                if i < N-1 and k < M and not libre and (k-1) not in gaps_inter:
                    continue                       # frontière interdite ici
                ow = runs[k-1][1]-runs[j][0]+1
                # mot court : l'encre observée prime sur le ratio de largeur
                poids = 2.4 if len(tokens[i]) > 2 else 1.0
                ratio = max(.05, ow/max(1.0, ews[i]*scale))
                cost = dp[i, j] + poids*abs(math.log(ratio))
                cost += sum(max(0, g-6)**1.15*0.12 for g in gaps[j:k-1])
                if i < N-1 and k < M: cost += 2.8*math.exp(-max(0, gaps[k-1])/4.0)
                if cost < dp[i+1, k]: dp[i+1, k] = cost; prev[i+1, k] = j
    if not np.isfinite(dp[N, M]): return None
    parts, i, k = [], N, M
    while i > 0:
        j = int(prev[i, k]); parts.append((j, k)); i -= 1; k = j
    parts.reverse()
    return [(runs[j][0], runs[k-1][1]) for j, k in parts]


class OtsuGaps:
    name = 'otsu_gaps'

    def boxes(self, gray: np.ndarray, line):
        mask, ox, oy = ink.line_mask(gray, line.line_box)
        a, b = core_band(mask)
        band = mask[a:b+1, :]
        area = max(1, int((b-a+1)*0.10))
        runs = ink.x_runs(band, area) or ink.x_runs(mask, ink.line_scale(line.line_box)['run_area_min'])
        if len(runs) < len(line.words): raise ValueError('trop peu de plages')
        gaps = np.array([runs[j+1][0]-runs[j][1]-1 for j in range(len(runs)-1)], float)
        t = otsu_seuil(gaps)
        inter = {j for j, g in enumerate(gaps) if g > t}
        got = partition_contrainte(line.words, runs, inter)
        if got is None: raise ValueError('dp contraint échoue')
        out = []
        for x0, x1 in got:
            ya, yb = ink.vertical_extent(mask, x0, x1)
            out.append((ox+x0, oy+ya, ox+x1, oy+yb))
        return out
