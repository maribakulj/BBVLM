#!/usr/bin/env python
"""Plan de régions tiré de l'OLR Haiku (ordre, articles) et des boîtes PP-DocLayout (coordonnées).

Chaque article est découpé en segments : boîtes consécutives de l'article, l'une sous
l'autre dans la même colonne. Un segment = une région lue en une fois, dans l'ordre
de lecture de Haiku. Les lignes kraken vont à la région qui contient leur centre ;
les lignes sans région (texte que le détecteur n'a pas encadré) forment des régions
de secours, groupées par colonne, insérées après la région située au-dessus d'elles.
Le plan a le format de layout/plan.json : ocr_presse.py le reprend tel quel.
Usage : plan_depuis_olr.py image segmentation.json dossier_olr sortie/layout
"""
import argparse
import hashlib
import json
from pathlib import Path


def union(boxes):
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]


def x_overlap(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) / max(1, min(a[2]-a[0], b[2]-b[0]))


def segments(article_boxes, gap):
    """Boîtes successives d'un article regroupées tant qu'elles se suivent dans la même colonne."""
    out = []
    for box in article_boxes:
        last = out[-1][-1] if out else None
        if last and x_overlap(last, box) > .6 and -gap < box[1] - last[3] < gap:
            out[-1].append(box)
        else:
            out.append([box])
    return [union(s) for s in out]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image'); parser.add_argument('segmentation'); parser.add_argument('olr'); parser.add_argument('output')
    args = parser.parse_args()
    olr_dir = Path(args.olr)
    olr = json.loads((olr_dir / 'olr-haiku.json').read_text())
    boxes = json.loads((olr_dir / 'boites.json').read_text())
    lines = json.loads(Path(args.segmentation).read_text())
    height = sorted(l['bbox'][3] - l['bbox'][1] for l in lines)[len(lines)//2]
    regions, used = [], set()
    for a, article in enumerate(olr.get('articles', []), 1):
        numbers = [int(n) for n in article.get('boites', []) if 1 <= int(n) <= len(boxes) and int(n) not in used]
        used.update(numbers)
        for s, bbox in enumerate(segments([boxes[n-1]['bbox'] for n in numbers], 3*height), 1):
            regions.append(dict(id=f'a{a:02d}_s{s:02d}', kind='olr_segment', article=a,
                                article_type=article.get('type'), bbox=[round(v) for v in bbox]))
    # Boîtes de texte que Haiku n'a rangées nulle part : régions à part, en fin de liste.
    for n, box in enumerate(boxes, 1):
        if n not in used and n not in {int(i) for i in olr.get('ignorees', []) if str(i).isdigit()} \
                and box['label'] not in ('image',):
            regions.append(dict(id=f'z{n:03d}', kind='unordered_box', bbox=[round(v) for v in box['bbox']]))

    def center(l):
        return (l['bbox'][0]+l['bbox'][2])/2, (l['bbox'][1]+l['bbox'][3])/2

    def area(b):
        return (b[2]-b[0])*(b[3]-b[1])
    line_regions, orphans = {}, []
    for l in lines:
        x, y = center(l)
        inside = [r for r in regions if r['bbox'][0] <= x <= r['bbox'][2] and r['bbox'][1] <= y <= r['bbox'][3]]
        if inside:
            line_regions[l['id']] = min(inside, key=lambda r: area(r['bbox']))['id']
        else:
            orphans.append(l)
    # Lignes orphelines : groupées par colonne et par proximité verticale.
    groups = []
    for l in sorted(orphans, key=lambda l: (l['bbox'][0], l['bbox'][1])):
        for g in groups:
            if x_overlap(g['bbox'], l['bbox']) > .5 and l['bbox'][1] - g['bbox'][3] < 2*height and g['bbox'][1] - l['bbox'][3] < 2*height:
                g['lines'].append(l); g['bbox'] = union([g['bbox'], l['bbox']]); break
        else:
            groups.append(dict(lines=[l], bbox=list(l['bbox'])))
    for k, g in enumerate(groups, 1):
        rid = f'o{k:03d}'
        # après la région de la même colonne qui finit juste au-dessus
        above = [i for i, r in enumerate(regions) if x_overlap(r['bbox'], g['bbox']) > .5 and r['bbox'][3] <= g['bbox'][1] + height]
        at = max(above, key=lambda i: regions[i]['bbox'][3]) + 1 if above else len(regions)
        regions.insert(at, dict(id=rid, kind='orphan_lines', bbox=[round(v) for v in g['bbox']]))
        for l in g['lines']:
            line_regions[l['id']] = rid
    kept = {v for v in line_regions.values()}
    regions = [r for r in regions if r['id'] in kept]
    # Boîtes du détecteur qui se chevauchent : chaque région est resserrée sur SES lignes
    # (marge d'un tiers de ligne), sinon le crop montre les lignes de la voisine, lues deux fois.
    by_id = {l['id']: l for l in lines}
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    with Image.open(args.image) as im:
        width, height_px = im.size
    for r in regions:
        own = [by_id[k]['bbox'] for k, v in line_regions.items() if v == r['id']]
        m = round(height / 3)
        if r['kind'] != 'orphan_lines':
            # ligne kraken à cheval sur deux colonnes : coupée à la largeur de la boîte du détecteur
            bx0, bx1 = r['bbox'][0] - m, r['bbox'][2] + m
            own = [[max(o[0], bx0), o[1], min(o[2], bx1), o[3]] for o in own if min(o[2], bx1) > max(o[0], bx0)]
        b = union(own)
        r['bbox'] = [round(max(0, b[0]-m)), round(max(0, b[1]-m)), round(min(width, b[2]+m)), round(min(height_px, b[3]+m))]
        r['keep_boxes'] = [[round(v) for v in o] for o in own]
    for r in regions:
        x0, y0, x1, y1 = r['bbox']
        r['hide_boxes'] = [[round(v) for v in by_id[k]['bbox']] for k, v in line_regions.items() if v != r['id']
                           and by_id[k]['bbox'][0] < x1 and by_id[k]['bbox'][2] > x0
                           and by_id[k]['bbox'][1] < y1 and by_id[k]['bbox'][3] > y0]
    for k, r in enumerate(regions, 1):
        r['order'] = k
    plan = dict(version='olr-haiku-ppdoclayout-v1', image=str(Path(args.image).resolve()),
                image_sha256=hashlib.sha256(Path(args.image).read_bytes()).hexdigest(),
                regions=regions, coordinate_system='source_pixels_xyxy', reference_used=False,
                parameters=dict(line_height=height, source='olr_haiku+pp_doclayout_v3'),
                audit=dict(detected_lines=len(lines), assigned_lines=len(line_regions),
                           orphan_lines=len(orphans), orphan_regions=len(groups),
                           olr_articles=len(olr.get('articles', [])), olr_missing=olr.get('manques', []),
                           # régions imbriquées gardées : le masquage des crops règle le double emploi
                           dropped_contained_regions=[]),
                line_regions=line_regions)
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    (out / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=1))
    try:
        from PIL import Image, ImageDraw
        Image.MAX_IMAGE_PIXELS = None
        im = Image.open(args.image).convert('RGB'); s = 1600 / max(im.size)
        im = im.resize((round(im.width*s), round(im.height*s))); d = ImageDraw.Draw(im)
        for r in regions:
            b = [v*s for v in r['bbox']]
            d.rectangle(b, outline=(220, 40, 40) if r['kind'] == 'orphan_lines' else (0, 90, 220), width=2)
            d.text((b[0]+3, b[1]+2), str(r['order']), fill=(200, 0, 0))
        im.save(out / 'plan-preview.jpg', quality=85)
    except Exception as e:  # aperçu seulement
        print('aperçu non produit :', e)
    print(json.dumps(plan['audit'], ensure_ascii=False), 'régions', len(regions))


if __name__ == '__main__':
    main()
