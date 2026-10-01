import sys, json, glob, os, re, tempfile
sys.path.insert(0, '/home/user/BBVLM/loop/outils')
from lxml import etree
from olr import mesure, ROLE
from accord import apparie
from cer import vue
S = '/tmp/claude-0/-home-user-BBVLM/84210bd8-ec20-5b45-a7f8-f35608b01c8d/scratchpad'
def lignes_alto(p):
    r = etree.parse(p).getroot(); ns = r.tag.split('}')[0][1:]; out = []
    for tl in r.iter(f'{{{ns}}}TextLine'):
        if tl.get('HPOS') is None: continue
        t = ' '.join(s.get('CONTENT') for s in tl.iter(f'{{{ns}}}String'))
        x, y, w, h = (int(tl.get(k)) for k in ('HPOS', 'VPOS', 'WIDTH', 'HEIGHT')); out.append((t, (x, y, x + w, y + h)))
    return out
def emboite(Z):
    import os
    if os.environ.get('Y01C') != '1': return Z
    aire = lambda z: max(0, z[2]-z[0])*max(0, z[3]-z[1])
    def dedans(a, b):
        i = max(0, min(a[2], b[2])-max(a[0], b[0]))*max(0, min(a[3], b[3])-max(a[1], b[1]))
        return aire(a) > 0 and i/aire(a) >= .9 and aire(b) > aire(a)
    return [a for a in Z if not any(dedans(a, b) for b in Z if b is not a)]
def zone(b, Z):
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    c = [(abs((z[2]-z[0])*(z[3]-z[1])), i) for i, z in enumerate(Z) if z[0] <= cx <= z[2] and z[1] <= cy <= z[3]]
    return min(c)[1] if c else None
def variantes(d):
    L = [l for l in open(d + 'lu_a.txt', encoding='utf-8').read().splitlines()]
    A = lignes_alto(d + 'page.alto.xml'); Z = emboite([z['bbox'] for z in json.load(open(d + 'yolo_zones.json'))['zones']])
    corps = [(k, ROLE.match(l.strip())) for k, l in enumerate(L) if l.strip() and not l.lower().startswith('#') and ROLE.match(l.strip())]
    if not corps: raise ValueError('lecture sans rôles')
    m = apparie([vue(mm.group(3), 'diplo') for _, mm in corps], [vue(t, 'diplo') for t, _ in A])
    t2a = {}
    for j, (t, b) in enumerate(A): t2a.setdefault(vue(t, 'diplo'), b)
    zl = [zone(t2a[m[i]], Z) if i in m and m[i] in t2a else None for i in range(len(corps))]
    out = {'base': list(L), 'a': list(L), 'b': list(L)}
    dern = {}
    for i, (k, mm) in enumerate(corps):
        role, plus, txt = mm.group(1), mm.group(2), mm.group(3)
        p = dern.get(role); dern[role] = i
        if p is None or zl[i] is None or zl[p] is None: continue
        if zl[i] != zl[p]: out['a'][k] = out['b'][k] = f'[{role}+] {txt}'
        else: out['b'][k] = f'[{role}] {txt}'
    return out, sum(z is not None for z in zl), len(zl)
if __name__ == '__main__':
    sets = sys.argv[1:]
    for pat in sets:
        for d in sorted(glob.glob(S + '/' + pat + '/*/')):
            if not all(os.path.exists(d + f) for f in ('lu_a.txt', 'page.alto.xml', 'yolo_zones.json', 'page.xml')): continue
            try: V, nz, n = variantes(d)
            except Exception as e: print(d.split('/')[-2][:14], 'err', e); continue
            res = {}
            for v, L in V.items():
                f = tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8'); f.write('\n'.join(L)); f.close()
                r = mesure(d + 'page.xml', f.name); os.unlink(f.name); res[v] = r
            print(json.dumps({'set': pat, 'page': d.split('/')[-2], 'zonees': nz, 'lignes': n, **{v: [r['f1_meme_region'], r['role_exact'], r['ordre_regions'], r['regions_ref'], r['regions_lues']] for v, r in res.items()}}), flush=True)
