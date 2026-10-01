"""E1 — mesure au judge BBVLM (CRITERE) dans le repère du crop, par œuvre.
usage : python e1_mesure.py A1_DIR PARTITION BRAS [PREDICTIONS.json]   (BRAS = G0 | fichier de prédictions)
PREDICTIONS.json : {bloc_id: [[x0,y0,x1,y1] par occurrence, repère crop]}"""
import json, sys, os
sys.path[:0] = ['/home/user/BBVLM/src', '/home/user/BBVLM/src/boxers', '/home/user/BBVLM/loop/outils']
import judge, corpora
def pages(a1, part):
    P = []
    for l in open(a1 + '/manifest.jsonl', encoding='utf-8'):
        m = json.loads(l)
        if m['partition'] != part: continue
        x0, y0 = m['crop'][:2]; L = []
        for li, lb in enumerate(m['lignes']):
            occ = [o for o in m['occurrences'] if o['ligne'] == li]
            wb = [(o['boite_page'][0] - x0, o['boite_page'][1] - y0, o['boite_page'][2] - x0, o['boite_page'][3] - y0) for o in occ]
            L.append(corpora.Line(m['texte'].split('\n')[li], [o['texte'] for o in occ], (lb[0] - x0, lb[1] - y0, lb[2] - x0, lb[3] - y0), wb))
        P.append((m, corpora.Page(m['id'], m['oeuvre'], f"{a1}/crops/{m['id']}.png", L)))
    return P
class Fichier:
    def __init__(self, pred, P):
        self.name = 'fichier'; self.t = {}
        for m, p in P:
            if m['id'] not in pred: continue
            b = pred[m['id']]
            for li, ln in enumerate(p.lines):
                self.t[(ln.line_box, tuple(ln.words))] = [tuple(b[k]) for k, o in enumerate(m['occurrences']) if o['ligne'] == li]
    def boxes(self, g, ln): return self.t[(ln.line_box, tuple(ln.words))]
class G0:
    """chaîne actuelle : LigneBase + W05 (+ W06) sur la boîte de ligne VT et le texte VT"""
    name = 'G0'
    def __init__(self):
        from centre import LigneBase; self.LB = LigneBase
    def boxes(self, g, ln):
        from w05 import ajuste
        o = tuple(ln.line_box); bs = [tuple(v) for v in self.LB({o: None}).boxes(g, ln)]
        if len(bs) == len(ln.words):
            try: bs = ajuste(g, o, ln.words, bs, False)
            except Exception: pass
        return bs
def critere(s): return s['pct_sous_0.5c'] is not None and s['pct_sous_0.5c'] >= 95 and s['err_max'] <= 3 and s['iou_med'] >= .8 and s['lignes_en_echec'] == 0
if __name__ == '__main__':
    a1, part, bras = sys.argv[1:4]; P = pages(a1, part)
    bx = G0() if bras == 'G0' else Fichier(json.load(open(sys.argv[4])), P)
    rep = judge.score(bx, [p for _, p in P]); s = rep.summary(); par = rep.per_corpus
    out = {'bras': bras, 'partition': part, 'global': s, 'oeuvres': par, 'oeuvres_au_critere': sum(critere(v) for v in par.values()), 'n_oeuvres': len(par)}
    print(json.dumps(out, ensure_ascii=False))
