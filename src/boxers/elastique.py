"""B16 — espaces élastiques : le gabarit ne décide plus de la largeur des vides.

L'overlay de BNL 0015 montre pourquoi B12 et B15 échouaient. Une ligne de
tableau — `Luxembourg 141 Dép...... fr. 12315 31` — a des blancs **inégaux
entre eux** : large après le nom de commune, étroit entre deux chiffres. Un
`space_ratio` scalaire, même estimé sur l'observé, impose un vide uniforme : il
ne peut correspondre qu'à un seul des blancs réels.

Correction structurelle : on rend le texte avec des espaces **minimaux** et on
élargit la bande de Sakoe-Chiba. Le vide du gabarit et le vide de l'image sont
tous deux sans encre ; le chemin DTW les apparie à coût quasi nul et peut donc
étirer arbitrairement — à condition que la bande le lui permette. On cesse de
deviner la largeur des blancs : on laisse l'alignement la découvrir.
"""
from __future__ import annotations
import numpy as np
import ink
from band import core_band
from dtw import render_profile, dtw_path
from routage import est_tabulaire
from dtwsnap import DTWSnap


class Elastique:
    name = 'elastique'

    def __init__(self):
        self.prose = DTWSnap()

    def _aligne(self, gray, line, space_ratio: float, bande: float):
        mask, ox, oy = ink.line_mask(gray, line.line_box)
        if mask.size <= 1: raise ValueError('masque vide')
        a, b = core_band(mask)
        obs = (mask[a:b+1, :] > 0).sum(axis=0).astype(float)
        if obs.sum() <= 0: raise ValueError("pas d'encre")
        px = max(8, int((b-a+1) / 0.46))
        prof, spans = render_profile(line.words, px, space_ratio=space_ratio)
        nz = np.nonzero(obs)[0]; o0, o1 = int(nz.min()), int(nz.max())
        nzp = np.nonzero(prof)[0]; p0, p1 = int(nzp.min()), int(nzp.max())
        path = dtw_path(prof[p0:p1+1], obs[o0:o1+1], band_frac=bande)
        if path is None: raise ValueError('dtw échoue')
        occ = (mask > 0).any(axis=0)
        out = []
        for (sa, sb) in spans:
            k0 = max(0, min(len(path)-1, int(round(sa - p0))))
            k1 = max(0, min(len(path)-1, int(round(sb - p0))))
            xa, xb = int(o0 + path[k0]), int(o0 + path[k1])
            if xb <= xa: xb = xa + 1
            xa = max(0, min(len(occ)-1, xa)); xb = max(0, min(len(occ)-1, xb))
            seg = np.nonzero(occ[xa:xb+1])[0]
            if len(seg): xa, xb = xa+int(seg.min()), xa+int(seg.max())
            ya, yb = ink.vertical_extent(mask, xa, xb)
            out.append((ox+xa, oy+ya, ox+xb, oy+yb))
        return out

    def boxes(self, gray: np.ndarray, line):
        if not est_tabulaire(line.words):
            return self.prose.boxes(gray, line)
        # espaces minimaux + bande large : c'est le DTW qui étire les vides
        return self._aligne(gray, line, space_ratio=0.25, bande=0.90)
