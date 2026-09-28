"""G01 — boîtes de mots avec le texte lu par le VLM, noté par CRITERE.md.

Entrées du boxer : image, texte VLM de la ligne (lecture retenue d'O01-O03,
appariée à la ligne de référence), boîte de ligne de référence. Jamais les
boîtes de mots de référence. Une ligne dont le nombre de mots lus diffère du
nombre de mots de référence est une ligne en échec (CRITERE : 0 exigé).
Moteurs : proportionnel, connexe (master), connexe → filtre A32 (astra).
"""
import json, sys, glob, os
import numpy as np
M = '/home/user/BBVLM/src'; sys.path[:0] = [M, M+'/boxers']
import corpora, judge, proportional, connexe
from lxml import etree
from accord import apparie
from cer import vue
from composantes import refine_cells


class ConnexeA32:
    name = 'connexe+A32'
    def __init__(self): self.c = connexe.Connexe()
    def boxes(self, g, ln):
        b = self.c.boxes(g, ln)
        x0, y0, x1, y1 = ln.line_box
        H, W = g.shape
        lb = [max(0, x0), max(0, y0), min(W, x1+1), min(H, y1+1)]
        cells = [[a, c, d+1, e+1] for a, c, d, e in b]
        out, _ = refine_cells(g, lb, cells, 'satellites')
        return [(a, c, d-1, e-1) for a, c, d, e in out]


def charge(dossier, lecture):
    ref = json.load(open(f'{dossier}/ref.json'))
    ouvrage, page = os.path.basename(dossier.rstrip('/')).rsplit('_', 1)
    xml = f'{dossier}/page.xml'
    r = etree.parse(xml).getroot(); N = {'p': r.tag.split('}')[0][1:]}
    tls = r.findall('.//p:TextLine', N)
    lu = [l for l in open(lecture, encoding='utf-8').read().splitlines() if l.strip()]
    idx = [i for i, x in enumerate(ref) if x.strip()]
    m = apparie([vue(ref[i], 'diplo') for i in idx], lu)
    lignes, echec_compte = [], 0
    for k, i in enumerate(idx):
        tl = tls[i]; ws, bs = [], []
        for w in tl.findall('p:Word', N):
            u = w.find('p:TextEquiv/p:Unicode', N); wc = w.find('p:Coords', N)
            if u is None or not u.text or wc is None: continue
            ws.append(u.text.strip()); bs.append(corpora._box(wc.get('points')))
        if len(ws) < 2: continue
        mots = m.get(k, '').split()
        if len(mots) != len(ws): echec_compte += 1; continue
        lignes.append(corpora.Line(' '.join(mots), mots, corpora._box(tl.find('p:Coords', N).get('points')), bs))
    return corpora.Page(page, ouvrage, f'{dossier}/page.png', lignes), echec_compte


if __name__ == '__main__':
    pages = [a.split('=') for a in sys.argv[1:]]
    res = {}
    for boxer in (proportional.Proportional(), connexe.Connexe(), ConnexeA32()):
        tot = {}
        for d, lec in pages:
            p, ec = charge(d, lec)
            r = judge.score(boxer, [p])
            s = r.summary(); s['lignes_en_echec'] += ec
            tot[p.corpus[:10]] = s
            print(f"{boxer.name:12s} {p.corpus[:10]:10s} lignes {s['lignes']:3d} échec {s['lignes_en_echec']:2d} | ≤0,5c {s['pct_sous_0.5c']:6} | pire {s['err_max']:5} | IoU méd {s['iou_med']} p10 {s['iou_p10']}")
        res[boxer.name] = tot
    json.dump(res, open('/tmp/claude-0/-home-user-BBVLM/84210bd8-ec20-5b45-a7f8-f35608b01c8d/scratchpad/g01.json', 'w'), indent=1, ensure_ascii=False)
