"""Couper aux gouttières les lignes détectées qui traversent deux colonnes.

BLLA relie parfois deux lignes voisines de colonnes différentes en une seule
(« …l'assassinat du | les rive droite… »). Gemini les a lues dans deux
régions distinctes : aucun texte contigu ne peut correspondre à la ligne
entière. On coupe donc la ligne là où le plan automatique place une
frontière de colonnes ET où les pixels montrent une bande blanche. Aucun
pixel n'est inventé ; la coupe est un intervalle vide d'encre observé. Le
texte, la référence et Gemini n'interviennent pas.
"""
from __future__ import annotations

import numpy as np

VERSION = 'gutter-line-split-v1'


def _clip_polygon(points, x0, x1):
    """Sutherland–Hodgman contre les demi-plans x >= x0 et x <= x1."""
    def clip(poly, inside, cut):
        out = []
        for i, p in enumerate(poly):
            q = poly[i-1]
            if inside(p):
                if not inside(q):
                    out.append(cut(q, p))
                out.append(p)
            elif inside(q):
                out.append(cut(q, p))
        return out

    def at(x):
        def cut(q, p):
            t = (x-q[0])/(p[0]-q[0]) if p[0] != q[0] else 0.
            return [x, q[1]+t*(p[1]-q[1])]
        return cut
    poly = [list(map(float, p)) for p in points]
    poly = clip(poly, lambda p: p[0] >= x0, at(x0)) if poly else poly
    poly = clip(poly, lambda p: p[0] <= x1, at(x1)) if poly else poly
    return poly


def _clip_baseline(points, x0, x1):
    pts = sorted((float(x), float(y)) for x, y in points)
    if len(pts) < 2:
        return []
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    a, b = max(x0, xs[0]), min(x1, xs[-1])
    if a >= b:
        return []
    inner = [[x, y] for x, y in pts if a < x < b]
    return [[a, float(np.interp(a, xs, ys))]] + inner + [[b, float(np.interp(b, xs, ys))]]


def _white_runs(profile):
    runs, start = [], None
    for i, v in enumerate(list(profile)+[1]):
        if v == 0 and start is None:
            start = i
        elif v != 0 and start is not None:
            runs.append((start, i)); start = None
    return runs


ALIGNED_CUTS = 5
ALIGNED_TOLERANCE = 8


def _internal_rules(gray, regions, line_height):
    """Filets verticaux internes : composantes fines (≤ 0,25 hauteur de ligne) et
    hautes (≥ 4 hauteurs de ligne), à plus de 2 hauteurs des bords de la région.
    Renvoie {région: [(x, y0, y1)]}."""
    import cv2
    found = {}
    for region in regions:
        x0, y0, x1, y1 = (int(v) for v in region['bbox'])
        crop = gray[y0:y1, x0:x1]
        if crop.size == 0:
            continue
        _, binary = cv2.threshold(crop, 0, 1, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        n, _, stats, _ = cv2.connectedComponentsWithStats(binary.astype(np.uint8), 8)
        rules = []
        for k in range(1, n):
            w, h = stats[k, cv2.CC_STAT_WIDTH], stats[k, cv2.CC_STAT_HEIGHT]
            cx = stats[k, cv2.CC_STAT_LEFT] + w/2
            if w <= .25*line_height and h >= 4*line_height and 2*line_height < cx < (x1-x0) - 2*line_height:
                rules.append((x0 + float(cx), y0 + float(stats[k, cv2.CC_STAT_TOP]),
                              y0 + float(stats[k, cv2.CC_STAT_TOP] + h)))
        if rules:
            found[region['id']] = rules
    return found


def split_crossing_lines(gray, lines, plan):
    """Renvoie (lignes, journal). Les lignes non coupées sont inchangées."""
    import cv2
    line_height = float(plan['parameters']['line_height'])
    regions = plan['regions']
    out, log, pending = [], [], []
    internal = _internal_rules(gray, regions, line_height)
    for line in lines:
        x0, y0, x1, y1 = line['detector_bbox'] if 'detector_bbox' in line else line['bbox']
        cy = (y0+y1)/2
        inside = [r for r in regions if r['bbox'][1] <= cy < r['bbox'][3]
                  and r['bbox'][0]-.2*line_height <= x0 and x1 <= r['bbox'][2]+.2*line_height]
        hit = sorted((r for r in regions if r['bbox'][1] <= cy < r['bbox'][3]
                      and min(x1, r['bbox'][2])-max(x0, r['bbox'][0]) >= 2*line_height),
                     key=lambda r: r['bbox'][0])
        columns = [float(c) for c in plan['parameters'].get('column_starts', [])
                   if x0+2*line_height < c < x1-2*line_height]
        spanning = bool(inside) and any(
            r['bbox'][0]+2*line_height < c < r['bbox'][2]-2*line_height
            for r in inside for c in plan['parameters'].get('column_starts', []))
        # Filet vertical interne à la région (tableau à deux colonnes côte à
        # côte) qui traverse la ligne : il compte comme une gouttière observée.
        crossing = [rx for r in inside for rx, ry0, ry1 in internal.get(r['id'], [])
                    if x0 + 2*line_height < rx < x1 - 2*line_height and ry0 < cy < ry1]
        internal_rule = bool(crossing and inside and not spanning)
        if internal_rule:
            columns, spanning = sorted(set(columns) | {rx + .4*line_height for rx in crossing}), True
        if (inside and not spanning) or (not inside and len(hit) < 2) or not columns:
            out.append(line); continue
        crop = gray[int(y0):int(y1), int(x0):int(x1)]
        # Otsu, comme l'audit de propriété des pixels. Un filet de colonne
        # (composante fine et haute) compte comme gouttière ; une colonne est
        # blanche si elle ne porte au plus qu'une poussière (≤2 % de hauteur).
        _, binary = cv2.threshold(crop, 0, 1, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        n, labels, stats, _ = cv2.connectedComponentsWithStats(binary.astype(np.uint8), 8)
        rules = [k for k in range(1, n) if stats[k, cv2.CC_STAT_WIDTH] <= .25*line_height
                 and stats[k, cv2.CC_STAT_HEIGHT] >= .4*crop.shape[0]]
        text_ink = binary.copy()
        for k in rules:
            text_ink[labels == k] = 0
        profile = text_ink.sum(axis=0)
        ink = (profile > max(1, .02*crop.shape[0])).astype(int)
        rule_x = [stats[k, cv2.CC_STAT_LEFT]+stats[k, cv2.CC_STAT_WIDTH]/2 for k in rules]
        cuts = []
        for c in columns:
            a, b = int(max(c-1.5*line_height, x0)-x0), int(min(c+.5*line_height, x1)-x0)
            runs = [(s0+a, e0+a) for s0, e0 in _white_runs(ink[a:b])]
            runs = [r for r in runs if r[1]-r[0] >= .3*line_height]
            if spanning:  # dans une région large : seul un filet observé sépare
                runs = [r for r in runs if any(r[0] <= x < r[1] for x in rule_x)]
            if runs:
                # La gouttière précède le début de colonne détecté : retenir la
                # bande blanche la plus proche, pas la plus large (un blanc de
                # mot peut dépasser un blanc de gouttière coupé par un filet).
                target = c-x0-.4*line_height
                s0, e0 = min(runs, key=lambda r: abs((r[0]+r[1])/2-target))
                cuts.append((x0+s0, x0+e0))
        pending.append(dict(line=line, cuts=cuts, spanning=spanning and not internal_rule, ink=ink, box=(x0, y0, x1, y1),
                            rules=len(rules), regions=[r['id'] for r in (inside or hit)], slot=len(out)))
        out.append(None)
    # Deuxième passe. Dans une région large (``spanning``), une lettre fine (l, i, t)
    # passe pour un filet et la ligne de prose est coupée au milieu d'un mot ; un
    # vrai filet de tableau coupe au contraire beaucoup de lignes à la même abscisse.
    # Une coupe de ce type n'est gardée qu'avec ALIGNED_CUTS autres lignes coupées
    # à ± ALIGNED_TOLERANCE px (Matin 0554721 : 0-4 pour les coupes fautives,
    # 5-13 pour les gouttières de tableau).
    centres = [((s+e)/2, k) for k, item in enumerate(pending) for s, e in item['cuts']]
    for k, item in enumerate(pending):
        cuts = item['cuts']
        if item['spanning']:
            cuts = [(s, e) for s, e in cuts
                    if sum(1 for c, j in centres if j != k and abs(c-(s+e)/2) <= ALIGNED_TOLERANCE) >= ALIGNED_CUTS]
        line, ink, (x0, y0, x1, y1) = item['line'], item['ink'], item['box']
        if not cuts:
            out[item['slot']] = line
            log.append(dict(id=line['id'], decision='kept_no_observed_gutter' if not item['cuts']
                            else 'kept_isolated_cut', regions=item['regions']))
            continue
        edges = [x0]+[v for s, e in cuts for v in (s, e)]+[x1]
        parts = []
        for k in range(0, len(edges), 2):
            a, b = edges[k], edges[k+1]
            if b-a < 2*line_height:
                continue
            cols = np.where(ink[int(a-x0):int(b-x0)])[0]
            if not len(cols):
                continue
            a, b = a+int(cols[0]), a+int(cols[-1])+1
            part = {k2: v for k2, v in line.items() if k2 not in ('bbox', 'detector_bbox', 'polygon', 'baseline')}
            bx = line['bbox']
            part.update(id=f"{line['id']}_S{len(parts)+1}",
                        bbox=[max(a, bx[0]), bx[1], min(b, bx[2]), bx[3]],
                        detector_bbox=[a, y0, b, y1],
                        baseline=_clip_baseline(line.get('baseline', []), a, b),
                        polygon=_clip_polygon(line.get('polygon', []), a, b),
                        split_from=line['id'], split_version=VERSION)
            if part['bbox'][0] >= part['bbox'][2]:
                continue
            parts.append(part)
        if len(parts) < 2:
            out[item['slot']] = line
            log.append(dict(id=line['id'], decision='kept_parts_too_narrow'))
            continue
        out[item['slot']] = parts
        log.append(dict(id=line['id'], decision='split_at_observed_gutter',
                        gutters=[[float(s), float(e)] for s, e in cuts],
                        parts=[p['id'] for p in parts], regions=item['regions'],
                        observed_rules=item['rules']))
    return [x for item in out for x in (item if isinstance(item, list) else [item])], log


def assign_regions(lines, plan):
    """Région de chaque ligne (centre dans une seule région), comme le plan."""
    out = {}
    for line in lines:
        x0, y0, x1, y1 = line['bbox']
        x, y = (x0+x1)/2, (y0+y1)/2
        hits = [r['id'] for r in plan['regions']
                if r['bbox'][0] <= x < r['bbox'][2] and r['bbox'][1] <= y < r['bbox'][3]]
        if len(hits) == 1:
            out[line['id']] = hits[0]
    return out
