"""Deux lectures indépendantes : leurs désaccords désignent-ils les fautes ?

Unité : la ligne de référence. Une ligne est « fautive » pour un lecteur si sa
lecture appariée diffère de la référence (vue donnée). Une ligne est
« signalée » si les deux lecteurs, appariés à cette même ligne, diffèrent.
"""
import json, sys
import numpy as np
from scipy.optimize import linear_sum_assignment
from cer import vue, lev


def apparie(R, H):
    if not H: return {}
    C = np.array([[lev(r, h)/max(1, len(r)) for h in H] for r in R])
    a, b = linear_sum_assignment(C)
    return {i: H[j] for i, j in zip(a, b) if C[i, j] <= 1}


def accord(ref, l1, l2, nom='norm'):
    R = [vue(x, nom) for x in ref if x.strip()]
    m1 = apparie(R, [vue(x, nom) for x in l1 if x.strip()])
    m2 = apparie(R, [vue(x, nom) for x in l2 if x.strip()])
    tp = fp = fn = tn = 0
    for i, r in enumerate(R):
        a, b = m1.get(i), m2.get(i)
        faute = a != r               # la faute du lecteur 1, celui qu'on garderait
        signal = a != b
        tp += faute and signal; fp += signal and not faute
        fn += faute and not signal; tn += not faute and not signal
    return {'lignes': len(R), 'fautives_l1': tp+fn, 'signalees': tp+fp,
            'vrais_signaux': tp, 'fautes_non_vues': fn,
            'precision': tp/max(1, tp+fp), 'rappel': tp/max(1, tp+fn)}


if __name__ == '__main__':
    ref = json.load(open(sys.argv[1]))
    l1, l2 = (open(p, encoding='utf-8').read().splitlines() for p in sys.argv[2:4])
    print(json.dumps(accord(ref, l1, l2), ensure_ascii=False))
