"""Contrôles sans vérité terrain — refuser plutôt que combler.

Une sortie de vérité terrain ne peut pas se permettre d'inventer. Or on ne
dispose, en production, d'aucune référence à quoi comparer. Deux signaux sont
néanmoins calculables depuis l'image seule et la proposition :

1. **le compte** — la géométrie annonce N lignes, le lecteur en rend M ;
2. **l'ajustement à l'encre** — un texte inventé ne peut pas se répartir sur les
   plages d'encre réellement présentes. Mesuré sur Le Petit Parisien :
   0,26 de coût par mot pour du texte exact, 0,97 pour du texte fabriqué.

Le second est ici, le premier vit dans `vlm.block_flags`.
"""
from __future__ import annotations
import numpy as np
import ink

INF = 1e9


def seuil_auto(couts, k: float = 2.5, plancher: float = 0.45,
               plafond: float = 1.10) -> float:
    """Seuil calibré SUR LE DOCUMENT, jamais figé. Les lignes correctes forment
    un pic serré ; on coupe à médiane + k·MAD."""
    v = np.array([c for c in couts if c < 1e8], dtype=float)
    if len(v) < 8: return 0.65
    med = float(np.median(v))
    mad = float(np.median(np.abs(v-med))) or 0.05
    return float(np.clip(med + k*1.4826*mad, plancher, plafond))


def cout_ligne(gray, x0, x1, y0, y1, cy, texte, cal):
    """Coût par mot de l'ajustement de `texte` sur l'encre de la bande.
    Rend (coût, boîtes, masque) — coût INF si l'ajustement est impossible."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'boxers'))
    from inkgap import partition
    toks = texte.split()
    if not toks: return INF, None, None
    mask, ox, oy = ink.line_mask(gray, (x0, y0, x1, y1))
    if mask.size <= 1: return INF, None, None
    runs = ink.x_runs(mask, cal.get('run_area_min', 3))
    if not runs: return INF, None, mask
    boxes = partition(toks, runs)
    if not boxes: return INF, None, mask
    # coût = dispersion des largeurs observées par rapport aux largeurs attendues
    from inkgap import FONT
    att = np.array([max(1.0, FONT.getlength(t)) for t in toks], float)
    obs = np.array([max(1, b-a+1) for a, b in boxes], float)
    ech = float(np.median(obs/att)) if len(att) else 1.0
    if ech <= 0: return INF, boxes, mask
    r = obs/(att*ech)
    cout = float(np.sum(np.abs(np.log(np.clip(r, 1e-3, 1e3)))))
    return cout, boxes, mask
