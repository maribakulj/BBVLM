"""Plan de lecture à partir de la structure logique de Gemini, ancrée sur les lignes.

1. Gemini voit la page entière UNE fois et rend sa structure : blocs dans
   l'ordre de lecture, type, article, colonne, premiers/derniers mots et une
   boîte approximative (millièmes de la largeur et de la hauteur). Il ne
   transcrit pas la page : lue en entier, une page de journal est réduite par le
   client à ~3 000 px et le petit corps devient illisible.
2. Les boîtes de Gemini ne sont pas exactes. Chaque ligne détectée par kraken est
   rattachée au bloc qui la contient (marge d'une hauteur de ligne), et la boîte
   de chaque bloc devient l'union de ses lignes : coordonnées ancrées dans la
   page, au pixel des lignes.
3. Les blocs voisins d'une même colonne sont regroupés en régions de lecture
   (une lecture Gemini par région, à pleine résolution) ; une région ne
   chevauche jamais une autre.
Le plan a le format de page_layout_auto (regions, line_regions, parameters) ;
paramètres de colonnes et hauteur de ligne repris du plan automatique.
"""
from __future__ import annotations
import json
from pathlib import Path

from page_anchors import save_json, sha256
from page_olr_gemini import TYPES

VERSION = 'gemini-structure-layout-v1'
PROMPT = (
    'Cette image est une page de journal français ancien. Décris sa STRUCTURE LOGIQUE, sans '
    'transcrire le texte complet. Liste TOUS les blocs de texte de la page, dans l’ordre de lecture '
    '(colonne par colonne, de haut en bas, en suivant les articles qui passent d’une colonne à la '
    'suivante). Pour chaque bloc : "n" (numéro dans l’ordre de lecture), "type" parmi '
    + ', '.join(f'"{t}"' for t in TYPES) +
    ', "article" (numéro de l’article auquel il appartient ; même numéro pour son titre et tous ses '
    'paragraphes, y compris sur plusieurs colonnes), "colonne" (1 = la plus à gauche), "debut" (les 6 '
    'premiers mots exactement comme imprimés), "fin" (les 6 derniers mots exactement comme imprimés) et '
    '"boite" : [gauche, haut, droite, bas] du bloc en millièmes de la largeur et de la hauteur de la page '
    '(0 = bord gauche ou haut, 1000 = bord droit ou bas), au plus près de l’encre du bloc. '
    'Un paragraphe = un bloc ; un tableau = un bloc ; une colonne d’un tableau sur plusieurs colonnes de la '
    'page = un bloc par colonne. N’oublie aucun bloc, même court (fins de paragraphe, annonces, bandeau). '
    'Ouvre d’abord l’image jointe ; si tu ne peux pas la voir, réponds uniquement IMAGE_ABSENTE. '
    'Réponds uniquement par un objet JSON {"blocs": [...]}.'
)


def _box(bloc, width, height):
    try:
        x0, y0, x1, y1 = (float(v) for v in bloc['boite'])
    except (KeyError, TypeError, ValueError):
        return None
    if not (0 <= x0 < x1 <= 1000 and 0 <= y0 < y1 <= 1000):
        return None
    return [x0 * width / 1000, y0 * height / 1000, x1 * width / 1000, y1 * height / 1000]


def anchor_lines(blocs, lines, width, height, line_height):
    """{id de ligne: n du bloc} : bloc dont la boîte (élargie d'une hauteur de
    ligne) contient le centre de la ligne ; à défaut, bloc le plus proche à
    moins de trois hauteurs. Plusieurs candidats : plus grand recouvrement."""
    boxes = {b['n']: _box(b, width, height) for b in blocs}
    boxes = {n: b for n, b in boxes.items() if b}
    margin = line_height
    out = {}
    for line in lines:
        x0, y0, x1, y1 = line['bbox']
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        inside = [n for n, b in boxes.items()
                  if b[0] - margin <= cx <= b[2] + margin and b[1] - margin / 2 <= cy <= b[3] + margin / 2]
        if not inside:
            def dist(b):
                return max(b[0] - cx, 0, cx - b[2]) + max(b[1] - cy, 0, cy - b[3])
            near = sorted(boxes, key=lambda n: dist(boxes[n]))
            if near and dist(boxes[near[0]]) <= 3 * line_height:
                inside = near[:1]
        if not inside:
            continue

        def overlap(n):
            b = boxes[n]
            return max(0, min(x1, b[2]) - max(x0, b[0])) * max(0, min(y1, b[3]) - max(y0, b[1]))
        out[line['id']] = max(inside, key=lambda n: (overlap(n), -n))
    return out


def reading_regions(blocs, lines, owner, line_height, width, height, max_height=1500):
    """Blocs ancrés → régions de lecture dans l'ordre de lecture.

    Boîte d'un bloc = union de ses lignes, bornée à sa boîte Gemini élargie
    d'une hauteur de ligne (une ligne kraken trop large ne l'étire pas). Seuls
    des blocs consécutifs de la même colonne, l'un sous l'autre, sont réunis.
    Deux régions qui se recouvrent sont coupées au milieu du recouvrement
    (jamais fusionnées en cascade) : aucune ligne n'est lue deux fois."""
    by_block = {}
    for line in lines:
        if line['id'] in owner:
            by_block.setdefault(owner[line['id']], []).append(line)
    order = [b for b in sorted(blocs, key=lambda b: b['n']) if b['n'] in by_block]
    m = line_height

    def block_box(bloc):
        rows = by_block[bloc['n']]
        u = [min(r['bbox'][0] for r in rows), min(r['bbox'][1] for r in rows),
             max(r['bbox'][2] for r in rows), max(r['bbox'][3] for r in rows)]
        g = _box(bloc, width, height)
        return [max(u[0], g[0] - m), max(u[1], g[1] - m), min(u[2], g[2] + m), min(u[3], g[3] + m)]
    groups = []
    for bloc in order:
        box = block_box(bloc)
        if box[2] <= box[0] or box[3] <= box[1]:
            continue
        if groups:
            last = groups[-1]
            lb = last['bbox']
            shared = max(0, min(box[2], lb[2]) - max(box[0], lb[0])) / max(1, min(box[2] - box[0], lb[2] - lb[0]))
            gap = box[1] - lb[3]
            if (bloc.get('colonne') == last['colonne'] and shared >= .6 and -m <= gap <= 1.5 * m
                    and max(box[3], lb[3]) - min(box[1], lb[1]) <= max_height):
                last['bbox'] = [min(box[0], lb[0]), min(box[1], lb[1]), max(box[2], lb[2]), max(box[3], lb[3])]
                last['blocs'].append(bloc['n']); continue
        groups.append(dict(bbox=box, blocs=[bloc['n']], colonne=bloc.get('colonne')))
    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            a, b = groups[i]['bbox'], groups[j]['bbox']
            ox, oy = min(a[2], b[2]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[1], b[1])
            if ox <= 0 or oy <= 0:
                continue
            if oy <= ox:   # l'une au-dessus de l'autre : coupe horizontale
                top_, low = (a, b) if a[1] + a[3] <= b[1] + b[3] else (b, a)
                cut = (max(top_[1], low[1]) + min(top_[3], low[3])) / 2
                top_[3], low[1] = cut, cut
            else:          # côte à côte : coupe verticale
                left, right = (a, b) if a[0] + a[2] <= b[0] + b[2] else (b, a)
                cut = (max(left[0], right[0]) + min(left[2], right[2])) / 2
                left[2], right[0] = cut, cut
    regions = []
    for k, g in enumerate(groups, 1):
        x0, y0, x1, y1 = g['bbox']
        if x1 - x0 < 8 or y1 - y0 < 8:
            continue
        regions.append(dict(id=f'g{k:03d}', kind='gemini_structure_region', order=len(regions) + 1,
                            bbox=[max(0, int(x0)), max(0, int(y0)), min(width, int(x1 + 1)), min(height, int(y1 + 1))],
                            blocs=g['blocs']))
    return regions


def snap_edges(regions, ink, line_height, lines, vrules=None):
    """Cale chaque bord de région sur un blanc de l'image, à deux hauteurs de
    ligne au plus. Bord vertical : la colonne de pixels qui traverse de l'encre
    dans le MOINS de lignes de texte (kraken) de la région, compté ligne par
    ligne (une moyenne sur toute la hauteur prend une colonne de points de
    conduite clairsemés pour un blanc) ; un filet vertical fin compte comme
    blanc. Bord horizontal : la rangée la moins encrée. Une découpe ne traverse
    ainsi pas un mot ; une ligne coupée à une gouttière est ensuite séparée en
    cellules (page_line_split). ``ink`` : image binaire (1 = encre)."""
    import numpy as np
    h, w = ink.shape
    reach = int(2 * line_height)
    thin = max(2, int(.25 * line_height))
    for r in regions:
        x0, y0, x1, y1 = r['bbox']
        rows = [l['bbox'] for l in lines if l['bbox'][1] < y1 and l['bbox'][3] > y0
                and min(l['bbox'][3], y1) - max(l['bbox'][1], y0) > .5 * (l['bbox'][3] - l['bbox'][1])]
        for side in ('left', 'right'):
            x = x0 if side == 'left' else x1
            # Filet vertical (traits fins et pâles des tableaux) à moins de trois
            # hauteurs de ligne : c'est LA séparation, prise en priorité.
            if vrules is not None:
                a3, b3 = max(0, x - int(3 * line_height)), min(w, x + int(3 * line_height) + 1)
                cover = vrules[y0:y1, a3:b3].mean(axis=0) if y1 > y0 else np.zeros(0)
                found = np.flatnonzero(cover > .3)
                if len(found):
                    best = a3 + int(found[np.argmin(np.abs(found + a3 - x))])
                    if side == 'left' and best < x1 - line_height:
                        x0 = best
                        continue
                    if side == 'right' and best > x0 + line_height:
                        x1 = best + 1
                        continue
            a, b = max(0, x - reach), min(w, x + reach + 1)
            hits = np.zeros(b - a)
            for lx0, ly0, lx1, ly1 in rows:
                if lx1 <= a or lx0 >= b:
                    continue
                band = ink[int(ly0):int(ly1), a:b]
                col = band.any(axis=0).astype(float)
                # filet vertical fin et plein : compte comme blanc
                full = band.mean(axis=0) > .85
                for i in np.flatnonzero(full):
                    lo, hi = max(0, i - thin), min(len(col), i + thin + 1)
                    if (band[:, lo:hi].mean(axis=0) < .15).sum() >= 2:
                        col[i] = 0.
                inside = np.zeros(b - a, bool)
                inside[max(0, int(lx0) - a):max(0, min(b, int(lx1)) - a)] = True
                hits += col * inside
            best = a + int(np.argmin(hits + 1e-4 * np.abs(np.arange(a, b) - x)))
            if side == 'left' and best < x1 - line_height:
                x0 = best
            elif side == 'right' and best > x0 + line_height:
                x1 = best + 1
        for side in ('top', 'bottom'):
            y = y0 if side == 'top' else y1
            a, b = max(0, y - reach), min(h, y + reach + 1)
            band = ink[a:b, x0:x1]
            if band.size == 0:
                continue
            frac = band.mean(axis=1)
            best = a + int(np.argmin(frac + 1e-4 * np.abs(np.arange(a, b) - y)))
            if side == 'top' and best < y1 - line_height:
                y0 = best
            elif side == 'bottom' and best > y0 + line_height:
                y1 = best + 1
        r['bbox'] = [int(x0), int(y0), int(x1), int(y1)]
    return regions


def write_plan(image, auto_plan, lines, structure, output):
    """Plan au format page_layout_auto, régions issues de la structure Gemini."""
    from PIL import Image
    with Image.open(image) as page:
        width, height = page.size
    line_height = float(auto_plan['parameters']['line_height'])
    blocs = [b for b in structure['blocs'] if isinstance(b.get('n'), int)]
    owner = anchor_lines(blocs, lines, width, height, line_height)
    regions = reading_regions(blocs, lines, owner, line_height, width, height)
    import cv2
    import numpy as np
    gray = cv2.imread(str(image), cv2.IMREAD_GRAYSCALE)
    _, ink = cv2.threshold(gray, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    loose = (gray < 190).astype('uint8')
    vrules = cv2.morphologyEx(loose, cv2.MORPH_OPEN, np.ones((int(3 * line_height), 1), np.uint8))
    vrules = cv2.dilate(vrules, np.ones((1, 3), np.uint8))
    regions = snap_edges(regions, ink, line_height, lines, vrules)
    # Chaque ligne va à la région qui contient son centre ; à défaut (ligne hors
    # de tout bloc Gemini, ou rognée), à la région la plus proche, et comptée.
    line_regions, orphans = {}, []
    for line in lines:
        cx, cy = (line['bbox'][0] + line['bbox'][2]) / 2, (line['bbox'][1] + line['bbox'][3]) / 2
        hit = [r for r in regions if r['bbox'][0] <= cx < r['bbox'][2] and r['bbox'][1] <= cy < r['bbox'][3]]
        if hit:
            line_regions[line['id']] = hit[0]['id']
        else:
            orphans.append(line)
    for line in orphans:
        cx, cy = (line['bbox'][0] + line['bbox'][2]) / 2, (line['bbox'][1] + line['bbox'][3]) / 2
        best = min(regions, key=lambda r: max(r['bbox'][0] - cx, 0, cx - r['bbox'][2]) + max(r['bbox'][1] - cy, 0, cy - r['bbox'][3]))
        line_regions[line['id']] = best['id']
    blocks_without_lines = [b['n'] for b in blocs if b['n'] not in set(owner.values())]
    plan = dict(version=VERSION, image=str(image), image_sha256=sha256(image), regions=regions,
                coordinate_system='source_pixels_xyxy', reference_used=False,
                parameters=dict(auto_plan['parameters']), line_regions=line_regions,
                audit=dict(detected_lines=len(lines), lines_in_gemini_blocks=len(owner),
                           lines_attached_to_nearest_region=[l['id'] for l in orphans],
                           gemini_blocks=len(blocs), blocks_without_boxes=[b['n'] for b in blocs if not _box(b, width, height)],
                           blocks_without_lines=blocks_without_lines, regions=len(regions),
                           auto_plan_version=auto_plan.get('version'), requires_review=bool(orphans or blocks_without_lines)))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    save_json(output / 'plan.json', plan)
    return plan
