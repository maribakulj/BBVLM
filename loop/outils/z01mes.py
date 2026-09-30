import sys, glob, os, subprocess, re
sys.path.insert(0, '/home/user/BBVLM/loop/outils')
from bilan_adj import reference_adjugee, score
SUS = re.compile('[ͤäöüů]')
tot = {'Z': [], 'S': []}
for z in sorted(glob.glob('z01/*/')):
    n = z.rstrip('/').split('/')[-1]; d = glob.glob(f'o*/{n}/')[0]
    ref, _ = reference_adjugee(d)
    for c in 'ZS':
        r = []
        for f in sorted(glob.glob(f'{z}{c}_*.txt')):
            p2 = subprocess.run([sys.executable, '/home/user/BBVLM/loop/outils/p2.py', f], capture_output=True, text=True).stdout.splitlines()
            s = score(ref, p2, 'glyphe')
            sus = sum(1 for x in s['fautes'] for a in [x.get('ref') or ''] if SUS.search(a) or SUS.search(x.get('lu') or ''))
            r.append((s['editions'], sus))
        tot[c] += [e for e, _ in r]
        print(n[:12], c, 'lectures', [e for e, _ in r], 'lignes à signe suscrit fautives', [x for _, x in r], 'moy %.1f' % (sum(e for e, _ in r) / max(1, len(r))), 'pire', max([e for e, _ in r] or [0]))
print('TOTAL Z', sum(tot['Z']), len(tot['Z']), '| S', sum(tot['S']), len(tot['S']))
