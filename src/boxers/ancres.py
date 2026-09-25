"""B17 — découper sur les vides certains, aligner à l'intérieur.

Les quatre tentatives précédentes sur le tableau (B12 espace estimé, B13 points
de conduite, B14 dispersion, B16 espaces élastiques) partaient toutes du même
présupposé : que le DTW devait absorber les grands vides. Mesuré, il ne le fait
pas — et lui en donner les moyens (bande à 0,90) l'a fait divaguer, BNL passant
de 34,4 à 24,6 %.

La géométrie de la ligne dit pourquoi : `Luxembourg` finit à x=100, le mot
suivant commence à x=256. **Un vide de 250 px sur une ligne haute de 31 px n'est
pas ambigu** — aucune paire de lettres d'un même mot n'est séparée ainsi. C'est
une frontière de mot certaine, et la demander au DTW revient à lui faire
redécouvrir ce qui est déjà acquis.

On s'en sert donc comme **ancre** : les vides très supérieurs à la médiane
découpent la ligne en segments, on répartit les mots entre segments par leur
largeur rendue, et le DTW n'aligne plus qu'à l'intérieur de chaque segment — où
les vides sont homogènes, c'est-à-dire là où il est bon.

Le principe vaut au-delà du tableau : partout où un vide est certain, il vaut
mieux l'imposer que l'inférer.
"""
from __future__ import annotations
import numpy as np
import ink
from band import core_band
from dtw import render_profile, dtw_path, _font
from dtwsnap import DTWSnap

FACTEUR_ANCRE = 3.0      # un vide >= 3x la médiane des vides est certain


class Ancres:
    name = 'ancres'

    def __init__(self):
        self.repli = DTWSnap()

    def _segments(self, runs, h_ligne):
        """Indices de plages où couper : vides franchement hors distribution."""
        if len(runs) < 3: return []
        gaps = np.array([runs[j+1][0]-runs[j][1]-1 for j in range(len(runs)-1)], float)
        pos = gaps[gaps > 0]
        if len(pos) < 3: return []
        med = float(np.median(pos))
        seuil = max(med*FACTEUR_ANCRE, h_ligne*1.2)
        return [j for j, g in enumerate(gaps) if g >= seuil]

    def _aligne_segment(self, mask, a, b, x0, x1, mots, ox, oy):
        """DTW d'un segment : mots connus, vides homogènes."""
        obs = (mask[a:b+1, x0:x1+1] > 0).sum(axis=0).astype(float)
        if obs.sum() <= 0 or len(mots) == 0: return None
        px = max(8, int((b-a+1)/0.46))
        prof, spans = render_profile(mots, px)
        nz = np.nonzero(obs)[0]; o0, o1 = int(nz.min()), int(nz.max())
        nzp = np.nonzero(prof)[0]; p0, p1 = int(nzp.min()), int(nzp.max())
        path = dtw_path(prof[p0:p1+1], obs[o0:o1+1], band_frac=0.30)
        if path is None: return None
        occ = (mask > 0).any(axis=0)
        out = []
        for (sa, sb) in spans:
            k0 = max(0, min(len(path)-1, int(round(sa-p0))))
            k1 = max(0, min(len(path)-1, int(round(sb-p0))))
            xa, xb = x0+o0+int(path[k0]), x0+o0+int(path[k1])
            if xb <= xa: xb = xa+1
            xa = max(0, min(len(occ)-1, xa)); xb = max(0, min(len(occ)-1, xb))
            seg = np.nonzero(occ[xa:xb+1])[0]
            if len(seg): xa, xb = xa+int(seg.min()), xa+int(seg.max())
            ya, yb = ink.vertical_extent(mask, xa, xb)
            out.append((ox+xa, oy+ya, ox+xb, oy+yb))
        return out

    def boxes(self, gray: np.ndarray, line):
        mask, ox, oy = ink.line_mask(gray, line.line_box)
        if mask.size <= 1: return self.repli.boxes(gray, line)
        a, b = core_band(mask)
        h = line.line_box[3]-line.line_box[1]
        runs = ink.x_runs(mask[a:b+1, :], max(1, int((b-a+1)*0.10)))
        coupes = self._segments(runs, h)
        if not coupes or len(runs) < len(line.words):
            return self.repli.boxes(gray, line)

        # segments de plages
        bornes = [-1] + coupes + [len(runs)-1]
        segs = [(runs[bornes[i]+1][0], runs[bornes[i+1]][1]) for i in range(len(bornes)-1)]
        if len(segs) > len(line.words): return self.repli.boxes(gray, line)

        # répartition des mots entre segments, au prorata de la largeur rendue
        f = _font(max(8, int((b-a+1)/0.46)))
        larg = [max(1.0, f.getlength(w)) for w in line.words]
        occup = [max(1, s[1]-s[0]+1) for s in segs]
        tot_o, tot_l = sum(occup), sum(larg)
        part = []
        i = 0
        for si, o in enumerate(segs):
            if si == len(segs)-1:
                part.append(list(range(i, len(line.words)))); break
            cible = (occup[si]/tot_o)*tot_l
            acc, j = 0.0, i
            while j < len(line.words)-(len(segs)-si-1) and (acc < cible or j == i):
                acc += larg[j]; j += 1
            part.append(list(range(i, j))); i = j
        if any(not p for p in part): return self.repli.boxes(gray, line)

        out = []
        for (sx0, sx1), idx in zip(segs, part):
            r = self._aligne_segment(mask, a, b, sx0, sx1, [line.words[k] for k in idx], ox, oy)
            if r is None or len(r) != len(idx): return self.repli.boxes(gray, line)
            out += r
        return out if len(out) == len(line.words) else self.repli.boxes(gray, line)
