import sys, glob, os, json, re, io, contextlib
sys.path.insert(0, '/home/user/BBVLM/loop/outils'); sys.path[:0] = ['/home/user/BBVLM/src', '/home/user/BBVLM/src/boxers']
import numpy as np
from scipy.optimize import linear_sum_assignment
from g01 import charge
from segeval import iou
S = '/tmp/claude-0/-home-user-BBVLM/84210bd8-ec20-5b45-a7f8-f35608b01c8d/scratchpad'
E = '/home/user/BBVLM/loop/etat_w06/'
SETS = {'crit2': ['o0[789]', 'o1[0-7]'], 'crit18': ['o18'], 'crit23': ['o23'], 'crit24': ['o24'], 'crit25': ['o25'], 'crit26': ['o26'], 'crit27': ['o27'], 'crit28': ['o28']}
tot = {}
for c, pats in SETS.items():
    L = [l for l in open(E + c + '.log') if 'échec' in l and 'CRITERE' not in l]
    ds = [d for p in pats for d in sorted(glob.glob(f'{S}/{p}/*/'))]
    ds = sorted(ds) if c == 'crit2' else ds
    ds = [d for d in ds if (os.path.exists(d + 'p3i_final.txt') or os.path.exists(d + 'p3_final.txt')) and os.path.exists(d + 'kraken_serre.json')]
    for d, l in zip(ds, L):
        nom = d.rstrip('/').split('/')[-1]
        m = re.match(r'(\S+)\s+échec\s+(\d+) ≤0.5c\s+(\S+) pire\s+(\S+) iou (\S+) (\S)', l)
        assert nom.startswith(m.group(1)), (nom, m.group(1))
        ech, pct, pire, io_, ok = int(m.group(2)), float(m.group(3)), float(m.group(4)), float(m.group(5)), m.group(6) == '✓'
        f = d + 'p3i_final.txt' if os.path.exists(d + 'p3i_final.txt') else d + 'p3_final.txt'
        with contextlib.redirect_stdout(io.StringIO()): page, ec = charge(d, f)
        kr = [l['bbox'] for l in json.load(open(d + 'kraken_crit2.json'))['lignes']] if os.path.exists(d + 'kraken_crit2.json') else []
        ref = [ln.line_box for ln in page.lines]
        sans = len(ref)
        if kr and ref:
            M = np.array([[iou(r, k) for k in kr] for r in ref]); a, b = linear_sum_assignment(-M); sans = len(ref) - sum(M[i, j] >= .5 for i, j in zip(a, b))
        autre = max(0, ech - ec - sans)
        geo = (pct < 95) or (pire > 3) or (io_ < .8)
        cause = 'ok' if ok else ('texte' if ec else '') + ('+lignes' if sans else '') + ('+boite' if autre else '') + ('+geometrie' if geo else '')
        cause = cause.strip('+') or 'ok?'
        grp = 'neuves' if c in ('crit26', 'crit27', 'crit28') else 'dev+ecart'
        tot.setdefault(grp, []).append((nom[:22], cause, ec, sans, autre, pct, pire, io_))
for g, X in tot.items():
    from collections import Counter
    print('==', g, len(X), 'pages', Counter(x[1] for x in X).most_common())
    print('   lignes en échec : texte (nb de mots ≠ VT)', sum(x[2] for x in X), '| sans ligne kraken', sum(x[3] for x in X), '| autre', sum(x[4] for x in X))
    for x in X:
        if x[1] != 'ok': print('  ', x)
