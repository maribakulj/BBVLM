import sys, glob, subprocess
sys.path.insert(0, '/home/user/BBVLM/loop/outils')
from bilan_adj import reference_adjugee, score
def p2(f): return subprocess.run([sys.executable, '/home/user/BBVLM/loop/outils/p2.py', f], capture_output=True, text=True).stdout.splitlines()
ok = True; tO = tN = 0
for z in sorted(glob.glob('z01/*/') + glob.glob('z02/*/')):
    n = z.rstrip('/').split('/')[-1]; d = glob.glob(f'o*/{n}/')[0]; ref, _ = reference_adjugee(d)
    O = [score(ref, p2(f), 'glyphe')['editions'] for f in sorted(glob.glob(z + 'Z_*.txt'))]
    N = [score(ref, p2(f), 'glyphe')['editions'] for f in sorted(glob.glob(z + 'N_*.txt'))]
    if not N: continue
    mo, mn = sum(O) / len(O), sum(N) / len(N); c = mn <= 1.2 * mo + 1 and max(N) <= max(O) + 3; ok &= c; tO += mo; tN += mn
    print(n[:12], 'Opus', O, 'moy %.1f' % mo, '| Sonnet', N, 'moy %.1f' % mn, '| tenu' if c else '| ÉCHEC')
print('moyennes cumulées Opus %.1f Sonnet %.1f' % (tO, tN), 'H-S02', 'TENUE' if ok else 'REJETÉE')
