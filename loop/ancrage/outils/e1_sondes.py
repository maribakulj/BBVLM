"""E1 — sondes G1 (états seuls) et G2 (états + attention croisée sur la carte fine). E1_PROTOCOLE.md.
usage : python e1_sondes.py A1_DIR FEAT_DIR BRAS COUCHE SORTIE_DIR   (BRAS = G1 | G2 ; COUCHE = 14 | 28)
Écrit SORTIE_DIR/{bras}_{couche}_{dev,test}.json (prédictions, repère crop) et journal.json."""
import json, sys, os, math, random, time
import numpy as np, torch, torch.nn as nn
torch.manual_seed(17); random.seed(17); np.random.seed(17); torch.set_num_threads(int(os.environ.get('FILS', '4')))
a1, fd, bras, couche, out = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]; os.makedirs(out, exist_ok=True)
M = [json.loads(l) for l in open(a1 + '/manifest.jsonl', encoding='utf-8')]
import hashlib
NT = int(os.environ.get('N_TRAIN', '600'))
TRAIN_OK = set(sorted([m['id'] for m in M if m['partition'] == 'train' and os.path.exists(f"{fd}/{m['id']}.npz")], key=lambda b: hashlib.sha256(b.encode()).hexdigest())[:NT])
def charge(part):
    D = []
    for m in M:
        if part == 'train' and m['id'] not in TRAIN_OK: continue
        if m['partition'] != part or not os.path.exists(f"{fd}/{m['id']}.npz"): continue
        z = np.load(f"{fd}/{m['id']}.npz"); x0, y0, x1, y1 = m['crop']; W, H = x1 - x0, y1 - y0
        gh, gw = z['grille'].tolist(); Wp, Hp = gw * 16, gh * 16                  # entrée complétée (repère crop, origine commune)
        b = np.array([[o['boite_page'][0] - x0, o['boite_page'][1] - y0, o['boite_page'][2] - x0, o['boite_page'][3] - y0] for o in m['occurrences']], np.float32)
        D.append({'id': m['id'], 'q': torch.tensor(z[f'l{couche}'].astype(np.float32)), 'fine': torch.tensor(z['fine'].astype(np.float32)),
                  'gh': gh, 'gw': gw, 'Wp': Wp, 'Hp': Hp, 'cible': torch.tensor(b / np.array([Wp, Hp, Wp, Hp], np.float32))})
    return D
def pos2d(gh, gw, d=64):
    """positions sinusoïdales 2D des patches dans l'ordre réel de la grille (E0 : [h/2][w/2][2][2])"""
    r, c = np.meshgrid(np.arange(gh), np.arange(gw), indexing='ij')
    r = r.reshape(gh // 2, 2, gw // 2, 2).transpose(0, 2, 1, 3).reshape(-1); c = c.reshape(gh // 2, 2, gw // 2, 2).transpose(0, 2, 1, 3).reshape(-1)
    f = np.exp(-np.arange(0, d // 2, 2) * math.log(1000.) / (d // 2))
    pe = lambda v, n: np.concatenate([np.sin((v[:, None] + .5) / n * 100 * f), np.cos((v[:, None] + .5) / n * 100 * f)], 1)
    return torch.tensor(np.concatenate([pe(r, gh), pe(c, gw)], 1), dtype=torch.float32), torch.tensor(np.stack([(c + .5) / gw, (r + .5) / gh], 1), dtype=torch.float32)
class Sonde(nn.Module):
    def __init__(self, g2):
        super().__init__(); self.g2 = g2; d = 256
        self.q = nn.Sequential(nn.LayerNorm(2048), nn.Linear(2048, d), nn.GELU())
        if g2:
            self.k = nn.Linear(256 + 64, d); self.v = nn.Linear(256 + 64, d); self.ln = nn.LayerNorm(256)
        self.tete = nn.Sequential(nn.Linear(d * (3 if g2 else 1) + (2 if g2 else 0), d), nn.GELU(), nn.Linear(d, 4))
    def forward(self, ex):
        q = self.q(ex['q'])
        if not self.g2: h = q
        else:
            pe, xy = ex['pe']; f = torch.cat([self.ln(ex['fine']), pe], 1)
            a = (q @ self.k(f).T / 16).softmax(-1); h = torch.cat([q, a @ self.v(f), q * (a @ self.v(f)), a @ xy], 1)
        o = self.tete(h).sigmoid(); cx, cy, w, hh = o.unbind(-1)
        return torch.stack([cx - w / 2, cy - hh / 2, cx + w / 2, cy + hh / 2], -1)
def giou(p, t):
    ix0 = torch.max(p[:, 0], t[:, 0]); iy0 = torch.max(p[:, 1], t[:, 1]); ix1 = torch.min(p[:, 2], t[:, 2]); iy1 = torch.min(p[:, 3], t[:, 3])
    inter = (ix1 - ix0).clamp(0) * (iy1 - iy0).clamp(0); ap = (p[:, 2] - p[:, 0]).clamp(0) * (p[:, 3] - p[:, 1]).clamp(0); at = (t[:, 2] - t[:, 0]) * (t[:, 3] - t[:, 1])
    u = ap + at - inter; iou = inter / u.clamp(1e-9)
    cx0 = torch.min(p[:, 0], t[:, 0]); cy0 = torch.min(p[:, 1], t[:, 1]); cx1 = torch.max(p[:, 2], t[:, 2]); cy1 = torch.max(p[:, 3], t[:, 3])
    c = (cx1 - cx0) * (cy1 - cy0); return iou - (c - u) / c.clamp(1e-9), iou
def prepare(D):
    for ex in D: ex['pe'] = pos2d(ex['gh'], ex['gw'])
tr, dv, te = charge('train'), charge('dev'), charge('test'); prepare(tr); prepare(dv); prepare(te)
print('blocs', len(tr), len(dv), len(te), flush=True)
mod = Sonde(bras == 'G2'); opt = torch.optim.AdamW(mod.parameters(), lr=1e-3, weight_decay=1e-4)
def evalue(D):
    mod.eval(); s = []
    with torch.no_grad():
        for ex in D: s.append(giou(mod(ex), ex['cible'])[1])
    mod.train(); return float(torch.cat(s).median())
meilleur, etat, journal, t0, patience = -1, None, [], time.time(), 0
for ep in range(30):
    random.shuffle(tr); L = 0
    for k in range(0, len(tr), 8):
        loss = 0
        for ex in tr[k:k + 8]:
            p = mod(ex); g, _ = giou(p, ex['cible']); loss = loss + (nn.functional.l1_loss(p, ex['cible']) * 4 + (1 - g).mean())
        opt.zero_grad(); loss.backward(); opt.step(); L += float(loss)
    v = evalue(dv); journal.append({'ep': ep, 'perte': L, 'iou_med_dev': v, 's': round(time.time() - t0)}); print(journal[-1], flush=True)
    if v > meilleur: meilleur, etat, patience = v, {k: x.clone() for k, x in mod.state_dict().items()}, 0
    else:
        patience += 1
        if patience >= 4: break
mod.load_state_dict(etat); mod.eval()
for nom, D in (('dev', dv), ('test', te)):
    with torch.no_grad(): P = {ex['id']: (mod(ex) * torch.tensor([ex['Wp'], ex['Hp'], ex['Wp'], ex['Hp']])).round().int().tolist() for ex in D}
    json.dump(P, open(f'{out}/{bras}_{couche}_{nom}.json', 'w'))
json.dump({'bras': bras, 'couche': couche, 'iou_med_dev_meilleur': meilleur, 'journal': journal}, open(f'{out}/{bras}_{couche}_journal.json', 'w'))
