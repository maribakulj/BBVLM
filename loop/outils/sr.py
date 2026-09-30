"""SR — segmentation par reconnaissance guidée par le texte connu (L36).

score(texte, région) = −log p(texte | région) / (nb de caractères + 1), par la perte CTC
du modèle W05 (CATMuS-Print) ; plus bas = la région explique mieux la ligne lue.
"""
import numpy as np


def etiquettes(texte):
    from w05 import modele, encode
    m = modele(); lab = []
    for ch in texte:
        lab += encode(m, ch)
    return lab


def score(gray, box, texte):
    import torch
    from w05 import emissions
    try: lp = emissions(gray, box)[0]
    except Exception: return float('inf')        # région illisible pour le modèle (kraken : net_scale absent)
    lab = etiquettes(texte)
    if not lab or lp.shape[0] < len(lab): return float('inf')
    t = torch.from_numpy(np.ascontiguousarray(lp, dtype=np.float32)).unsqueeze(1)      # (T, 1, C)
    lab_t = torch.tensor([lab], dtype=torch.long)
    L = torch.nn.functional.ctc_loss(t, lab_t, torch.tensor([lp.shape[0]]), torch.tensor([len(lab)]),
                                     blank=0, reduction='sum', zero_infinity=False)
    return float(L) / (len(texte) + 1)


def _meme_bande(a, b):
    return min(a[3], b[3]) - max(a[1], b[1]) >= .5 * min(a[3] - a[1], b[3] - b[1])


def _union(p, q):
    return [min(p[0], q[0]), min(p[1], q[1]), max(p[2], q[2]), max(p[3], q[3])]


def _recouvre(a, b, f=.5):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return ix * iy > f * min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))


def scissions(gray, boites, fh=1.6, creux=.1, im=None):
    """boîtes trop hautes (≥ fh × hauteur médiane) : bandes = suites de rangées encrées
    (encre sombre < Otsu, neutre si l'image couleur est fournie, ≥ max(1 % de la largeur,
    creux × pic du profil)) ; candidates = chaque bande et chaque suite contiguë de bandes
    (hors la boîte entière)"""
    import cv2
    B = [list(map(int, b)) for b in boites]
    if not B: return []
    hm = float(np.median([b[3] - b[1] for b in B])); out = []
    for b in B:
        h = b[3] - b[1]
        if h < fh * hm: continue
        x0, y0, x1, y1 = max(0, b[0]), max(0, b[1]), b[2], b[3]
        c = gray[y0:y1, x0:x1]
        if c.size == 0: continue
        m = c < cv2.threshold(c, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[0]
        if im is not None:
            rgb = im[y0:y1, x0:x1].astype(int); m &= (rgb.max(2) - rgb.min(2)) < 60
        p = np.convolve(m.sum(1).astype(float), np.ones(3) / 3, mode='same')
        haut = p >= max(.01 * (x1 - x0), creux * np.percentile(p, 95))
        bandes, y = [], 0
        while y < len(haut):
            if haut[y]:
                z = y
                while z < len(haut) and haut[z]: z += 1
                if z - y >= 3:
                    # jambages et points : la bande s'étend tant que la rangée voisine porte un peu d'encre
                    ya, yb = y, z
                    while ya > 0 and m[ya - 1].sum() >= 2: ya -= 1
                    while yb < len(haut) and m[yb].sum() >= 2: yb += 1
                    bandes.append((ya, yb))
                y = z
            else: y += 1
        bandes = sorted(set(bandes))
        for a in range(len(bandes)):
            for e in range(a, len(bandes)):
                ya, yb = bandes[a][0], bandes[e][1]
                if yb - ya < .4 * hm or (ya <= 1 and yb >= h - 1): continue
                out.append((b[0], y0 + ya, b[2], y0 + yb))
    return list(dict.fromkeys(out))


def extensions(gray, boites, im=None, saut=3.0, haut=.8, cibles=None):
    """boîtes prolongées à l'encre voisine (encre sombre, neutre si couleur) : à gauche et à
    droite dans la bande de la ligne (sauts de blanc ≤ saut × h, arrêt devant une autre boîte),
    vers le haut et le bas (rangées encrées contiguës, ≤ haut × h) ; toutes combinaisons"""
    import cv2
    B = [list(map(int, b)) for b in boites]; out = []
    H, W = gray.shape
    for n, b in enumerate(B):
        if cibles is not None and n not in cibles: continue
        x0, y0, x1, y1 = b; h = max(1, y1 - y0)
        # masque d'encre de la bande élargie
        yy0, yy1 = max(0, y0 - int(haut * h)), min(H, y1 + int(haut * h))
        c = gray[yy0:yy1]
        m = c < cv2.threshold(gray[y0:y1, max(0, x0):x1], 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[0]
        if im is not None:
            rgb = im[yy0:yy1].astype(int); m &= (rgb.max(2) - rgb.min(2)) < 60
        bande = m[y0 - yy0:y1 - yy0]
        col = bande.sum(0) >= 2
        autres = [a for k, a in enumerate(B) if k != n and min(a[3], y1) - max(a[1], y0) > .3 * h]
        plein = bande.mean(0) > .6          # bord de page, filet vertical : mur
        def mur_g(x): return plein[x] or any(a[0] <= x <= a[2] for a in autres)
        # gauche
        gx, x, blanc = x0, x0 - 1, 0
        while x >= 0 and blanc <= saut * h and not mur_g(x):
            if col[x]: gx, blanc = x, 0
            else: blanc += 1
            x -= 1
        dx, x, blanc = x1, x1, 0
        while x < W and blanc <= saut * h and not mur_g(x):
            if col[x]: dx, blanc = x + 1, 0
            else: blanc += 1
            x += 1
        # haut / bas : rangées encrées contiguës au-dessus et au-dessous, sur les colonnes de la boîte
        rows = m[:, max(0, gx):dx].sum(1) >= 2
        hy, y = y0, y0 - yy0 - 1
        while y >= 0 and rows[y]: hy = yy0 + y; y -= 1
        by, y = y1, y1 - yy0
        while y < len(rows) and rows[y]: by = yy0 + y + 1; y += 1
        for xa in {x0, gx}:
            for xb in {x1, dx}:
                for ya in {y0, hy}:
                    for yb in {y1, by}:
                        if (xa, ya, xb, yb) != (x0, y0, x1, y1): out.append((xa, ya, xb, yb))
    return list(dict.fromkeys(out))


def resserre(dossier, boites, gain=.15):
    """boîtes resserrées verticalement à l'encre neutre et sombre (exclut tampons et encres
    colorées : pixel sombre (< Otsu du crop) et peu chromatique (max-min RGB < 60)) ;
    gardées si la hauteur baisse d'au moins `gain`"""
    import cv2
    im = cv2.imread(f'{dossier}/page.png', cv2.IMREAD_COLOR)
    if im is None: return []
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); out = []
    for b in [list(map(int, b)) for b in boites]:
        x0, y0, x1, y1 = max(0, b[0]), max(0, b[1]), b[2], b[3]
        c = g[y0:y1, x0:x1]
        if c.size == 0: continue
        t = cv2.threshold(c, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[0]
        rgb = im[y0:y1, x0:x1].astype(int)
        m = (c < t) & ((rgb.max(2) - rgb.min(2)) < 60)
        r = np.where(m.sum(1) >= .01 * (x1 - x0))[0]
        if len(r) < 3: continue
        ny0, ny1 = y0 + int(r[0]), y0 + int(r[-1]) + 1
        if (ny1 - ny0) <= (1 - gain) * (y1 - y0): out.append((b[0], ny0, b[2], ny1))
    return out


def candidates(boites, nmax=3, extra=()):
    """boîtes + unions de 2..nmax boîtes voisines d'une même bande (aucune boîte entre elles)
    + candidates supplémentaires (scissions)"""
    B = [list(map(int, b)) for b in boites]
    C = [tuple(b) for b in B] + [tuple(map(int, e)) for e in extra]
    for i, a in enumerate(B):
        chaine, cur = [i], a
        for _ in range(nmax - 1):
            v = [j for j in range(len(B)) if j not in chaine and B[j][0] >= cur[2] - 2 and _meme_bande(cur, B[j])]
            if not v: break
            j = min(v, key=lambda j: B[j][0])
            if any(k not in chaine + [j] and _meme_bande(cur, B[k]) and B[k][0] < B[j][0] and B[k][2] > cur[2] for k in range(len(B))): break
            chaine.append(j); cur = _union(cur, B[j]); C.append(tuple(cur))
    return list(dict.fromkeys(C))


def choisit(gray, textes, boites, tau=4.5, dossier=None):
    """rend {indice texte: boîte choisie} — choix glouton global : paires (ligne lue, candidate)
    triées par score croissant ; une paire est prise si la ligne est libre et la candidate ne
    recouvre aucune candidate déjà prise"""
    import os
    import cv2 as _cv
    _im = _cv.imread(f'{dossier}/page.png', _cv.IMREAD_COLOR) if dossier else None
    ex = list(scissions(gray, boites, im=_im)) if os.environ.get('BBVLM_SR_SCINDE', '1') == '1' else []
    if os.environ.get('BBVLM_SR_SERRE', '0') == '1' and dossier: ex += resserre(dossier, boites)
    if os.environ.get('BBVLM_SR_ETEND', '1') == '1': ex += extensions(gray, boites, _im)
    if os.environ.get('BBVLM_SR_UNION_ETEND', '0') == '1':
        # unions de morceaux, puis prolongées à l'encre (titre coupé en deux ET trop bas : « Am I. Sontag »)
        _o = {tuple(map(int, b)) for b in boites}
        U = [c for c in candidates(boites) if c not in _o]
        if U:
            L = [list(map(int, b)) for b in boites] + [list(u) for u in U]
            ex += extensions(gray, L, _im, cibles=set(range(len(boites), len(L))))
    C = candidates(boites, extra=ex)
    if not textes or not C: return {}
    orig = {tuple(map(int, b)) for b in boites}
    delta = float(os.environ.get('BBVLM_SR_DELTA', '0.5'))
    M = [[score(gray, c, t) for c in C] for t in textes]
    paires = []
    for i in range(len(textes)):
        base = min([M[i][k] for k, c in enumerate(C) if c in orig] or [float('inf')])
        for k, c in enumerate(C):
            s = M[i][k]
            # une candidate nouvelle (union, scission, extension) doit expliquer la ligne nettement
            # mieux que la meilleure ligne d'origine : la perte CTC pénalise à peine la surface en trop
            # et un gain absolu minimal sur la ligne : sur un mot seul, la marge par signe ne suffit pas
            # (réclames « Die », « l. » étendues à l'encre voisine : lignes perdues)
            gain = (base - s) * (len(textes[i]) + 1)
            # une ligne lue d'un seul mot ne départage pas de nouvelles géométries (indices CTC trop faibles)
            multi = len(textes[i].split()) >= int(os.environ.get('BBVLM_SR_MOTS', '2'))
            if s <= tau and (c in orig or (multi and s <= base - delta and gain >= float(os.environ.get('BBVLM_SR_GAIN', '5')))): paires.append((s, i, k))
    paires.sort()
    res, pris = {}, []
    for s, i, k in paires:
        if i in res or any(_recouvre(C[k], C[k2]) for k2 in pris): continue
        res[i] = C[k]; pris.append(k)
    return res
