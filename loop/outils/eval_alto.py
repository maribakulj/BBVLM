"""Note un ALTO produit contre la référence PAGE au mot (texte et boîtes).

Appariement hongrois sur l'IoU des boîtes de mots (tous mots de la page).
Rapporte : rappel à IoU ≥ 0,5 et ≥ 0,8, IoU médian et p10 des paires,
et rappel conjoint (texte diplo exact ET IoU ≥ 0,8) — ce qu'un utilisateur
d'une VT au mot obtient réellement. Mots non placés = manqués.
"""
import sys
import numpy as np
from lxml import etree
from scipy.optimize import linear_sum_assignment
from cer import vue
from segeval import iou


def mots_alto(p):
    r = etree.parse(p).getroot(); N = {'a': r.tag.split('}')[0][1:]}
    out = []
    for s in r.iter(f'{{{N["a"]}}}String'):
        if s.get('HPOS') is None: continue
        x, y, w, h = (int(s.get(k)) for k in ('HPOS', 'VPOS', 'WIDTH', 'HEIGHT'))
        out.append((s.get('CONTENT'), (x, y, x+w-1, y+h-1)))
    return out


def mots_page(p):
    r = etree.parse(p).getroot(); N = {'p': r.tag.split('}')[0][1:]}
    out = []
    for w in r.findall('.//p:Word', N):
        u = w.find('p:TextEquiv/p:Unicode', N); c = w.find('p:Coords', N)
        if u is None or not u.text or c is None: continue
        pts = [tuple(map(int, q.split(','))) for q in c.get('points').split()]
        out.append((u.text.strip(), (min(a for a, _ in pts), min(b for _, b in pts), max(a for a, _ in pts), max(b for _, b in pts))))
    return out


def note(alto, page):
    P, R = mots_alto(alto), mots_page(page)
    M = np.array([[iou(r[1], p[1]) for p in P] for r in R])
    a, b = linear_sum_assignment(-M)
    ious = np.array([M[i, j] for i, j in zip(a, b)])
    conj = sum(1 for i, j in zip(a, b) if M[i, j] >= .8 and vue(R[i][0], 'diplo') == vue(P[j][0], 'diplo'))
    n = len(R)
    return {'mots_ref': n, 'mots_places': len(P), 'rappel_iou50': round(float((ious >= .5).sum()/n), 4),
            'rappel_iou80': round(float((ious >= .8).sum()/n), 4), 'iou_med': round(float(np.median(ious)), 3),
            'iou_p10': round(float(np.percentile(ious, 10)), 3), 'rappel_texte_et_iou80': round(conj/n, 4)}


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        alto, page = arg.split('=')
        print(alto.split('/')[-2][:10], note(alto, page))
