"""B14 — l'adaptation ne s'applique QUE si la ligne en a besoin.

B12 a élargi l'espace du gabarit et la bande DTW pour tout le monde. Résultat :
BnF passe de 1,84c à 3,37c de pire cas — au-dessus du seuil — pour gagner 1,6
point sur BNL. C'est le schéma exact que le critère interdit, et celui qui a
réfuté H1 dans `hans` : un gain sur un corpus payé par une régression ailleurs.

L'adaptation n'est pas fausse, elle est mal ciblée. Une ligne de prose a des
blancs inter-mots resserrés autour d'une valeur ; un tableau les a larges et
très inégaux. La dispersion relative des blancs de la classe haute sépare les
deux SANS savoir de quel document il s'agit. On ne dévie du comportement de
B11 que lorsqu'elle dépasse un seuil.
"""
from __future__ import annotations
import numpy as np
import ink
from band import core_band
from hybride import otsu_seuil
from dtwsnap import DTWSnap
from dtwadapt import DTWAdapt

SEUIL_DISPERSION = 0.55      # au-delà : mise en page tabulaire


def dispersion_blancs(gray, line) -> float:
    mask, ox, oy = ink.line_mask(gray, line.line_box)
    if mask.size <= 1: return 0.0
    a, b = core_band(mask)
    runs = ink.x_runs(mask[a:b+1, :], max(1, int((b-a+1)*0.10)))
    if len(runs) < 3: return 0.0
    gaps = np.array([runs[j+1][0]-runs[j][1]-1 for j in range(len(runs)-1)], float)
    gaps = gaps[gaps > 0]
    if len(gaps) < 2: return 0.0
    hauts = gaps[gaps > otsu_seuil(gaps)]
    if len(hauts) < 2: return 0.0
    return float(np.std(hauts)/max(1.0, np.mean(hauts)))


class Conditionnel:
    name = 'conditionnel'

    def __init__(self):
        self.prose = DTWSnap()
        self.tableau = DTWAdapt()

    def boxes(self, gray: np.ndarray, line):
        d = dispersion_blancs(gray, line)
        moteur = self.tableau if d > SEUIL_DISPERSION else self.prose
        try:
            return moteur.boxes(gray, line)
        except Exception:
            return self.prose.boxes(gray, line)
