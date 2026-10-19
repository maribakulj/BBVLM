#!/usr/bin/env python
"""Mesure de l'OLR (blocs + ordre de lecture) d'un ALTO contre les TextRegion de la VT.

- Découpage : appariement un-à-un des TextBlock de l'ALTO aux TextRegion de la VT
  par IoU (affectation optimale) ; part des régions VT retrouvées à IoU ≥ 0,5.
- Ordre : sur les paires appariées, tau de Kendall entre l'ordre de lecture de la
  VT (readingOrder index) et celui de l'ALTO (ReadingOrder), et part des régions
  VT consécutives dont l'ordre relatif est le même chez nous.
La VT ne porte ni types ni articles : ils ne sont pas mesurés ici.
"""
import argparse
import json
from pathlib import Path
import re
import sys

import numpy as np
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'scripts'))
from mesurer_boites import iou_matrix

NS = '{http://www.loc.gov/standards/alto/ns-v4#}'


def reference_regions(path):
    out = []
    for region in etree.parse(str(path)).getroot().iter('{*}TextRegion'):
        coords = region.find('{*}Coords')
        if coords is None:
            continue
        pts = [tuple(map(float, p.split(','))) for p in coords.get('points').split()]
        index = re.search(r'readingOrder \{index:(\d+);', region.get('custom', ''))
        out.append(dict(id=region.get('id'), bbox=[min(p[0] for p in pts), min(p[1] for p in pts),
                                                     max(p[0] for p in pts), max(p[1] for p in pts)],
                        order=int(index.group(1)) if index else None))
    return out


def alto_blocks(path):
    root = etree.parse(str(path)).getroot()
    order = {ref.get('REF'): k for k, ref in enumerate(root.iter(f'{NS}ElementRef'))}
    out = []
    for block in root.iter(f'{NS}TextBlock'):
        x, y, w, h = (float(block.get(k)) for k in ('HPOS', 'VPOS', 'WIDTH', 'HEIGHT'))
        out.append(dict(id=block.get('ID'), bbox=[x, y, x+w, y+h], order=order.get(block.get('ID'))))
    return out


def kendall(a, b):
    n, concordant, discordant = len(a), 0, 0
    for i in range(n):
        for j in range(i+1, n):
            s = (a[i]-a[j])*(b[i]-b[j])
            concordant += s > 0; discordant += s < 0
    return (concordant-discordant)/max(1, concordant+discordant)


def evaluate(manifest, alto, page_id):
    page = [p for p in json.loads(Path(manifest).read_text())['pages'] if p['id'] == page_id][0]
    ref, ours = reference_regions(page['reference']), alto_blocks(alto)
    from scipy.optimize import linear_sum_assignment
    m = iou_matrix([r['bbox'] for r in ref], [o['bbox'] for o in ours])
    rows, cols = linear_sum_assignment(-m)
    pairs = [(i, j, m[i, j]) for i, j in zip(rows, cols) if m[i, j] >= .5]
    ordered = [(ref[i]['order'], ours[j]['order']) for i, j, _ in pairs
               if ref[i]['order'] is not None and ours[j]['order'] is not None]
    ordered.sort()
    ref_rank, our_rank = [a for a, _ in ordered], [b for _, b in ordered]
    consecutive = sum(1 for k in range(len(our_rank)-1) if our_rank[k] < our_rank[k+1])
    # Découpage plus fin dans la VT : une région VT est « bien placée » si au moins
    # 80 % de son aire tombe dans UN seul de nos blocs (elle n'est pas coupée).
    def inter(a, b):
        return max(0, min(a[2], b[2])-max(a[0], b[0]))*max(0, min(a[3], b[3])-max(a[1], b[1]))
    contained = 0
    for r in ref:
        area = max(1, (r['bbox'][2]-r['bbox'][0])*(r['bbox'][3]-r['bbox'][1]))
        if any(inter(r['bbox'], o['bbox']) >= .8*area for o in ours if o['id'] != 'OLR_NON_ATTRIBUE'):
            contained += 1
    return dict(page=page_id, regions_vt=len(ref), blocs_alto=len(ours),
                regions_vt_dans_un_seul_bloc=contained/len(ref) if ref else None,
                regions_vt_retrouvees_iou50=len(pairs)/len(ref) if ref else None,
                iou_median_apparies=float(np.median([p[2] for p in pairs])) if pairs else None,
                ordre_kendall_tau=kendall(ref_rank, our_rank) if len(ordered) > 1 else None,
                ordre_paires_consecutives_justes=consecutive/max(1, len(our_rank)-1))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest'); parser.add_argument('alto'); parser.add_argument('page_id')
    args = parser.parse_args()
    print(json.dumps(evaluate(args.manifest, args.alto, args.page_id), ensure_ascii=False, indent=1))
