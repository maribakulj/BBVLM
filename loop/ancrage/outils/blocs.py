"""A1 — blocs traçables OCR-D (CONTRAT.md v1). usage : python blocs.py SORTIE [max_pages]
Écrit SORTIE/manifest.jsonl (un bloc par ligne) et SORTIE/crops/*.png ; images de page supprimées après usage."""
import hashlib, json, os, sys, unicodedata, urllib.request
import cv2, numpy as np
from lxml import etree
REV = '481f7235acfc1f78e88b3c2f22f551595c3f2032'
BASE = f'https://raw.githubusercontent.com/OCR-D/OCR-D-GT-VD-SBB/{REV}/'
def get(u):
    for k in range(4):
        try:
            with urllib.request.urlopen(u, timeout=120) as r: return r.read()
        except Exception:
            if k == 3: raise
def h(s): return int(hashlib.sha256(s.encode()).hexdigest(), 16)
def partition(oeuvre):
    v = h(oeuvre) % 20
    return 'test' if v < 4 else 'dev' if v < 7 else 'train'
def bbox(el, N):
    pts = [tuple(map(int, q.split(','))) for q in el.find('p:Coords', N).get('points').split()]
    xs, ys = [a for a, _ in pts], [b for _, b in pts]
    return [min(xs), min(ys), max(xs) + 1, max(ys) + 1]          # semi-ouvert
def blocs_page(xml_path):
    r = etree.fromstring(get(BASE + xml_path)); N = {'p': r.tag.split('}')[0][1:]}
    out, exclues = [], 0
    for tr in r.findall('.//p:TextRegion', N):
        L = []
        for tl in tr.findall('p:TextLine', N):
            u = tl.find('p:TextEquiv/p:Unicode', N); t = unicodedata.normalize('NFC', (u.text or '') if u is not None else '')
            ws = []
            for w in tl.findall('p:Word', N):
                wu = w.find('p:TextEquiv/p:Unicode', N)
                if wu is None or w.find('p:Coords', N) is None: ws = None; break
                ws.append((unicodedata.normalize('NFC', wu.text or ''), bbox(w, N)))
            if not t.strip() or not ws or ' '.join(x for x, _ in ws) != t: exclues += 1; L.append(None); continue
            L.append({'texte': t, 'boite': bbox(tl, N), 'mots': ws})
        # suites de lignes valides consécutives, découpées en blocs de 3-8 lignes (tirage déterministe)
        run = []
        for x in L + [None]:
            if x is not None: run.append(x); continue
            i = 0
            while len(run) - i >= 3:
                n = 3 + h(f'{xml_path}|{tr.get("id")}|{i}') % 6; n = min(n, len(run) - i)
                if len(run) - i - n in (1, 2): n = len(run) - i if len(run) - i <= 8 else n - (3 - (len(run) - i - n))
                out.append((tr.get('id'), tr.get('type'), run[i:i + n])); i += n
            run = []
    return r, out, exclues
def main(sortie, maxp=10**9):
    os.makedirs(sortie + '/crops', exist_ok=True)
    pages = [l.strip() for l in open(os.path.dirname(os.path.abspath(__file__)) + '/gt_pages.txt')][:maxp]
    fait = set()
    if os.path.exists(sortie + '/manifest.jsonl'):
        fait = {json.loads(l)['page'] for l in open(sortie + '/manifest.jsonl')}
    man = open(sortie + '/manifest.jsonl', 'a', encoding='utf-8'); stats = open(sortie + '/pages.jsonl', 'a')
    for xp in pages:
        if xp in fait: continue
        oeuvre = xp.split('/')[1]; pid = xp.split('_')[-1][:-4]
        _, B, exc = blocs_page(xp)
        img = cv2.imdecode(np.frombuffer(get(BASE + f'data/{oeuvre}/OCR-D-IMG/OCR-D-IMG_{pid}.tif'), np.uint8), cv2.IMREAD_COLOR)
        H, W = img.shape[:2]
        for k, (rid, rtype, lignes) in enumerate(B):
            x0 = max(0, min(l['boite'][0] for l in lignes) - 16); y0 = max(0, min(l['boite'][1] for l in lignes) - 16)
            x1 = min(W, max(l['boite'][2] for l in lignes) + 16); y1 = min(H, max(l['boite'][3] for l in lignes) + 16)
            texte = '\n'.join(l['texte'] for l in lignes); vt = hashlib.sha256(texte.encode()).hexdigest()[:16]
            occ, pos = [], 0
            for li, l in enumerate(lignes):
                for wi, (w, b) in enumerate(l['mots']):
                    d = texte.index(w, pos); occ.append({'ligne': li, 'mot': wi, 'debut': d, 'fin': d + len(w), 'texte': w, 'boite_page': b}); pos = d + len(w)
            bid = f'{oeuvre}_{pid}_{rid}_{k}'
            cv2.imwrite(f'{sortie}/crops/{bid}.png', img[y0:y1, x0:x1])
            man.write(json.dumps({'id': bid, 'page': xp, 'oeuvre': oeuvre, 'partition': partition(oeuvre), 'region': rid, 'type': rtype,
                                  'version_texte': vt, 'texte': texte, 'crop': [x0, y0, x1, y1], 'page_wh': [W, H],
                                  'lignes': [l['boite'] for l in lignes], 'occurrences': occ}, ensure_ascii=False) + '\n')
        stats.write(json.dumps({'page': xp, 'blocs': len(B), 'lignes_exclues': exc}) + '\n'); man.flush(); stats.flush()
        print(xp, len(B), exc, flush=True)
if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 10**9)
