"""B15 — router sur le TEXTE, pas sur l'image.

B14 routait selon la dispersion des blancs observés. Mesuré : elle ne dépasse
jamais le seuil sur les lignes de tableau de BNL, qui repartent donc vers le
moteur de prose. Aucune régression, aucun gain.

Le signal fiable était sous la main : **le texte dit ce qu'il est**. La sortie
du VLM contient `id.......`, `Dép......`, et des colonnes de nombres. Le motif
de conduite est trouvé sur 17 lignes sur 18 — contre zéro détection côté image.

C'est le principe qu'on a établi une couche plus haut, pour la mise en page :
le modèle lit, la géométrie place. Ici de même — le texte annonce la nature de
la ligne, la géométrie s'y adapte.
"""
from __future__ import annotations
import re
import numpy as np
from dtwsnap import DTWSnap
from dtwadapt import DTWAdapt

CONDUITE = re.compile(r'\.{3,}|·{3,}|-{3,}|_{3,}')


def est_tabulaire(words: list[str]) -> bool:
    """Trois marqueurs, indépendants de la langue et du siècle."""
    t = ' '.join(words)
    if CONDUITE.search(t): return True
    if len(words) < 3: return False
    # part de jetons purement numériques (colonnes de chiffres)
    num = sum(1 for w in words if re.fullmatch(r'[\d.,%/-]+', w))
    if num/len(words) >= 0.45: return True
    # jetons très courts en majorité, sans ponctuation de phrase
    court = sum(1 for w in words if len(w) <= 3)
    return court/len(words) >= 0.70 and not re.search(r'[,;:»]', t)


class Routage:
    name = 'routage'

    def __init__(self):
        self.prose = DTWSnap()
        self.tableau = DTWAdapt()

    def boxes(self, gray: np.ndarray, line):
        moteur = self.tableau if est_tabulaire(line.words) else self.prose
        try:
            return moteur.boxes(gray, line)
        except Exception:
            return self.prose.boxes(gray, line)
