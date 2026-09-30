"""S05 — placer les lignes lues par ancrage OCR (L10 : Feng & Manmatha 2006,
Yalniz & Manmatha 2011 ; astra A53).

Tesseract (tessdata_best, script/Fraktur ou Latin) lit chaque ligne kraken ;
ce texte n'est jamais publié, il sert d'ancre. Les lignes du lecteur sont
appariées aux lignes kraken par similarité de texte (hongrois, vue réduite :
minuscules, ſ→s, lettres et chiffres seuls), avec un léger terme de rang pour
départager les lignes identiques (« 2. — 6. » dans deux blocs). Les paires trop
dissemblables sont rejetées ; les lignes restées sans ancre sont placées par
l'alignement par largeur (aligne.py) sur les lignes kraken restantes.
Cache : DOSSIER/ancres_tesseract.json (clé = boîte).
"""
import json, os, re, subprocess, unicodedata
import numpy as np
import cv2
from scipy.optimize import linear_sum_assignment
from cer import lev

TESSDATA = os.environ.get('BBVLM_TESSDATA', '/tmp/claude-0/-home-user-BBVLM/84210bd8-ec20-5b45-a7f8-f35608b01c8d/scratchpad/tessdata')
SEUIL = 0.6          # distance d'édition normalisée maximale d'une ancre
RANG = 0.15          # poids du rang (départage seulement)


def reduit(t):
    t = unicodedata.normalize('NFKD', t.replace('ſ', 's').lower())
    return re.sub(r'[^a-z0-9]', '', t)


def lit_lignes(dossier, boites, ecriture):
    cache_f = f'{dossier}/ancres_tesseract.json'
    try: cache = json.load(open(cache_f))
    except (FileNotFoundError, ValueError): cache = {}
    lang = 'script/Fraktur' if ecriture == 'fraktur' else 'lat'   # un modèle par écriture (3 modèles : 9 s/ligne)
    g = None; out = []
    for b in boites:
        k = f'{lang}|{b[0]},{b[1]},{b[2]},{b[3]}'
        if k not in cache:
            if g is None: g = cv2.imread(f'{dossier}/page.png', cv2.IMREAD_GRAYSCALE)
            x0, y0, x1, y1 = (int(v) for v in b)
            crop = g[max(0, y0-4):y1+5, max(0, x0-4):x1+5]
            if crop.size == 0: cache[k] = ''; continue
            ok, png = cv2.imencode('.png', crop)
            r = subprocess.run(['tesseract', 'stdin', 'stdout', '--tessdata-dir', TESSDATA, '-l', lang, '--psm', '7'],
                               input=png.tobytes(), capture_output=True, env={**os.environ, 'OMP_THREAD_LIMIT': '1'})
            cache[k] = r.stdout.decode('utf-8', 'replace').strip()
        out.append(cache[k])
    json.dump(cache, open(cache_f, 'w'), ensure_ascii=False)
    return out


def aligne_ancre(textes, boites, ocr):
    """Rend {indice_texte: indice_boite}."""
    from aligne import aligne, ordre_lecture
    T, K = len(textes), len(boites)
    if not T or not K: return {}
    rang_k = {k: r for r, k in enumerate(ordre_lecture(boites))}
    A = [reduit(t) for t in textes]; B = [reduit(o) for o in ocr]
    C = np.full((T, K), 9.0)
    for i in range(T):
        for k in range(K):
            if len(A[i]) < 2 or len(B[k]) < 2: continue
            d = lev(A[i], B[k]) / max(len(A[i]), len(B[k]))
            C[i, k] = d + RANG * abs(i/T - rang_k[k]/K)
    ri, ki = linear_sum_assignment(C)
    res = {int(i): int(k) for i, k in zip(ri, ki) if C[i, k] - RANG * abs(i/T - rang_k[k]/K) <= SEUIL}
    # lignes sans ancre : alignement par largeur sur les lignes kraken libres
    libres_t = [i for i in range(T) if i not in res]
    libres_k = [k for k in range(K) if k not in set(res.values())]
    if libres_t and libres_k:
        a = aligne([textes[i] for i in libres_t], [boites[k] for k in libres_k])
        import os
        if os.environ.get('BBVLM_S12') == '1' and res:
            # S12 : le repli par largeur ne pose pas une ligne lue sur une boîte 3 fois trop étroite
            # pour son nombre de signes (référence : lignes ancrées de la page) — sinon non placée
            def _r(i, k):
                b = boites[k]; return (b[2] - b[0]) / max(1, len(textes[i].replace(' ', ''))) / max(1, b[3] - b[1])
            med = float(np.median([_r(i, k) for i, k in res.items()]))
            a = {it: ik for it, ik in a.items() if med / 3 <= _r(libres_t[it], libres_k[ik])}   # borne basse seule : les titres espacés (« ) 152 ( ») sont larges à bon droit
        for it, ik in a.items(): res[libres_t[it]] = libres_k[ik]
    return res
