"""B22 — l'étendue verticale d'un mot ne peut pas déborder sa ligne.

Diagnostic Newseye : frontières justes à 97,9 % mais IoU 0,610. Mesuré sur une
ligne, les boîtes prédites font **54 px de haut contre 31 dans la VT** — 74 % de
trop — alors que leurs abscisses coïncident au pixel près.

Cause : `ink.line_mask` élargit le crop de 12 % de la hauteur de ligne pour ne
pas trancher les hampes et les jambages. Utile pour détecter l'encre du mot,
néfaste pour mesurer son étendue : cette marge capte l'encre des lignes voisines,
et `vertical_extent` la prend pour du mot.

On sépare donc les deux usages. Le masque élargi sert à trouver les colonnes
d'encre ; l'étendue verticale est mesurée sur un masque **borné à la boîte de
ligne**. Rien ne change aux frontières — seulement à la hauteur des boîtes.
"""
from __future__ import annotations
import numpy as np
import ink
from compose import Compose


class Serre:
    name = 'serre'

    def __init__(self):
        self.base = Compose()

    def boxes(self, gray: np.ndarray, line):
        brut = self.base.boxes(gray, line)
        # masque SANS marge : l'encre qui s'y trouve appartient à cette ligne
        strict, sx, sy = ink.line_mask(gray, line.line_box, pad=0.0)
        if strict.size <= 1: return brut
        H = strict.shape[0]
        out = []
        for (x0, y0, x1, y1) in brut:
            a = max(0, min(strict.shape[1]-1, x0-sx))
            b = max(0, min(strict.shape[1]-1, x1-sx))
            sub = strict[:, a:b+1]
            rows = np.where((sub > 0).any(axis=1))[0]
            if len(rows) == 0:
                # aucune encre dans la bande stricte : on rabat sur la ligne
                out.append((x0, line.line_box[1], x1, line.line_box[3])); continue
            out.append((x0, sy+int(rows.min()), x1, sy+int(rows.max())))
        return out
