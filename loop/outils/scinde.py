"""S08 — scinder une ligne kraken qui porte deux lignes lues (coupe guidée par le texte).

S07 (gouttières géométriques) a échoué : la gouttière de deux colonnes de notes
a la taille des blancs d'un titre espacé. Le texte tranche : si l'OCR
d'ancrage (Tesseract, S05) d'une ligne kraken ressemble bien mieux à la
concaténation de deux lignes lues consécutives (A puis B) qu'à n'importe
quelle ligne lue seule, la ligne kraken porte les deux. On la coupe au blanc
(≥ 0,15 h) le plus large dans la fenêtre autour de la proportion |A|/(|A|+|B|)
de sa largeur d'encre ; chaque morceau est resserré sur son encre.
"""
import os
import numpy as np, cv2
from cer import lev
from ancre import reduit

GAIN = float(os.environ.get('BBVLM_SCINDE_GAIN', '0.15'))   # distance seule − distance concaténée
MAXD = float(os.environ.get('BBVLM_SCINDE_MAXD', '0.35'))   # distance concaténée maximale


PORTEE = int(os.environ.get('BBVLM_SCINDE_PORTEE', '6'))


def _d(a, b): return lev(a, b) / max(1, len(a), len(b))


def scinde(gray, boites, ocr, textes):
    R = [reduit(t) for t in textes]
    out = []
    for b, o in zip(boites, ocr):
        ro = reduit(o)
        if len(ro) < 8: out.append(b); continue
        seul = min((_d(ro, r) for r in R if len(r) >= 2), default=1)
        meil = None
        for i in range(len(R)):
            for j in range(max(0, i - PORTEE), min(len(R), i + PORTEE + 1)):   # notes en colonnes : A et B non consécutives
                if i == j or len(R[i]) < 3 or len(R[j]) < 3: continue
                if abs(len(R[i]) + len(R[j]) - len(ro)) > 0.4 * len(ro): continue
                dc = _d(ro, R[i] + R[j])
                if meil is None or dc < meil[0]: meil = (dc, len(R[i]) / (len(R[i]) + len(R[j])))
        if meil is None or meil[0] > MAXD or seul - meil[0] < GAIN: out.append(b); continue
        x0, y0, x1, y1 = map(int, b); h = y1 - y0
        crop = gray[y0:y1+1, x0:x1+1]
        _, bw = cv2.threshold(crop, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        cols = np.nonzero(bw.sum(0))[0]
        if len(cols) < 10: out.append(b); continue
        xa, xb = cols[0], cols[-1]
        cible = xa + meil[1] * (xb - xa)
        vide = bw.sum(0) == 0
        runs, i = [], xa
        while i <= xb:
            if vide[i]:
                j = i
                while j <= xb and vide[j]: j += 1
                if j - i >= 0.15 * h: runs.append((i, j - 1))
                i = j
            else: i += 1
        fen = [(z - a, (a + z) // 2) for a, z in runs if abs((a + z) / 2 - cible) <= 0.15 * (xb - xa)]
        if not fen: out.append(b); continue
        xc = max(fen)[1]
        parts = []
        for u, v in ((xa, xc), (xc + 1, xb)):
            ys, xs = np.nonzero(bw[:, u:v+1])
            if len(xs) < 10: continue
            parts.append([int(x0+u+xs.min()), int(y0+ys.min()), int(x0+u+xs.max()), int(y0+ys.max())])
        out += parts if len(parts) == 2 else [b]
    return out


def renvois(gray, boites, ocr, textes, dossier=None, lang='script/Fraktur'):
    """S08c — colonnes de renvois chiffrés alignés à droite (tables des matières).

    Si la lecture contient ≥ 2 lignes purement chiffrées (« 1. — 6. »), une ligne
    kraken large (≥ 6 h) dont l'OCR se termine par des chiffres est relue par
    Tesseract avec boîtes de mots ; la suite finale de jetons chiffrés (chiffres,
    points, tirets) est détachée si elle commence après la moitié de la ligne :
    le renvoi devient une ligne candidate que l'ancrage S05 peut recevoir.
    Garde-fou : ses chiffres doivent être ceux d'une ligne chiffrée de la lecture
    (sinon « … Beſatzung aus 500 » serait coupé, briedefra).
    Les blancs d'encre seuls ne suffisent pas : ceux du renvoi (« 1. — 6. »)
    sont aussi larges que celui qui le sépare du texte (mesuré sur 852691769).
    """
    import re, json, os
    from mots_tess import mots_ligne
    num = re.compile(r'[\d\s.,—–\-:;]+')
    chif = lambda t: ''.join(c for c in t if c.isdigit())
    lus = {chif(t) for t in textes if num.fullmatch(t.strip() or 'x')}
    if len(lus) < 2: return boites
    cf = f'{dossier}/mots_tesseract.json' if dossier else None
    cache = json.load(open(cf)) if cf and os.path.exists(cf) else {}
    out = []
    for b, o in zip(boites, ocr):
        x0, y0, x1, y1 = map(int, b); h = y1 - y0
        if not re.search(r'\d[\s.,]*$', o or '') or (x1 - x0) < 6 * h:
            out.append(b); continue
        mots = mots_ligne(gray, b, lang, cache, f'{lang}|{x0},{y0},{x1},{y1}')
        k = len(mots)
        while k > 0 and num.fullmatch(mots[k-1][0]): k -= 1
        if k == 0 or k == len(mots) or not any(c.isdigit() for m in mots[k:] for c in m[0]) \
           or mots[k][1] < x0 + 0.5 * (x1 - x0) or chif(''.join(m[0] for m in mots[k:])) not in lus:
            out.append(b); continue
        cut = (mots[k-1][2] + mots[k][1]) // 2
        crop = gray[y0:y1+1, x0:x1+1]
        _, bw = cv2.threshold(crop, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        parts = []
        for u, v in ((0, cut - x0), (cut - x0 + 1, x1 - x0)):
            ys, xs = np.nonzero(bw[:, u:v+1])
            if len(xs) < 10: continue
            parts.append([int(x0+u+xs.min()), int(y0+ys.min()), int(x0+u+xs.max()), int(y0+ys.max())])
        out += parts if len(parts) == 2 else [b]
    if cf: json.dump(cache, open(cf, 'w'))
    return out
