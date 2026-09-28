"""Exactitude de l'alignement lecture→kraken, mesurée contre la référence."""
import json, sys, glob
from aligne import aligne
from accord import apparie
from cer import vue
from segeval import iou

for arg in sys.argv[1:]:
    d, lec = arg.split('=')
    ref = json.load(open(f'{d}/ref.json')); rb = json.load(open(f'{d}/ref_boites.json'))
    kr = [l['bbox'] for l in json.load(open(f'{d}/kraken_serre.json'))['lignes']]
    lu = [l for l in open(lec, encoding='utf-8').read().splitlines() if l.strip() and not l.startswith('#')]
    idx = [i for i, x in enumerate(ref) if x.strip()]
    m_ref = apparie([vue(ref[i], 'diplo') for i in idx], [vue(x, 'diplo') for x in lu])   # ligne réf -> texte lu
    lu_vers_ref = {lu.index(t) if t in lu else None: idx[k] for k, t in m_ref.items()}
    a = aligne(lu, kr)
    ok = tot = 0
    for t, j in a.items():
        r = lu_vers_ref.get(t)
        if r is None: continue
        tot += 1; ok += iou(kr[j], rb[r]) >= .3
    print(f"{d.rstrip('/').split('/')[-1][:10]:10s} lignes lues {len(lu)} kraken {len(kr)} alignées {len(a)} correctes {ok}/{tot}")
