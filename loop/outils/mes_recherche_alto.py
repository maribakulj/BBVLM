import sys, glob, os, json, statistics as st
sys.path.insert(0, '/home/user/BBVLM/loop/outils'); sys.path[:0] = ['/home/user/BBVLM/src', '/home/user/BBVLM/src/boxers']
from recherche_adj import mesure as _m2
import recherche
def mesure(alto, d):
    import os
    return _m2(alto, d) if os.path.exists(d + 'adj/verdicts.json') else recherche.mesure(alto, d + 'page.xml')
S = '/tmp/claude-0/-home-user-BBVLM/84210bd8-ec20-5b45-a7f8-f35608b01c8d/scratchpad'
R = {}
for d in sorted(glob.glob(S+'/o0[789]/*/') + glob.glob(S+'/o1[0-8]/*/') + glob.glob(S+'/o2[345678]/*/')):
    if not os.path.exists(d+'page.alto.sr6.xml'): continue
    n = d.rstrip('/').split('/')[-1]; grp = 'neuves' if '/o2' in d and d.split('/')[-3] in ('o26','o27','o28') else 'dev+ecart'
    a = mesure(d+'page.alto.sr4.xml', d)['rappel'] if os.path.exists(d+'page.alto.sr4.xml') else None
    b = mesure(d+'page.alto.sr6.xml', d)['rappel']
    R[n] = (grp, a, b)
for g in ('dev+ecart', 'neuves'):
    X = [v for v in R.values() if v[0] == g]
    A = [v[1] for v in X if v[1] is not None]; B = [v[2] for v in X]
    print(g, len(X), 'pages | sr4 méd', st.median(A) if A else None, '≥0,95', sum(a >= .95 for a in A), '| sr5 méd', round(st.median(B), 4), '≥0,95', sum(b >= .95 for b in B), '| pire sr5', min(B))
for n, (g, a, b) in sorted(R.items(), key=lambda x: (x[1][2] - (x[1][1] or x[1][2]))):
    if a is not None and abs(b - a) > .005: print('  ', g, n[:24], a, '→', b)
json.dump(R, open(S + '/mes_sr6.json', 'w'))
