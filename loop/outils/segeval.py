"""Segmentation en lignes : appariement, fusions, divisions, lignes manquantes.

Appariement hongrois sur l'IoU des rectangles de ligne ; une ligne de
référence est « trouvée » si IoU ≥ 0,5 avec une ligne prédite. Fusion : une
ligne prédite couvre (≥ 50 % de leur hauteur) plusieurs lignes de référence ;
division : une ligne de référence est couverte par plusieurs prédites.
Rapport par page, jamais de moyenne entre pages.
"""
import numpy as np
from scipy.optimize import linear_sum_assignment


def iou(a, b):
    ix = max(0, min(a[2], b[2])-max(a[0], b[0])); iy = max(0, min(a[3], b[3])-max(a[1], b[1]))
    i = ix*iy; u = (a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-i
    return i/u if u > 0 else 0.


def couvre(p, r):
    """Part de la hauteur de r couverte par p, si leurs x se recouvrent."""
    if min(p[2], r[2]) <= max(p[0], r[0]): return 0.
    return max(0, min(p[3], r[3])-max(p[1], r[1]))/max(1, r[3]-r[1])


def evalue(ref, pred):
    M = np.array([[iou(r, p) for p in pred] for r in ref]) if pred else np.zeros((len(ref), 0))
    a, b = linear_sum_assignment(-M) if pred else ([], [])
    trouvees = sum(1 for i, j in zip(a, b) if M[i, j] >= .5)
    fusions = sum(1 for p in pred if sum(couvre(p, r) >= .5 for r in ref) > 1)
    divisions = sum(1 for r in ref if sum(couvre(p, r) >= .5 for p in pred) > 1)
    return {'ref': len(ref), 'pred': len(pred), 'trouvees_iou50': trouvees,
            'rappel': trouvees/max(1, len(ref)), 'precision': trouvees/max(1, len(pred)),
            'fusions': fusions, 'divisions': divisions,
            'iou_med': float(np.median([M[i, j] for i, j in zip(a, b)])) if len(a) else 0.}
