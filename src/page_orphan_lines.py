"""Lignes oubliées par le détecteur : encre qu'aucune ligne détectée ne couvre.

Le détecteur de lignes manque parfois des colonnes entières de chiffres dans
les tableaux (cotes de la Bourse) ou des fins de paragraphe courtes. On
binarise la page, on efface l'encre déjà couverte par une ligne détectée, et
on regroupe l'encre restante en lignes : composantes de taille de caractère,
réunies par rangées (recouvrement vertical) et par proximité horizontale.
Image seule : aucune référence, aucun texte. Les lignes produites portent
``source='orphan-ink'`` ; leur texte viendra de l'appariement CTC par bloc.
"""
from __future__ import annotations

import numpy as np

VERSION = 'orphan-ink-lines-v1'


def _otsu(gray):
    hist = np.bincount(gray.ravel(), minlength=256).astype(float)
    total = hist.sum()
    cum, cum_mean = np.cumsum(hist), np.cumsum(hist*np.arange(256))
    between = (cum_mean[-1]*cum - cum_mean*total)**2 / np.maximum(cum*(total-cum), 1)
    return int(np.argmax(between))


def find_orphan_lines(gray, lines, line_height, regions=None, min_chars=2):
    """gray : page en niveaux de gris (uint8) ; lines : lignes détectées (bbox) ;
    line_height : hauteur typique d'une ligne de texte (px). Renvoie de nouvelles
    lignes {id, bbox, baseline, polygon, source} triées en ordre de lecture."""
    from scipy import ndimage
    ink = gray < _otsu(gray)
    covered = np.zeros_like(ink)
    pad = max(2, int(.15*line_height))
    for line in lines:
        x0, y0, x1, y1 = (int(round(v)) for v in line['bbox'])
        covered[max(0, y0-pad):y1+pad, max(0, x0-pad):x1+pad] = True
    rest = ink & ~covered
    labels, _ = ndimage.label(rest)
    boxes = ndimage.find_objects(labels)
    comps, small = [], []
    for k, sl in enumerate(boxes, 1):
        if sl is None:
            continue
        h, w = sl[0].stop-sl[0].start, sl[1].stop-sl[1].start
        area = int((labels[sl] == k).sum())
        # taille de caractère : ni poussière, ni filet, ni bloc d'illustration
        if h < .3*line_height and w < .5*line_height and area >= 4:
            small.append([sl[1].start, sl[0].start, sl[1].stop, sl[0].stop])  # points, virgules
            continue
        if h < .3*line_height or h > 1.6*line_height or w > 4*line_height or area < .02*line_height**2:
            continue
        if w > 8*h or h > 6*w:  # filets horizontaux / verticaux
            continue
        comps.append([sl[1].start, sl[0].start, sl[1].stop, sl[0].stop])
    comps.sort(key=lambda b: ((b[1]+b[3])/2, b[0]))
    # rangées : recouvrement vertical d'au moins la moitié de la hauteur
    rows = []
    for box in comps:
        for row in rows:
            r = row['box']
            overlap = min(r[3], box[3]) - max(r[1], box[1])
            if overlap >= .5*min(r[3]-r[1], box[3]-box[1]):
                row['items'].append(box)
                row['box'] = [min(r[0], box[0]), min(r[1], box[1]), max(r[2], box[2]), max(r[3], box[3])]
                break
        else:
            rows.append(dict(box=list(box), items=[box]))
    found = []
    for row in rows:
        items = sorted(row['items'])
        group = [items[0]]
        for box in items[1:] + [None]:
            if box is not None and box[0] - max(b[2] for b in group) <= 1.2*line_height:
                group.append(box); continue
            if len(group) >= min_chars:
                x0 = min(b[0] for b in group); x1 = max(b[2] for b in group)
                y0 = min(b[1] for b in group); y1 = max(b[3] for b in group)
                if regions is None or any(r[0] <= (x0+x1)/2 < r[2] and r[1] <= (y0+y1)/2 < r[3] for r in regions):
                    found.append([x0, y0, x1, y1])
            group = [box] if box is not None else []
    # points de conduite, virgules, petites fractions : rattachés à la ligne
    # trouvée dont ils prolongent la rangée (même bande verticale, écart court)
    changed = True
    while changed:
        changed = False
        for box in found:
            for dot in small:
                cy = (dot[1]+dot[3])/2
                if box[1]-.2*line_height <= cy <= box[3]+.2*line_height and \
                        -1.2*line_height <= dot[0]-box[2] <= 1.2*line_height and dot[2] > box[2]:
                    box[2] = dot[2]; changed = True
                elif box[1]-.2*line_height <= cy <= box[3]+.2*line_height and \
                        -1.2*line_height <= box[0]-dot[2] <= 1.2*line_height and dot[0] < box[0]:
                    box[0] = dot[0]; changed = True
    found.sort(key=lambda b: (b[1], b[0]))
    out = []
    for k, (x0, y0, x1, y1) in enumerate(found, 1):
        base = y1 - .2*(y1-y0)
        out.append(dict(id=f'O{k:04d}', bbox=[x0, y0, x1, y1], detector_bbox=[x0, y0, x1, y1],
                        baseline=[[float(x0), float(base)], [float(x1), float(base)]],
                        polygon=[[x0, y0], [x1, y0], [x1, y1], [x0, y1]], source='orphan-ink'))
    return out
