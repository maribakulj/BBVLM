"""Découper les régions hautes en morceaux lus séparément par Gemini.

Une colonne entière (4 000 px, 5 000 caractères) donne des réponses longues
que le flux d'agy coupe ; on la découpe en morceaux d'au plus ``max_height``
pixels, aux blancs ENTRE deux lignes détectées (aucune ligne n'est coupée).
Les lignes sont réattribuées au morceau qui contient leur centre. Image et
lignes seules ; aucune référence.
"""
from __future__ import annotations


def split_tall_regions(plan, lines, max_height=1500):
    by_id = {l['id']: l for l in lines}
    regions, line_regions = [], {}
    order = 0
    for region in sorted(plan['regions'], key=lambda r: r['order']):
        x0, y0, x1, y1 = region['bbox']
        members = [by_id[k] for k, v in plan['line_regions'].items() if v == region['id'] and k in by_id]
        cuts = [y0]
        if y1 - y0 > max_height and members:
            spans = sorted((l['bbox'][1], l['bbox'][3]) for l in members)
            # coupe entre deux lignes successives dont les boîtes se recouvrent
            # de moins d'un tiers de hauteur ; aucune autre ligne ne la traverse
            gaps, reach = [], spans[0][1]
            for (pa, pb), (a, b) in zip(spans, spans[1:]):
                height = min(pb - pa, b - a)
                if a >= reach - height/3:
                    cut = (max(reach, a) + min(reach, a)) // 2
                    if not any(sa + (sb - sa)/3 < cut < sb - (sb - sa)/3 for sa, sb in spans):
                        gaps.append(int(cut))
                reach = max(reach, b)
            # glouton : depuis la dernière coupe, le blanc le plus proche de
            # ``max_height`` plus bas, tant que le reste dépasse 1,2 × max_height
            while y1 - cuts[-1] > 1.2*max_height:
                usable = [g for g in gaps if cuts[-1] + max_height//3 < g < y1 - max_height//3]
                if not usable:
                    break
                cuts.append(min(usable, key=lambda g: abs(g - (cuts[-1] + max_height))))
        cuts.append(y1)
        cuts = sorted(set(cuts))
        for k, (a, b) in enumerate(zip(cuts, cuts[1:]), 1):
            order += 1
            rid = region['id'] if len(cuts) == 2 else f"{region['id']}_m{k}"
            regions.append({**region, 'id': rid, 'bbox': [x0, int(a), x1, int(b)], 'order': order,
                            **({'split_from': region['id']} if len(cuts) > 2 else {})})
            for l in members:
                cy = (l['bbox'][1] + l['bbox'][3]) / 2
                if a <= cy < b or (b == y1 and cy == b):
                    line_regions[l['id']] = rid
        for l in members:
            line_regions.setdefault(l['id'], regions[-1]['id'])
    out = {**plan, 'regions': regions, 'line_regions': {**plan['line_regions'], **line_regions}}
    out.setdefault('parameters', {})['max_region_height'] = max_height
    return out


def drop_contained_regions(plan, lines, threshold=.9):
    """Supprime une région contenue (≥ ``threshold`` de son aire) dans une autre
    plus grande : sinon son contenu est lu deux fois par Gemini et ses lignes,
    attribuables aux deux, ne sont rattachées à aucune. Les lignes sans région
    sont réattribuées à la région restante qui contient leur centre."""
    def area(b):
        return max(0, b[2]-b[0])*max(0, b[3]-b[1])
    regions = plan['regions']
    dropped = set()
    for a in regions:
        for b in regions:
            if a is b or b['id'] in dropped or area(a['bbox']) > area(b['bbox']):
                continue
            ix = max(0, min(a['bbox'][2], b['bbox'][2]) - max(a['bbox'][0], b['bbox'][0]))
            iy = max(0, min(a['bbox'][3], b['bbox'][3]) - max(a['bbox'][1], b['bbox'][1]))
            if area(a['bbox']) and ix*iy >= threshold*area(a['bbox']) and (area(a['bbox']) < area(b['bbox']) or a['id'] > b['id']):
                dropped.add(a['id'])
    if not dropped:
        return plan
    kept = [r for r in regions if r['id'] not in dropped]
    by_id = {l['id']: l for l in lines}
    line_regions = {}
    for lid, rid in plan['line_regions'].items():
        if rid is not None and rid not in dropped:
            line_regions[lid] = rid; continue
        line = by_id.get(lid)
        if line is None:
            continue
        cx, cy = (line['bbox'][0]+line['bbox'][2])/2, (line['bbox'][1]+line['bbox'][3])/2
        inside = [r for r in kept if r['bbox'][0] <= cx < r['bbox'][2] and r['bbox'][1] <= cy < r['bbox'][3]]
        if len(inside) == 1:
            line_regions[lid] = inside[0]['id']
    for line in lines:
        if line['id'] not in line_regions:
            cx, cy = (line['bbox'][0]+line['bbox'][2])/2, (line['bbox'][1]+line['bbox'][3])/2
            inside = [r for r in kept if r['bbox'][0] <= cx < r['bbox'][2] and r['bbox'][1] <= cy < r['bbox'][3]]
            if len(inside) == 1:
                line_regions[line['id']] = inside[0]['id']
    audit = dict(plan.get('audit', {}))
    audit['dropped_contained_regions'] = sorted(dropped)
    audit['ambiguous'] = [l for l in audit.get('ambiguous', []) if l not in line_regions]
    return {**plan, 'regions': [dict(r, order=k) for k, r in enumerate(sorted(kept, key=lambda r: r['order']), 1)],
            'line_regions': line_regions, 'audit': audit}
