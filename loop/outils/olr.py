"""OLR des livres depuis la lecture étiquetée (consigne P4), et sa mesure.

Lecture : lignes « [rôle] texte » ou « [rôle+] texte » (+ = début d'une
nouvelle région du même rôle). Régions prédites = suites de lignes de même
rôle, coupées à chaque « + » ; ordre des régions = ordre de lecture.
Référence : PAGE XML OCR-D (TextRegion@type, ReadingOrder).
Mesures par page : exactitude du rôle par ligne ; F1 des paires de lignes
« même région » ; exactitude des paires de régions ordonnées (ordre des
premières lignes, pour les régions appariées).
"""
import json, re, sys
from lxml import etree
from accord import apparie
from cer import vue

ROLE = re.compile(r'^\[([a-z\-]+)(\+?)\]\s?(.*)$')
EQUIV = {'heading': 'heading', 'header': 'header', 'page-number': 'page-number', 'paragraph': 'paragraph',
         'marginalia': 'marginalia', 'footnote': 'footnote', 'footnote-continued': 'footnote',
         'signature-mark': 'signature-mark', 'catch-word': 'catch-word', 'caption': 'caption'}


def lit(lignes):
    out, reg = [], -1
    prec = None
    for l in lignes:
        if l.lower().startswith('#ecriture') or not l.strip(): continue
        m = ROLE.match(l.strip())
        role, plus, texte = (m.group(1), m.group(2) == '+', m.group(3)) if m else ('paragraph', False, l)
        if plus or role != prec: reg += 1
        out.append((role, reg, texte)); prec = role
    return out


def reference(page_xml):
    r = etree.parse(page_xml).getroot(); N = {'p': r.tag.split('}')[0][1:]}
    ordre = {x.get('regionRef'): int(x.get('index')) for x in r.iter(f'{{{N["p"]}}}RegionRefIndexed')}
    lignes = []
    for tr in r.findall('.//p:TextRegion', N):
        for tl in tr.findall('p:TextLine', N):
            u = tl.find('p:TextEquiv/p:Unicode', N)
            if u is None or not (u.text or '').strip(): continue
            lignes.append((EQUIV.get(tr.get('type'), 'other'), tr.get('id'), ordre.get(tr.get('id'), 999), u.text))
    return lignes


def mesure(page_xml, lecture):
    ref = reference(page_xml); lu = lit(open(lecture, encoding='utf-8').read().splitlines())
    m = apparie([vue(x[3], 'diplo') for x in ref], [vue(x[2], 'diplo') for x in lu])
    txt2i = {}
    for j, x in enumerate(lu): txt2i.setdefault(vue(x[2], 'diplo'), j)
    pairs = {i: txt2i[t] for i, t in m.items() if t in txt2i}
    ok_role = sum(1 for i, j in pairs.items() if lu[j][0] == ref[i][0])
    tp = fp = fn = 0
    idx = sorted(pairs)
    for a in range(len(idx)):
        for b in range(a+1, len(idx)):
            i, k = idx[a], idx[b]
            s_ref = ref[i][1] == ref[k][1]; s_lu = lu[pairs[i]][1] == lu[pairs[k]][1]
            tp += s_ref and s_lu; fp += s_lu and not s_ref; fn += s_ref and not s_lu
    f1 = 2*tp/max(1, 2*tp+fp+fn)
    # ordre des régions de référence : position de leur première ligne dans la lecture
    premiere = {}
    for i, j in pairs.items():
        rid = ref[i][1]; premiere[rid] = min(premiere.get(rid, 10**9), j)
    regs = sorted(premiere, key=lambda r: [x[2] for x in ref if x[1] == r][0])
    bon = tot = 0
    for a in range(len(regs)):
        for b in range(a+1, len(regs)):
            tot += 1; bon += premiere[regs[a]] < premiere[regs[b]]
    return {'lignes_ref': len(ref), 'lignes_appariees': len(pairs), 'role_exact': round(ok_role/max(1, len(pairs)), 3),
            'f1_meme_region': round(f1, 3), 'ordre_regions': round(bon/max(1, tot), 3), 'regions_ref': len(set(x[1] for x in ref)),
            'regions_lues': len(set(x[1] for x in lu))}


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        p, l = arg.split('=')
        print(l.split('/')[-2][:10], l.split('/')[-1], mesure(p, l))
