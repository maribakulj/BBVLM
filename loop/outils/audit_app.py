import sys, json, os, collections
sys.path.insert(0, '/home/user/BBVLM/loop/outils')
from cer import vue
A = 'audit2627/'; carte = json.load(open(A + 'carte.json'))
T = collections.defaultdict(list)
for f in ('lot0_1', 'lot0_2', 'lot1_1', 'lot1_2'):
    for x in json.load(open(A + f + '.json')): T[x['image'][:-4]].append(x['texte'])
stat = collections.Counter(); ann = collections.defaultdict(list)
for c, (d, i) in sorted(carte.items()):
    cle = {k['id']: k for k in json.load(open(d + '/adj/cle.json'))}[i]
    v = {k['id']: k for k in json.load(open(d + '/adj/verdicts.json'))}[i]
    vt = vue(cle['X'] if cle['_ref'] == 'X' else cle['Y'], 'glyphe'); adj = vue(v['texte_correct'], 'glyphe')
    t = [vue(x, 'glyphe') for x in T[c]]
    if len(t) == 2 and t[0] == t[1] == vt: r = 'annulé'; ann[d].append(i)
    elif len(t) == 2 and t[0] == t[1] == adj: r = 'confirmé'
    else: r = 'indécis'
    stat[r] += 1
    if r != 'confirmé': print(r, d.split('/')[-1][:12], i, '| VT:', vt[:50], '| ADJ:', adj[:50], '| R:', [x[:50] for x in t])
print(dict(stat))
if '--ecrit' in sys.argv:
    for d, ids in ann.items():
        p = d + '/adj/annule.json'; old = json.load(open(p)) if os.path.exists(p) else []
        json.dump(sorted(set(old) | set(ids)), open(p, 'w')); print('annule.json', d.split('/')[-1], ids)
