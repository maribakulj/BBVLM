"""S01 + E01 : lignes prédites par kraken, puis boîtes connexe avec texte VLM.

S01 : segeval (IoU ≥ 0,5, fusions, divisions) par page.
E01 : pour chaque ligne de référence, la ligne kraken appariée (IoU ≥ 0,5)
remplace la boîte de ligne de référence ; le texte est la lecture VLM
appariée. Aucune ligne kraken appariée = ligne en échec. Noté par judge
(CRITERE.md). C'est la première mesure où ni le texte ni la boîte de ligne
ne viennent de la référence.
"""
import json, sys
import numpy as np
from scipy.optimize import linear_sum_assignment
from g01 import charge
from segeval import evalue, iou
M = '/home/user/BBVLM/src'; sys.path[:0] = [M, M+'/boxers']
import judge, connexe, corpora


def e01(dossier, lecture, boxer):
    page, echec_compte = charge(dossier, lecture)
    kr = [l['bbox'] for l in json.load(open(f'{dossier}/kraken.json'))['lignes']]
    ref = [ln.line_box for ln in page.lines]
    s = evalue(ref, kr) if ref else {}
    Mx = np.array([[iou(r, k) for k in kr] for r in ref]) if kr and ref else np.zeros((len(ref), 0))
    a, b = linear_sum_assignment(-Mx) if kr and ref else ([], [])
    m = {i: kr[j] for i, j in zip(a, b) if Mx[i, j] >= .5}
    lignes, sans = [], 0
    for i, ln in enumerate(page.lines):
        if i not in m: sans += 1; continue
        x0, y0, x1, y1 = m[i]
        lignes.append(corpora.Line(ln.text, ln.words, (x0, y0, x1, y1), ln.word_boxes))
    p2 = corpora.Page(page.name, page.corpus, page.image_path, lignes)
    r = judge.score(boxer, [p2]).summary()
    r['lignes_en_echec'] += sans + echec_compte
    return s, r


if __name__ == '__main__':
    b = connexe.Connexe()
    for arg in sys.argv[1:]:
        d, lec = arg.split('=')
        s, r = e01(d, lec, b)
        nom = d.rstrip('/').split('/')[-1][:10]
        print(f"{nom:10s} S01 réf {s.get('ref')} préd {s.get('pred')} trouvées {s.get('trouvees_iou50')} fusions {s.get('fusions')} divisions {s.get('divisions')} IoU méd {s.get('iou_med', 0):.3f} || E01 lignes {r['lignes']} échec {r['lignes_en_echec']} ≤0,5c {r['pct_sous_0.5c']} pire {r['err_max']} IoU méd {r['iou_med']}", flush=True)
