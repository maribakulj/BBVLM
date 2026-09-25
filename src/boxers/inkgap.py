"""Plages d'encre + partition par programmation dynamique.

Reprend l'algorithme mesuré dans vlm-alto-fresh : on projette l'encre en
plages horizontales, puis on répartit ces plages en exactement N groupes
contigus, un par mot, en minimisant un coût qui combine l'écart aux largeurs
attendues, le blanc avalé dans un mot, et la coïncidence des frontières avec
les blancs larges.
"""
from __future__ import annotations
import math
import numpy as np
from PIL import ImageFont
import ink

def _font():
    for p in ('/System/Library/Fonts/Supplemental/Times New Roman.ttf',
              '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
              '/System/Library/Fonts/Times.ttc'):
        try: return ImageFont.truetype(p, 100)
        except Exception: continue
    return ImageFont.load_default()

FONT = _font()


def partition(tokens, runs, ews=None):
    N, M = len(tokens), len(runs)
    if not runs or N == 0: return None
    if ews is None:
        ews = np.array([max(1.0, FONT.getlength(t)) for t in tokens], float)
    if M < N:
        left, right = runs[0][0], runs[-1][1]
        sp = np.full(max(0, N-1), FONT.getlength(' '), float)
        tot = ews.sum() + sp.sum(); pos = left; box = []
        for i, w in enumerate(ews):
            wd = (right-left+1)*(w/tot)
            box.append((int(round(pos)), int(round(pos+wd-1)))); pos += wd
            if i < N-1: pos += (right-left+1)*(sp[i]/tot)
        return box
    gaps = [runs[j+1][0]-runs[j][1]-1 for j in range(M-1)]
    bidx = sorted(sorted(range(len(gaps)), key=lambda j: gaps[j], reverse=True)[:N-1])
    groups, j = [], 0
    for b in bidx+[M-1]:
        k = b+1; groups.append((j, k)); j = k
    ratios = [(runs[b-1][1]-runs[a][0]+1)/ew for (a, b), ew in zip(groups, ews)]
    scale = max(.05, min(.6, float(np.median(ratios)) if ratios else .2))
    inf = 1e18
    dp = np.full((N+1, M+1), inf); prev = np.full((N+1, M+1), -1, int); dp[0, 0] = 0
    for i in range(N):
        for j in range(M):
            if dp[i, j] >= inf: continue
            maxk = M-(N-i-1)
            for k in range(j+1, min(maxk, j+23)+1):
                ow = runs[k-1][1]-runs[j][0]+1
                ratio = max(.05, ow/max(1.0, ews[i]*scale))
                cost = dp[i, j] + 2.4*abs(math.log(ratio))
                cost += sum(max(0, g-6)**1.15*0.12 for g in gaps[j:k-1])
                if i < N-1 and k < M: cost += 2.8*math.exp(-max(0, gaps[k-1])/4.0)
                if cost < dp[i+1, k]: dp[i+1, k] = cost; prev[i+1, k] = j
    if not np.isfinite(dp[N, M]): return None
    parts, i, k = [], N, M
    while i > 0:
        j = int(prev[i, k]); parts.append((j, k)); i -= 1; k = j
    parts.reverse()
    return [(runs[j][0], runs[k-1][1]) for j, k in parts]


class InkGapDP:
    name = 'inkgap_dp'

    def boxes(self, gray: np.ndarray, line):
        mask, ox, oy = ink.line_mask(gray, line.line_box)
        s = ink.line_scale(line.line_box)
        runs = ink.x_runs(mask, s['run_area_min'])
        got = partition(line.words, runs)
        if got is None: raise ValueError('dp échoue')
        out = []
        for a, b in got:
            ya, yb = ink.vertical_extent(mask, a, b)
            out.append((ox+a, oy+ya, ox+b, oy+yb))
        return out
