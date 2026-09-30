import re
import sys, glob, os, shutil
sys.path.insert(0, '/home/user/BBVLM/loop/outils')
from p2 import parenthese, fraction
S = os.path.dirname(os.path.abspath(__file__)); ecrit = '--ecrit' in sys.argv
n = 0
for d in sorted(glob.glob(S+'/o*/*/')):
    f = d+'p3i_final.txt' if os.path.exists(d+'p3i_final.txt') else d+'p3_final.txt'
    if not os.path.exists(f): continue
    L = open(f, encoding='utf-8').read().split('\n'); N = []
    for l in L:
        if not l.strip() or l.startswith('#'): N.append(l); continue
        pre = ''
        mm = re.match(r'\[[a-z-]+\+?\] ', l)
        if mm: pre, l = mm.group(0), l[mm.end():]
        m = fraction(parenthese(l))
        if m != l: n += 1; print(d.rstrip('/').split('/')[-1][:14], '|', l[:60], '→', m[:60])
        N.append(pre + m)
    if ecrit and N != L:
        shutil.copy(f, f[:-4] + '_avantR4b.txt'); open(f, 'w', encoding='utf-8').write('\n'.join(N))
print('lignes modifiées', n)
