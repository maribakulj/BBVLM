"""G02 — développement sur les pages de G01 (consommées pour la géométrie).

connexe+A32 routé à la manière d'A37 (astra) : la boîte A32 n'est gardée que
si elle ne déborde pas verticalement la boîte connexe ; sinon on garde
l'horizontale d'A32 et la verticale de connexe. Et diagnostic du pire cas.
"""
import sys, json
import numpy as np
from g01 import charge, ConnexeA32
M = '/home/user/BBVLM/src'; sys.path[:0] = [M, M+'/boxers']
import judge, connexe


class Route(ConnexeA32):
    name = 'connexe+A32 routé'
    def boxes(self, g, ln):
        c = self.c.boxes(g, ln)
        x0, y0, x1, y1 = ln.line_box; H, W = g.shape
        from composantes import refine_cells
        out, _ = refine_cells(g, [max(0, x0), max(0, y0), min(W, x1+1), min(H, y1+1)],
                              [[a, b, d+1, e+1] for a, b, d, e in c], 'satellites')
        res = []
        for (a, b, d, e), (p, q, r, s) in zip(c, out):
            r, s = r-1, s-1
            y0, y1 = max(b, q), min(e, s)             # horizontale A32, jamais plus haut/bas que connexe
            if y1 < y0: y0, y1 = b, e                 # verticales disjointes (boîte dégénérée, O10) : connexe
            res.append((p, y0, r, y1))
        return res


def pire(boxer, page):
    worst = (0, None)
    g = page.gray
    for ln in page.lines:
        try: pred = boxer.boxes(g, ln)
        except Exception: continue
        if len(pred) != len(ln.words): continue
        gt = ln.word_boxes; span = max(b[2] for b in gt)-min(b[0] for b in gt)
        cw = max(1.0, span/max(1, sum(len(w) for w in ln.words)))
        for k in range(len(gt)-1):
            lo, hi = sorted((gt[k][2], gt[k+1][0])); x = (pred[k][2]+pred[k+1][0])/2
            d = (lo-x if x < lo else x-hi if x > hi else 0)/cw
            if d > worst[0]: worst = (d, (ln.text, k, ln.words[k], ln.words[k+1], gt[k], gt[k+1], pred[k], pred[k+1], ln.line_box))
    return worst


if __name__ == '__main__':
    pages = [a.split('=') for a in sys.argv[1:]]
    for boxer in (connexe.Connexe(), Route()):
        for d, lec in pages:
            p, ec = charge(d, lec)
            s = judge.score(boxer, [p]).summary()
            print(f"{boxer.name:18s} {p.corpus[:10]:10s} échec {s['lignes_en_echec']+ec:2d} | ≤0,5c {s['pct_sous_0.5c']:6} | pire {s['err_max']:5} | IoU méd {s['iou_med']} p10 {s['iou_p10']}")
            if boxer.name == 'connexe' and s['err_max'] and s['err_max'] > 2:
                print('   PIRE', pire(boxer, p))
