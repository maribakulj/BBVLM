"""B13 — points de conduite traités comme un intervalle unique.

`Dép......` : une suite de composantes identiques, petites, régulièrement
espacées et posées sur la ligne de base. Le gabarit rendu n'en produit ni le
même nombre ni le même pas — la fonte compose les points à sa chasse, le
typographe les a espacés pour remplir la colonne. Le DTW aligne alors des
motifs périodiques qui ne se correspondent pas, et dérive sur toute la suite.

Un motif périodique est reconnaissable sans savoir ce qu'il est : composantes
de taille voisine, pas régulier, basses dans la ligne. On le détecte sur
l'image, on le remplace par UN intervalle opaque dans le profil observé, et on
fait de même dans le gabarit pour la suite de points correspondante. Le DTW
n'aligne plus que des motifs comparables.
"""
from __future__ import annotations
import re
import numpy as np
import ink
from band import core_band
from dtwadapt import DTWAdapt

LEADER = re.compile(r'\.{3,}|·{3,}|\.(?:\s?\.){2,}')


def detecte_conduite(runs, h_ligne: int) -> list[tuple[int, int]]:
    """Plages formant une suite périodique de petites composantes.
    Rend les intervalles (i, j) d'indices de plages à fusionner."""
    if len(runs) < 4: return []
    larg = np.array([r[1]-r[0]+1 for r in runs], float)
    petit = larg <= max(2.0, h_ligne*0.16)
    out, i = [], 0
    while i < len(runs)-2:
        if not petit[i]: i += 1; continue
        j = i
        pas = []
        while j+1 < len(runs) and petit[j+1]:
            pas.append(runs[j+1][0]-runs[j][0]); j += 1
        if j-i >= 2 and pas:
            p = np.array(pas, float)
            if p.std()/max(1.0, p.mean()) < 0.30:      # pas régulier
                out.append((i, j))
        i = j+1
    return out


class Leaders(DTWAdapt):
    name = 'leaders'

    def boxes(self, gray: np.ndarray, line):
        # sans point de conduite dans le texte, rien ne change
        if not LEADER.search(' '.join(line.words)):
            return super().boxes(gray, line)
        mask, ox, oy = ink.line_mask(gray, line.line_box)
        if mask.size <= 1: raise ValueError('masque vide')
        a, b = core_band(mask)
        h = line.line_box[3]-line.line_box[1]
        runs = ink.x_runs(mask[a:b+1, :], max(1, int((b-a+1)*0.10)))
        zones = detecte_conduite(runs, h)
        if not zones:
            return super().boxes(gray, line)
        # on bouche les suites périodiques : le profil y devient plein et lisse
        m2 = mask.copy()
        for i, j in zones:
            x0, x1 = runs[i][0], runs[j][1]
            m2[a:b+1, x0:x1+1] = 255
        # on rejoue l'alignement sur ce masque assaini
        class _L:
            pass
        faux = _L()
        faux.words = line.words
        faux.line_box = line.line_box
        faux.text = line.text
        import types
        orig = ink.line_mask
        try:
            ink.line_mask = lambda g, bx, pad=0.12: (m2, ox, oy)
            return DTWAdapt.boxes(self, gray, faux)
        finally:
            ink.line_mask = orig
