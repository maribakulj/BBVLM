import sys, glob, subprocess
sys.path.insert(0, '/home/user/BBVLM/loop/outils')
from bilan_adj import reference_adjugee, score
from accord import apparie
from cer import lev
def p2(f): return [l for l in subprocess.run([sys.executable, '/home/user/BBVLM/loop/outils/p2.py', f], capture_output=True, text=True).stdout.splitlines() if l.strip()]
for z in sorted(glob.glob('z01/*/') + glob.glob('z02/*/')):
    n = z.rstrip('/').split('/')[-1]; d = glob.glob(f'o*/{n}/')[0]; ref, _ = reference_adjugee(d)
    R = [p2(f) for f in sorted(glob.glob(z + 'Z_*.txt'))]
    piv = R[0]; M = [apparie(piv, r) for r in R[1:]]
    vote = []
    for i, l in enumerate(piv):
        c = [l] + [m[i] for m in M if i in m]
        vote.append(min(c, key=lambda x: sum(lev(x, y) for y in c)))
    ind = [score(ref, r, 'glyphe')['editions'] for r in R]
    fin = score(ref, open(glob.glob(d + 'p3i_final.txt')[0] if glob.glob(d + 'p3i_final.txt') else d + 'p3_final.txt').read().splitlines(), 'glyphe')['editions']
    print(n[:12], 'lectures seules', ind, '| vote médian', score(ref, vote, 'glyphe')['editions'], '| chaîne actuelle', fin)
