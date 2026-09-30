"""Chaîne complète → ALTO 4.4 : lignes kraken resserrées, texte lu, boîtes connexe.

Aucune donnée de référence en entrée. Pour chaque ligne lue : ligne kraken
alignée (`aligne.py`), mots placés par `connexe` (master). Une ligne lue sans
ligne kraken, ou dont le placement échoue, est écrite sans boîtes de mots mais
marquée `TAGREFS="NON_PLACE"` et comptée dans la provenance : on ne comble pas.
Coordonnées ALTO : HPOS/VPOS/WIDTH/HEIGHT en pixels, bornes inclusives.
usage : python vers_alto.py DOSSIER TEXTE SORTIE.xml
"""
import json, sys, os
from lxml import etree
import cv2
M = '/home/user/BBVLM/src'; sys.path[:0] = [M, M+'/boxers']
import connexe, corpora
from aligne import aligne

NS = 'http://www.loc.gov/standards/alto/ns-v4#'


def E(parent, tag, **at):
    return etree.SubElement(parent, f'{{{NS}}}{tag}', **{k: str(v) for k, v in at.items()})


def lignes_page(dossier, lignes, roles=None, ecr='fraktur'):
    """Lignes de la page telles que la chaîne les utilise : kraken G03 (+ G04b),
    scindées (S08), manchettes coupées (S02) ; rend (kr, boites des mots (G05), géométrie publiée)."""
    import shutil
    kr = json.load(open(f"{dossier}/{os.environ.get('BBVLM_LIGNES', 'kraken_serre.json')}"))['lignes']
    if os.environ.get('BBVLM_SCINDE', '1') == '1' and os.environ.get('BBVLM_ANCRE', '1') == '1' and shutil.which('tesseract'):
        # S08 : ligne kraken portant deux lignes lues (notes en colonnes, manchette collée) → scindée
        from ancre import lit_lignes
        from scinde import scinde
        g0 = cv2.imread(f'{dossier}/page.png', cv2.IMREAD_GRAYSCALE)
        bb = [l['bbox'] for l in kr]
        nb = scinde(g0, bb, lit_lignes(dossier, bb, ecr), lignes)
        if os.environ.get('BBVLM_RENVOIS', '1') == '1':      # S08c (adopté) : renvois chiffrés alignés à droite
            from scinde import renvois
            nb = renvois(g0, nb, lit_lignes(dossier, nb, ecr), lignes, dossier,
                         'script/Fraktur' if ecr == 'fraktur' else 'lat')
        if os.environ.get('BBVLM_FUSION', '1') == '1':      # S11 (adopté) : deux lignes kraken pour une ligne lue
            from scinde import fusionne
            nb = fusionne(nb, lit_lignes(dossier, nb, ecr), lignes)
        if nb != bb:
            garde = {tuple(l['bbox']): l for l in kr}
            kr = [garde.get(tuple(b), {'bbox': b}) for b in nb]
        if os.environ.get('BBVLM_ETEND', '1') == '1':    # S09 (adopté) : lignes courtes complétées par l'encre
            from etend import etend
            eb = etend(g0, [l['bbox'] for l in kr])
            if os.environ.get('BBVLM_ETEND_LOIN') == '1' and shutil.which('tesseract'):
                # S09c : second passage jusqu'à 4 h (listes « ix.      Bonen », geomeikud) ; gardé seulement
                # si la relecture (deux modèles) de la boîte élargie ressemble strictement mieux à une ligne lue
                from ancre import lit_lignes
                from cer import lev
                e2 = etend(g0, eb, ecart=float(os.environ.get('BBVLM_ETEND_LOIN_E', '4')), hmin=0.2)   # minuscules « ix. »
                ch = [i for i in range(len(eb)) if list(map(int, e2[i])) != list(map(int, eb[i]))]
                if ch:
                    R = [''.join(t.replace('ſ', 's').lower().split()) for t in lignes]
                    def _d(t):
                        t = ''.join(t.replace('ſ', 's').lower().split())
                        return min((lev(t, r) / max(1, len(t), len(r)) for r in R if r), default=1)
                    bx = [eb[i] for i in ch] + [e2[i] for i in ch]
                    O = [lit_lignes(dossier, bx, e) for e in ('fraktur', 'romain')]
                    for n, i in enumerate(ch):
                        if min(_d(o[len(ch) + n]) for o in O) < min(_d(o[n]) for o in O): eb[i] = [int(v) for v in e2[i]]
            def _g04(l, e):     # la boîte G04b ne reçoit que l'extension horizontale (sinon G05 se désactive, hackherz)
                g = l.get('bbox_g04', l['bbox'])
                return [min(g[0], e[0]), g[1], max(g[2], e[2]), g[3]]
            kr = [l if list(map(int, l['bbox'])) == e else {**l, 'bbox': e, 'bbox_g04': _g04(l, e)} for l, e in zip(kr, eb)]
    if not (roles and any(r[0] == 'marginalia' for r in roles)) and os.environ.get('BBVLM_S02C', '1') == '1' and shutil.which('tesseract'):
        # S02c (adopté) : sans rôles, coupe S02 gardée seulement si le plus petit morceau, relu, retrouve une ligne lue (L20)
        from coupe import coupe_page
        from ancre import lit_lignes, reduit
        from cer import lev
        g0 = cv2.imread(f'{dossier}/page.png', cv2.IMREAD_GRAYSCALE)
        bb = [list(map(int, l['bbox'])) for l in kr]
        cp = [list(map(int, p)) for p in coupe_page(g0, bb)]
        R = [reduit(t) for t in lignes]
        def _dm(p):     # meilleure distance de la relecture de p (deux modèles) à une ligne lue
            o = [reduit(t) for e in ('fraktur', 'romain') for t in lit_lignes(dossier, [p], e)]
            return min((lev(t, r) / max(len(t), len(r)) for t in o for r in R if t and r), default=1)
        def _ok(petit, grand, tout):
            # le petit morceau retrouve une ligne lue, et le grand ne s'éloigne pas du texte
            # (sinon c'est un mot du texte courant qu'on détache : « ſehr » ≈ « wer », geomeikud)
            return _dm(petit) <= float(os.environ.get('BBVLM_S02C_D', '0.5')) and _dm(grand) <= _dm(tout)
        nkr = []
        for l, b in zip(kr, bb):
            mx = [p for p in cp if p[0] >= b[0] - 1 and p[2] <= b[2] + 1 and p[1] >= b[1] - 1 and p[3] <= b[3] + 1]
            if len(mx) > 1 and _ok(min(mx, key=lambda p: p[2] - p[0]), max(mx, key=lambda p: p[2] - p[0]), b):
                nkr += [{'bbox': p} for p in mx]
            else:
                nkr.append(l)
        kr = nkr
    if roles and any(r[0] == 'marginalia' for r in roles):
        # manchettes signalées par le lecteur : détacher celles que kraken a fusionnées (coupe.py)
        from coupe import coupe_page
        g0 = cv2.imread(f'{dossier}/page.png', cv2.IMREAD_GRAYSCALE)
        garde = {tuple(l['bbox']): l for l in kr}
        kr = [garde.get(tuple(b), {'bbox': b}) for b in coupe_page(g0, [l['bbox'] for l in kr])]
    if os.environ.get('BBVLM_EYN') == '1' and os.path.exists(f'{dossier}/eynollah.xml'):
        # EY1 : lignes eynollah qui ne recouvrent aucune ligne kraken = candidates en plus
        from lxml import etree as _et
        r = _et.parse(f'{dossier}/eynollah.xml').getroot(); N = {'p': r.tag.split('}')[0][1:]}
        def _rec(e, k):
            ix = max(0, min(e[2], k[2]) - max(e[0], k[0])); iy = max(0, min(e[3], k[3]) - max(e[1], k[1]))
            return ix * iy / max(1, (e[2] - e[0]) * (e[3] - e[1]))
        for tl in r.iter(f"{{{N['p']}}}TextLine"):
            pts = [tuple(map(int, q.split(','))) for q in tl.find('p:Coords', N).get('points').split()]
            e = [min(a for a, _ in pts), min(b for _, b in pts), max(a for a, _ in pts), max(b for _, b in pts)]
            if all(_rec(e, l['bbox']) < .5 and _rec(l['bbox'], e) < .5 for l in kr):
                kr.append({'bbox': e})
    if os.environ.get('BBVLM_S06') == '1':
        # S06b : bandes d'encre hors lignes kraken (projection, L11) ajoutées comme candidates ;
        # l'ancrage ne leur donne du texte que si une ligne lue y correspond
        from bandes import bandes
        g0 = cv2.imread(f'{dossier}/page.png', cv2.IMREAD_GRAYSCALE)
        kr = kr + [{'bbox': b} for b in bandes(g0, [l['bbox'] for l in kr])]
    if os.environ.get('BBVLM_S17', '0') == '1' and lignes:      # REJETÉE (s15/RESULTATS.md)
        # S17 : boîte kraken sans ligne lue (ancrage S05) dans la bande d'une boîte ancrée,
        # sans boîte entre elles → réunie à celle-ci (« ij.      Treer » : numéro de liste
        # détaché que ni Tesseract ni CATMuS ne lisent ; S15/S16)
        from ancre import lit_lignes, aligne_ancre
        bx = [l['bbox'] for l in kr]
        pris = set(aligne_ancre(lignes, bx, lit_lignes(dossier, bx, ecr)).values())
        def _vr(a, b): return min(a[3], b[3]) - max(a[1], b[1]) >= .5 * min(a[3] - a[1], b[3] - b[1])
        _g17 = cv2.imread(f'{dossier}/page.png', cv2.IMREAD_GRAYSCALE)
        def _p10(b):
            c = _g17[max(0, int(b[1])):int(b[3]), max(0, int(b[0])):int(b[2])]
            if c.size == 0: return 255.
            t = cv2.threshold(c, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[0]
            m = c[c < t]
            return float(__import__('numpy').percentile(m, 10)) if m.size else 255.
        mort = set()
        for k in range(len(kr)):
            if k in pris: continue
            a = kr[k]['bbox']
            cand = [j for j in pris if j not in mort and _vr(a, kr[j]['bbox'])
                    and max(kr[j]['bbox'][0] - a[2], a[0] - kr[j]['bbox'][2]) <= float(os.environ.get('BBVLM_S17_ECART', '4')) * (a[3] - a[1])]
            if not cand: continue
            j = min(cand, key=lambda j: max(kr[j]['bbox'][0] - a[2], a[0] - kr[j]['bbox'][2]))
            b = kr[j]['bbox']; lo, hi = min(a[2], b[2]), max(a[0], b[0])
            # S17b : encre de même nature (annotation manuscrite plus claire : p10 ≈ 107 contre 35-39, buchdas/27)
            if _p10(a) > _p10(b) + float(os.environ.get('BBVLM_S17_ENCRE', '30')): continue
            if any(i not in (j, k) and _vr(a, kr[i]['bbox']) and kr[i]['bbox'][0] < hi and kr[i]['bbox'][2] > lo for i in range(len(kr))): continue
            u = lambda p, q: [min(p[0], q[0]), min(p[1], q[1]), max(p[2], q[2]), max(p[3], q[3])]
            kr[j] = {**kr[j], 'bbox': u(a, b), **({'bbox_g04': u(a, kr[j]['bbox_g04'])} if 'bbox_g04' in kr[j] else {})}
            mort.add(k)
        kr = [l for i, l in enumerate(kr) if i not in mort]
    if os.environ.get('BBVLM_SR', '1') == '1' and lignes:      # adoptée le 30/09 (s15/RESULTATS.md)
        # SR (L36) : segmentation par reconnaissance guidée par le texte lu — chaque ligne lue
        # reçoit la candidate (ligne, ou union de morceaux voisins d'une même bande) qui
        # l'explique le mieux (perte CTC W05), affectation globale sans chevauchement ;
        # les lignes kraken non recouvertes par une boîte choisie sont gardées telles quelles
        from sr import choisit, _recouvre
        _gs = cv2.imread(f'{dossier}/page.png', cv2.IMREAD_GRAYSCALE)
        ch = list(choisit(_gs, lignes, [l['bbox'] for l in kr], float(os.environ.get('BBVLM_SR_TAU', '4.5')), dossier).values())
        garde = {tuple(map(int, l['bbox'])): l for l in kr}
        nkr = [garde.get(tuple(b), {'bbox': list(b)}) for b in ch]
        _neuves = [b for b in ch if tuple(b) not in garde]
        _dans = lambda a, b: a[0] >= b[0] - 1 and a[1] >= b[1] - 1 and a[2] <= b[2] + 1 and a[3] <= b[3] + 1
        _pris = {tuple(b) for b in ch}
        nkr += [l for l in kr if tuple(map(int, l['bbox'])) not in _pris and not any(_dans(l['bbox'], b) for b in _neuves)
                and not any(_dans(b, l['bbox']) for b in _neuves)]      # scission choisie : la ligne d'origine cède la place
        kr = nkr
    if os.environ.get('BBVLM_S18', '1') == '1':
        # S18 (L43) : taches détachées en haut/bas de la boîte de ligne retirées
        from sr import detache
        _g18 = cv2.imread(f'{dossier}/page.png', cv2.IMREAD_GRAYSCALE)
        kr = [{**l, 'bbox': detache(_g18, l['bbox']), **({'bbox_g04': detache(_g18, l['bbox_g04'])} if 'bbox_g04' in l else {})} for l in kr]
    if os.environ.get('BBVLM_S14', '1') == '1':      # S14 : lettrine rattachée à sa ligne (appliquée si le mot lu commence par deux capitales)
        from lettrine import detecte
        g0 = cv2.imread(f'{dossier}/page.png', cv2.IMREAD_GRAYSCALE)
        for i, c in detecte(g0, [l['bbox'] for l in kr]).items(): kr[i] = {**kr[i], 'lettrine': c}
    boites = [l['bbox'] for l in kr]
    mg = os.environ.get('BBVLM_MOTS_G04', 'page')
    if mg == 'page':
        # G05 : page contaminée par l'encre des lignes voisines (la boîte G04b abaisse
        # le haut des lignes de ≥ SEUIL·h en médiane) → mots calculés sur la boîte G04b
        import numpy as _np
        r = [(l['bbox_g04'][1] - l['bbox'][1]) / max(1, l['bbox'][3] - l['bbox'][1]) for l in kr if 'bbox_g04' in l]
        mg = '1' if r and float(_np.median(r)) >= float(os.environ.get('BBVLM_G05_SEUIL', '0.05')) else '0'
    if mg == '1':          # mots calculés sur la boîte de ligne G04b
        boites = [l.get('bbox_g04', l['bbox']) for l in kr]
    elif mg == 'ligne':    # G06 : même choix que G05, mais ligne par ligne
        sl = float(os.environ.get('BBVLM_G05_SEUIL', '0.05'))
        boites = [l['bbox_g04'] if 'bbox_g04' in l and (l['bbox_g04'][1] - l['bbox'][1]) / max(1, l['bbox'][3] - l['bbox'][1]) >= sl
                  else l['bbox'] for l in kr]
    # géométrie publiée des TextLine : boîte G04b si disponible (lignes scindées/coupées : boîte G03)
    geo = [l.get('bbox_g04', l['bbox']) if os.environ.get('BBVLM_LIGNE_G04', '1') == '1' else l['bbox'] for l in kr]
    return kr, boites, geo


def construit(dossier, texte, sortie, lecteur='Claude Opus (2 passes + arbitrage P3)', structure=None):
    """structure : lecture étiquetée (consigne P4) dont on tire rôle et région de
    chaque ligne (`olr.lit`), dans le même ordre que `texte`. Sans elle : un seul bloc."""
    lignes = [l for l in open(texte, encoding='utf-8').read().splitlines() if l.strip() and not l.startswith('#')]
    roles = None
    if structure:
        from olr import lit
        roles = lit(open(structure, encoding='utf-8').read().splitlines())
        if len(roles) != len(lignes): roles = None
    import shutil
    ecr = 'fraktur'
    if structure:
        for l in open(structure, encoding='utf-8'):
            if l.lower().startswith('#ecriture:'): ecr = l.split(':', 1)[1].strip().lower()
    kr, boites, geo = lignes_page(dossier, lignes, roles, ecr)
    # W03b : pré-calcul Calamari binarisé des boîtes de ligne (environnement séparé, BBVLM_CALA_PY)
    cpy = os.environ.get('BBVLM_CALA_PY')
    if cpy and ecr != 'fraktur' and not os.path.exists(f'{dossier}/calamari_bin.json'):
        import subprocess
        json.dump({'lignes': [{'bbox': [int(v) for v in b]} for b in boites]}, open(f'{dossier}/lignes_alto.json', 'w'))
        subprocess.run([cpy, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cala_page.py'), dossier],
                       env={**os.environ, 'BBVLM_CALA_BIN': '1', 'BBVLM_CALA_LIGNES': 'lignes_alto.json'},
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    g = cv2.imread(f'{dossier}/page.png', cv2.IMREAD_GRAYSCALE); H, W = g.shape
    # Placement : avec les rôles, manchettes alignées sur les lignes de marge
    # (mesuré sur 8 pages : égal partout, herrleyc 0,47 → 0,66 en rappel IoU80).
    if os.environ.get('BBVLM_ANCRE', '1') == '1' and shutil.which('tesseract'):   # S05 adopté (banc 20 pages)
        # S05 : ancrage par OCR Tesseract des lignes kraken (L10)
        from ancre import lit_lignes, aligne_ancre
        loc = aligne_ancre(lignes, boites, lit_lignes(dossier, boites, ecr))
    elif roles:
        from aligne import aligne_roles
        loc = aligne_roles(lignes, [r[0] for r in roles], boites)
    else:
        loc = aligne(lignes, boites)
    import os as _os
    if _os.environ.get('BBVLM_BOXER', 'base') == 'base':     # B04 adopté : redressement par ligne de base, pages penchées seulement
        from centre import LigneBase
        bx = LigneBase({tuple(int(v) for v in b): l.get('baseline') for l, b in zip(kr, boites)})
    elif _os.environ.get('BBVLM_BOXER', 'base') == 'route':   # G02/A37 par défaut (mesuré sur 8 pages)
        from g02 import Route
        bx = Route()
    else:
        bx = connexe.Connexe()
    if os.environ.get('BBVLM_SAT') == '1':               # M01 : signes suscrits rattachés
        from satellites import ConnexeSat
        bx.c = ConnexeSat()
    root = etree.Element(f'{{{NS}}}alto', nsmap={None: NS, 'xsi': 'http://www.w3.org/2001/XMLSchema-instance'})
    root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation', NS+' http://www.loc.gov/standards/alto/v4/alto-4-4.xsd')
    d = E(root, 'Description'); E(d, 'MeasurementUnit').text = 'pixel'
    si = E(d, 'sourceImageInformation'); E(si, 'fileName').text = os.path.basename(dossier.rstrip('/'))+'.tif'
    p = E(d, 'OCRProcessing', ID='OCRP1'); st = E(p, 'ocrProcessingStep')
    E(st, 'processingStepDescription').text = ('texte : lecture VLM diplomatique OCR-D niveau 2 ; lignes : kraken blla resserré sur '
                                              "l'encre du polygone ; mots : connexe (BBVLM). Brouillon de vérité terrain : relecture humaine requise.")
    sw = E(st, 'processingSoftware'); E(sw, 'softwareName').text = f'BBVLM loop — {lecteur} + kraken 7.1.1 + connexe'
    tags = E(root, 'Tags'); E(tags, 'OtherTag', ID='NON_PLACE', LABEL='ligne lue non placée', TYPE='provenance')
    for r in sorted({x[0] for x in roles}) if roles else []:
        E(tags, 'LayoutTag', ID=f'ROLE_{r}', LABEL=r, TYPE='OCR-D region type')
    ordre = E(root, 'ReadingOrder') if roles else None
    grp = E(ordre, 'OrderedGroup', ID='RO1') if roles else None
    lay = E(root, 'Layout'); page = E(lay, 'Page', ID='P1', PHYSICAL_IMG_NR=1, WIDTH=W, HEIGHT=H)
    ps = E(page, 'PrintSpace', ID='PS1', HPOS=0, VPOS=0, WIDTH=W, HEIGHT=H)
    blocs = {}
    def bloc(i):
        if not roles:
            if 'B1' not in blocs: blocs['B1'] = E(ps, 'TextBlock', ID='B1')
            return blocs['B1']
        role, reg, _ = roles[i]
        if reg not in blocs:
            blocs[reg] = E(ps, 'TextBlock', ID=f'B{reg+1:03d}', TAGREFS=f'ROLE_{role}')
            E(grp, 'ElementRef', ID=f'RO_B{reg+1:03d}', REF=f'B{reg+1:03d}')
        return blocs[reg]
    n_place = n_non = 0
    _mtf = f'{dossier}/mots_tesseract.json'
    try: _mt = json.load(open(_mtf))
    except (FileNotFoundError, ValueError): _mt = {}
    corrigees = []
    for i, t in enumerate(lignes):
        mots = t.split()
        if i in loc:
            x0, y0, x1, y1 = boites[loc[i]]
            gx0, gy0, gx1, gy1 = geo[loc[i]]
            lt = kr[loc[i]].get('lettrine') if len(t) > 1 and t[:2].isupper() else None     # S14 : la lettre après la lettrine est en capitale (« ES », « DA », « AUf »)
            if lt: gx0, gy0, gx1, gy1 = min(gx0, lt[0]), min(gy0, lt[1]), max(gx1, lt[2]), max(gy1, lt[3])
            tl = E(bloc(i), 'TextLine', ID=f'L{i+1:04d}', HPOS=gx0, VPOS=gy0, WIDTH=gx1-gx0+1, HEIGHT=gy1-gy0+1)
            try:
                bs = bx.boxes(g, corpora.Line(t, mots, (x0, y0, x1, y1), []))
                ok = len(bs) == len(mots)
                if ok and lt:
                    bs = [tuple(v) for v in bs]; a, b_, c, e = bs[0]
                    bs[0] = (min(a, lt[0]), min(b_, lt[1]), max(c, lt[2]), max(e, lt[3]))
                if ok and os.environ.get('BBVLM_W01') == '1':
                    # W01 : bords gauche/droit des mots pris chez Tesseract quand le mot concorde
                    from mots_tess import mots_ligne, aligne
                    k = f"{'script/Fraktur' if ecr == 'fraktur' else 'lat'}|{x0},{y0},{x1},{y1}"
                    eux = mots_ligne(g, (x0, y0, x1, y1), k.split('|')[0], _mt, k)
                    for a, b in aligne(mots, eux).items():
                        p, q, r_, s_ = bs[a]
                        bs[a] = (eux[b][1], q, eux[b][2], s_)
                w02d = os.environ.get('BBVLM_W02D') == '1'     # W02d (rejetée) : romain avec script/Latin
                w03 = os.environ.get('BBVLM_W03', 'romain_b')   # W03b adoptée (romain : Calamari binarisé, espaces appariées par rang) ; '0' pour couper
                w05 = False                                       # W05 adoptée : alignement forcé CTC (kraken CATMuS), repli W03b/W02 si kraken absent
                if ok and len(bs) == len(mots) and os.environ.get('BBVLM_W05', 'tout') != '0':
                    try:
                        from w05 import ajuste as ajuste5
                        bs = ajuste5(g, (x0, y0, x1, y1), mots, bs); w05 = True
                    except Exception:
                        w05 = False
                w03b = w03.endswith('_b')                        # W03b : entrée binarisée, appariement par rang
                if w05: pass
                elif ok and (w03 in ('tout', 'tout_b') or (w03 in ('romain', 'romain_b') and ecr != 'fraktur')):
                    from w03 import ajuste as ajuste3, ajuste_b
                    if w03b: ajuste3 = ajuste_b
                    if '_cal' not in locals():
                        try: _cal = json.load(open(f'{dossier}/calamari_bin.json' if w03b else f'{dossier}/calamari.json'))
                        except (FileNotFoundError, ValueError): _cal = {}
                    bs = ajuste3(g, (x0, y0, x1, y1), bs, _cal.get(f'{x0},{y0},{x1},{y1}'))
                elif ok and os.environ.get('BBVLM_W02', '1') == '1' and (ecr == 'fraktur' or w02d or os.environ.get('BBVLM_W02C', '1') == '0'):      # W02 : coupure choisie par Tesseract, bords à l'encre ; W02c : Fraktur seulement
                    from w02 import ajuste
                    lg = 'script/Fraktur' if ecr == 'fraktur' else ('script/Latin' if w02d else 'lat')
                    bs = ajuste(g, (x0, y0, x1, y1), mots, bs, lg, _mt, f"{lg}|{x0},{y0},{x1},{y1}")
                if ok and os.environ.get('BBVLM_BLANCS') == '1':     # S10 : blancs vérifiés par l'encre
                    from blancs import corrige
                    mots, bs = corrige(g, mots, bs)
            except Exception:
                ok = False
        else:
            tl = E(bloc(i), 'TextLine', ID=f'L{i+1:04d}', TAGREFS='NON_PLACE'); ok = False
        corrigees.append(' '.join(mots))
        if ok:
            n_place += 1
            for k, (m, (a, b, c, e)) in enumerate(zip(mots, bs)):
                E(tl, 'String', ID=f'L{i+1:04d}_W{k+1:02d}', CONTENT=m, HPOS=a, VPOS=b, WIDTH=c-a+1, HEIGHT=e-b+1)
                if k < len(mots)-1:
                    E(tl, 'SP', HPOS=c+1, VPOS=b, WIDTH=max(1, bs[k+1][0]-c-1))
        else:
            n_non += 1
            tl.set('TAGREFS', 'NON_PLACE')
            for k, m in enumerate(mots):
                E(tl, 'String', ID=f'L{i+1:04d}_W{k+1:02d}', CONTENT=m)
                if k < len(mots)-1: E(tl, 'SP')
    for b in blocs.values():            # géométrie du bloc = enveloppe de ses lignes placées
        bs_ = [(int(t.get('HPOS')), int(t.get('VPOS')), int(t.get('HPOS'))+int(t.get('WIDTH')), int(t.get('VPOS'))+int(t.get('HEIGHT'))) for t in b if t.get('HPOS')]
        if bs_:
            b.set('HPOS', str(min(x[0] for x in bs_))); b.set('VPOS', str(min(x[1] for x in bs_)))
            b.set('WIDTH', str(max(x[2] for x in bs_)-min(x[0] for x in bs_))); b.set('HEIGHT', str(max(x[3] for x in bs_)-min(x[1] for x in bs_)))
    if _mt: json.dump(_mt, open(_mtf, 'w'), ensure_ascii=False)
    if os.environ.get('BBVLM_BLANCS') == '1':
        open(f'{dossier}/lecture_blancs.txt', 'w', encoding='utf-8').write('\n'.join(corrigees) + '\n')
    xml = etree.tostring(root, encoding='UTF-8', xml_declaration=True, pretty_print=True)
    open(sortie, 'wb').write(xml)
    return {'lignes': len(lignes), 'placees': n_place, 'non_placees': n_non}


def valide(chemin, xsd):
    s = etree.XMLSchema(etree.parse(xsd))
    ok = s.validate(etree.parse(chemin))
    return ok, [str(e) for e in s.error_log][:5]


if __name__ == '__main__':
    r = construit(*sys.argv[1:4], structure=sys.argv[4] if len(sys.argv) > 4 else None)
    ok, err = valide(sys.argv[3], os.path.join(os.path.dirname(__file__), '..', 'schemas', 'alto-4-4-local.xsd'))
    print(r, 'XSD', 'valide' if ok else err)
