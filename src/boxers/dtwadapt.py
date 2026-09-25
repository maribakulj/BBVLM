"""B12 — espace du gabarit estimé sur l'observé, bande DTW adaptative.

Échec mesuré de B11 sur BNL 0015, tableau financier
(`Luxembourg 141 Dép...... fr. 12315 31`) : 32,79 % seulement, alors que sa
vérité terrain est géométriquement valide. Deux causes, toutes deux dans le
gabarit et non dans le DTW :

1. **L'espace rendu est la chasse de la fonte.** En prose, l'espace inter-mot
   vaut à peu près cette chasse. Dans un tableau, les colonnes imposent des
   blancs plusieurs fois plus larges et très inégaux. Le gabarit est donc
   comprimé là où l'image est étalée.
2. **La bande de Sakoe-Chiba borne la déformation.** À 0,25 elle interdit
   exactement le décalage qu'un tableau exige.

On estime donc l'espace sur les blancs observés — médiane des blancs de la
classe haute, séparés par Otsu — et on élargit la bande quand leur dispersion
est forte. Le DTW reste inchangé : c'est son entrée qu'on corrige.
"""
from __future__ import annotations
import numpy as np
import ink
from band import core_band
from dtw import render_profile, dtw_path
from hybride import otsu_seuil


class DTWAdapt:
    name = 'dtw_adapt'

    def boxes(self, gray: np.ndarray, line):
        mask, ox, oy = ink.line_mask(gray, line.line_box)
        if mask.size <= 1: raise ValueError('masque vide')
        a, b = core_band(mask)
        obs = (mask[a:b+1, :] > 0).sum(axis=0).astype(float)
        if obs.sum() <= 0: raise ValueError("pas d'encre")
        s = ink.line_scale(line.line_box)
        px = max(8, int((b-a+1) / 0.46))

        # ── espace estimé sur l'image ──────────────────────────────────────
        runs = ink.x_runs(mask[a:b+1, :], max(1, int((b-a+1)*0.10)))
        ratio, disp = 1.0, 0.0
        if len(runs) > 2:
            gaps = np.array([runs[j+1][0]-runs[j][1]-1 for j in range(len(runs)-1)], float)
            gaps = gaps[gaps > 0]
            if len(gaps) >= 2:
                t = otsu_seuil(gaps)
                hauts = gaps[gaps > t]
                if len(hauts):
                    from dtw import _font
                    chasse = max(1.0, _font(px).getlength(' '))
                    ratio = float(np.clip(np.median(hauts)/chasse, 0.3, 8.0))
                    # dispersion des blancs inter-mots : forte => tableau
                    disp = float(np.std(hauts)/max(1.0, np.mean(hauts)))

        prof, spans = render_profile(line.words, px, space_ratio=ratio)
        bande = float(np.clip(0.25 + disp*0.8, 0.25, 0.85))

        nz = np.nonzero(obs)[0]; o0, o1 = int(nz.min()), int(nz.max())
        nzp = np.nonzero(prof)[0]; p0, p1 = int(nzp.min()), int(nzp.max())
        path = dtw_path(prof[p0:p1+1], obs[o0:o1+1], band_frac=bande)
        if path is None: raise ValueError('dtw échoue')

        def to_obs(xr: float) -> float:
            k = max(0, min(len(path)-1, int(round(xr - p0))))
            return o0 + path[k]

        occ = (mask > 0).any(axis=0)
        out = []
        for (sa, sb) in spans:
            xa, xb = int(round(to_obs(sa))), int(round(to_obs(sb)))
            if xb <= xa: xb = xa+1
            # recalage sur l'encre (B11)
            xa = max(0, min(len(occ)-1, xa)); xb = max(0, min(len(occ)-1, xb))
            seg = np.nonzero(occ[xa:xb+1])[0]
            if len(seg): xa, xb = xa+int(seg.min()), xa+int(seg.max())
            ya, yb = ink.vertical_extent(mask, xa, xb)
            out.append((ox+xa, oy+ya, ox+xb, oy+yb))
        return out
