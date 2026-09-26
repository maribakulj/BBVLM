"""B54 — refuser le support d'encre quand il est plus large que le texte.

Cause mesurée en B52 : une boîte de ligne qui franchit le filet de colonne laisse
entrer l'encre du voisin ; le moteur étire alors son gabarit sur toute l'étendue
et place des mots dans l'autre colonne. Pire cas de Newseye : 33,31 caractères.

Le garde-fou n'utilise QUE le texte et l'image — jamais la VT des mots — donc il
vaut en production, où les boîtes de ligne viendront d'eynollah ou de kraken et
auront le même défaut.

Première version ÉCARTÉE : elle décidait de rogner d'après un seuil sur la
largeur du support. B55 a montré qu'aucun seuil ne sépare proprement les lignes
polluées des lignes saines — au mieux 11 suspectes sur 70 attrapées pour 16
saines abîmées — et la mesure l'a confirmé en dégradant le pire cas de BnF de
1,84 à 9,04. Un détecteur n'existe pas ici.

Principe retenu : **ne pas décider, laisser l'alignement juger**. On propose les
deux supports — entier et rogné — au DTW, et on garde celui dont le coût
d'alignement normalisé est le plus faible. Le gabarit rendu porte la forme du
texte ; si l'encre étrangère le contrarie, le support rogné s'aligne mieux. Aucun
seuil à fixer, et la décision est prise ligne par ligne sur une quantité que le
moteur calcule déjà.

Prévalence de l'encre étrangère (B53) : 0,9 % des lignes de Newseye, 0 % de BnF
et de PetitParisien.
"""
from __future__ import annotations
import numpy as np
import ink
from band import core_band
from dtw import render_profile
from connexe import Connexe

SEUIL_BLANC = 1.8   # un blanc plus large que ce multiple de l'espace rendu sépare deux amas
GAIN_MIN = 0.02     # le support rogné doit gagner franchement, sinon on garde l'entier


class Rogne:
    name = 'rogne'

    def __init__(self, base=None):
        self.base = base or Connexe()

    def _support_utile(self, gray, line):
        """Renvoie une boîte de ligne rognée, ou None si rien à rogner."""
        mask, ox, oy = ink.line_mask(gray, line.line_box)
        if mask.size <= 1: return None
        a, b = core_band(mask)
        col = (mask[a:b+1, :] > 0).sum(axis=0)
        nz = np.nonzero(col)[0]
        if nz.size < 2: return None
        o0, o1 = int(nz.min()), int(nz.max())
        px = max(8, int((b-a+1)/0.46))
        prof, spans = render_profile(line.words, px)
        if not spans: return None
        # amas d'encre séparés par des blancs larges
        from dtw import _font
        espace = max(2.0, _font(px).getlength(' '))
        vide = 0; amas = []; debut = o0
        for x in range(o0, o1+2):
            plein = x <= o1 and col[x] > 0
            if plein:
                if vide > espace*SEUIL_BLANC and debut is not None:
                    amas.append((debut, x-vide-1)); debut = x
                vide = 0
            else:
                vide += 1
        amas.append((debut, o1))
        if len(amas) < 2: return None
        # On ne choisit pas : on demande au DTW lequel des supports candidats
        # s'aligne le mieux sur le gabarit du texte.
        from dtw import dtw_path
        nzp = np.nonzero(prof)[0]
        if nzp.size < 2: return None
        prof_c = prof[int(nzp.min()):int(nzp.max())+1]
        meilleur = None
        for fin in [am[1] for am in amas]:
            obs = col[o0:fin+1].astype(float)
            if obs.size < 2 or obs.sum() <= 0: continue
            chemin, cout = dtw_path(prof_c, obs, with_cost=True)
            if chemin is None: continue
            if meilleur is None or cout < meilleur[0] - (GAIN_MIN if fin != amas[-1][1] else 0.0):
                meilleur = (cout, fin)
        if meilleur is None or meilleur[1] >= o1: return None
        x0, y0, x1, y1 = line.line_box
        return (x0, y0, min(x1, ox+meilleur[1]+2), y1)

    def boxes(self, gray: np.ndarray, line):
        neuf = self._support_utile(gray, line)
        if neuf is None:
            return self.base.boxes(gray, line)
        class _L:
            pass
        l2 = _L()
        for k in ('text', 'words', 'word_boxes'):
            setattr(l2, k, getattr(line, k, None))
        l2.line_box = neuf
        try:
            return self.base.boxes(gray, l2)
        except Exception:
            return self.base.boxes(gray, line)
