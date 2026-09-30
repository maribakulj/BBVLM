# T08 : signal gratuit de soudure/coupure — nombre de mots lu ≠ nombre de mots Calamari / Tesseract sur la même ligne
import sys, glob, os, json, difflib
sys.path.insert(0, '/home/user/BBVLM/loop/outils')
import g01
from lxml import etree
S = os.path.dirname(os.path.abspath(__file__))
def nm(s): return len(s.split())
tot = {'lignes': 0, 'drapeau_cal': 0, 'drapeau_tes': 0, 'drapeau_deux': 0, 'echec': 0, 'echec_cal': 0, 'echec_tes': 0, 'echec_deux': 0, 'ok_deux': 0}
for d in sorted(glob.glob(S+'/o0[789]/*/') + glob.glob(S+'/o1[0-8]/*/') + glob.glob(S+'/o2[345]/*/')):
    f = d+'p3i_final.txt' if os.path.exists(d+'p3i_final.txt') else d+'p3_final.txt'
    if not os.path.exists(f) or not os.path.exists(d+'kraken_serre.json'): continue
    lu = [l for l in open(f, encoding='utf-8').read().splitlines() if l.strip() and not l.startswith('#')]
    try: cal = [v['s'] for v in json.load(open(d+'calamari_bin.json')).values()]
    except Exception: cal = []
    try: tes = [' '.join(w[0] for w in v) for v in json.load(open(d+'mots_tesseract.json')).values()]
    except Exception: tes = []
    ref = json.load(open(d+'ref.json')); idx = [i for i, x in enumerate(ref) if x.strip()]
    m = g01.apparie([g01.vue(ref[i], 'diplo') for i in idx], lu)
    r = etree.parse(d+'page.xml').getroot(); N = {'p': r.tag.split('}')[0][1:]}; tls = r.findall('.//p:TextLine', N)
    vt = {}
    for k, i in enumerate(idx):
        ws = [w for w in tls[i].findall('p:Word', N)]
        if k in m: vt[m[k]] = len(ws)
    def proche(l, L):
        b, bs = None, .5
        for x in L:
            s = difflib.SequenceMatcher(None, l.replace(' ', ''), x.replace(' ', '')).ratio()
            if s > bs: b, bs = x, s
        return b
    for l in lu:
        if nm(l) < 2 or l not in vt: continue
        c, t = proche(l, cal), proche(l, tes)
        fc = c is not None and nm(c) != nm(l); ft = t is not None and nm(t) != nm(l)
        e = vt[l] != nm(l)
        tot['lignes'] += 1; tot['drapeau_cal'] += fc; tot['drapeau_tes'] += ft; tot['drapeau_deux'] += fc and ft
        tot['echec'] += e; tot['echec_cal'] += e and fc; tot['echec_tes'] += e and ft; tot['echec_deux'] += e and fc and ft
        if e: print(d.rstrip('/').split('/')[-1][:12], 'cal', fc, 'tes', ft, '|', l[:50], '| C:', (c or '')[:50])
print(tot)
