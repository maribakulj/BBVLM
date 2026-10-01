"""A1 — tests du contrat (occurrences, boîtes, transformations). usage : python test_a1.py MANIFESTE_DIR"""
import json, sys, hashlib, math
import cv2
D = sys.argv[1]; M = [json.loads(l) for l in open(D + '/manifest.jsonl', encoding='utf-8')]
err = []
def smart_resize(h, w, f=32, mn=4*32*32, mx=16384*32*32):      # convention Qwen3-VL (processor), vérifiée en E0
    hb, wb = max(f, round(h / f) * f), max(f, round(w / f) * f)
    if hb * wb > mx: b = math.sqrt(h * w / mx); hb, wb = math.floor(h / b / f) * f, math.floor(w / b / f) * f
    elif hb * wb < mn: b = math.sqrt(mn / (h * w)); hb, wb = math.ceil(h * b / f) * f, math.ceil(w * b / f) * f
    return hb, wb
for m in M:
    t = m['texte']
    if hashlib.sha256(t.encode()).hexdigest()[:16] != m['version_texte']: err.append((m['id'], 'version'))
    lignes = t.split('\n')
    if len(lignes) != len(m['lignes']) or not 3 <= len(lignes) <= 8: err.append((m['id'], 'nb lignes', len(lignes)))
    for o in m['occurrences']:
        if t[o['debut']:o['fin']] != o['texte']: err.append((m['id'], 'offset', o))
    for li, l in enumerate(lignes):
        if ' '.join(o['texte'] for o in m['occurrences'] if o['ligne'] == li) != l: err.append((m['id'], 'jonction', li))
    x0, y0, x1, y1 = m['crop']
    for o in m['occurrences']:
        b = o['boite_page']
        if not (x0 <= b[0] < b[2] <= x1 and y0 <= b[1] < b[3] <= y1): err.append((m['id'], 'hors crop', o['texte']))
        c = [b[0] - x0, b[1] - y0, b[2] - x0, b[3] - y0]                       # page → crop → page
        if [c[0] + x0, c[1] + y0, c[2] + x0, c[3] + y0] != b: err.append((m['id'], 'aller-retour'))
    im = cv2.imread(f"{D}/crops/{m['id']}.png")
    if im is None or im.shape[:2] != (y1 - y0, x1 - x0): err.append((m['id'], 'crop dims'))
    else:
        H, W = im.shape[:2]; hb, wb = smart_resize(H, W)
        for o in m['occurrences'][:3]:                                          # crop → entrée modèle → crop (sans arrondi)
            b = o['boite_page']; c = [b[0] - x0, b[1] - y0, b[2] - x0, b[3] - y0]
            e = [c[0] * wb / W, c[1] * hb / H, c[2] * wb / W, c[3] * hb / H]
            r = [e[0] * W / wb, e[1] * H / hb, e[2] * W / wb, e[3] * H / hb]
            if max(abs(a - b) for a, b in zip(r, c)) > 1e-9: err.append((m['id'], 'aller-retour modèle'))
print('blocs', len(M), 'occurrences', sum(len(m['occurrences']) for m in M), 'erreurs', len(err))
for e in err[:20]: print(e)
sys.exit(1 if err else 0)
