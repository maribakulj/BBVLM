#!/usr/bin/env python
"""Essai « structure d'abord » sur une page déjà traitée : structure Gemini avec
boîtes (1 appel), plan ancré sur les lignes kraken, mesures contre la VT
(évaluation seulement) et aperçu. N'écrit que dans le dossier de sortie."""
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'scripts'))
from page_olr_gemini import ask_structure
import page_layout_gemini as plg

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('run', help='dossier ocr_presse existant (segmentation/, layout/plan.json)')
parser.add_argument('output'); parser.add_argument('--image', required=True)
parser.add_argument('--evaluation-manifest'); parser.add_argument('--page-id')
args = parser.parse_args()
run, out = Path(args.run), Path(args.output); out.mkdir(parents=True, exist_ok=True)
image = Path(args.image); local = out / image.name
if not local.exists():
    shutil.copy2(image, local)
lines = json.loads((run / 'segmentation/segmentation.json').read_text())
auto = json.loads((run / 'layout/plan.json').read_text())
cached = out / 'olr-gemini.json'
structure = json.loads(cached.read_text()) if cached.exists() else ask_structure(out, local, prompt=plg.PROMPT)
if not structure.get('complete'):
    raise SystemExit('structure incomplète : voir olr-gemini.json')
plan = plg.write_plan(image, auto, lines, structure, out / 'layout')
report = dict(plan['audit'])
if args.evaluation_manifest and args.page_id:
    from mesurer_olr import reference_regions
    from mesurer_boites import iou_matrix
    from scipy.optimize import linear_sum_assignment
    from PIL import Image
    page = [p for p in json.loads(Path(args.evaluation_manifest).read_text())['pages'] if p['id'] == args.page_id][0]
    ref = reference_regions(page['reference'])
    with Image.open(image) as im:
        W, H = im.size
    raw = [b for b in (plg._box(b, W, H) for b in structure['blocs']) if b]
    anchored = [r['bbox'] for r in plan['regions']]
    for name, boxes in (('boites_gemini_brutes', raw), ('regions_ancrees', anchored)):
        m = iou_matrix([r['bbox'] for r in ref], boxes)
        r_, c_ = linear_sum_assignment(-m)
        ious = sorted(float(m[i, j]) for i, j in zip(r_, c_))
        def inter(a, b):
            return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
        inside = sum(any(inter(r['bbox'], b) >= .8 * max(1, (r['bbox'][2] - r['bbox'][0]) * (r['bbox'][3] - r['bbox'][1]))
                         for b in boxes) for r in ref)
        report[name] = dict(n=len(boxes), regions_vt=len(ref), iou50=sum(v >= .5 for v in ious) / len(ref),
                            iou_median=ious[len(ious) // 2] if ious else None, vt_dans_un_seul=inside / len(ref))
    # Erreur des bords des boîtes brutes : boîte Gemini vs union des lignes kraken qui lui sont rattachées
    owner = plg.anchor_lines([b for b in structure['blocs'] if isinstance(b.get('n'), int)], lines, W, H,
                             float(auto['parameters']['line_height']))
    errs = []
    for b in structure['blocs']:
        box = plg._box(b, W, H); rows = [l for l in lines if owner.get(l['id']) == b.get('n')]
        if box and rows:
            u = [min(l['bbox'][0] for l in rows), min(l['bbox'][1] for l in rows), max(l['bbox'][2] for l in rows), max(l['bbox'][3] for l in rows)]
            errs += [abs(box[k] - u[k]) for k in range(4)]
    errs.sort()
    report['ecart_bords_px'] = dict(mediane=errs[len(errs) // 2], p90=errs[int(.9 * len(errs))]) if errs else None
from PIL import Image, ImageDraw
with Image.open(image) as im:
    prev = im.convert('RGB'); d = ImageDraw.Draw(prev)
    for b in structure['blocs']:
        box = plg._box(b, *im.size)
        if box:
            d.rectangle(box, outline=(220, 40, 40), width=4)
    for r in plan['regions']:
        d.rectangle(r['bbox'], outline=(30, 90, 220), width=8)
        d.text((r['bbox'][0] + 10, r['bbox'][1] + 10), r['id'], fill=(30, 90, 220))
    prev.thumbnail((2400, 2400)); prev.save(out / 'apercu.jpg', quality=85)
(out / 'essai-rapport.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
print(json.dumps({k: v for k, v in report.items() if k not in ('lines_attached_to_nearest_region',)}, ensure_ascii=False, indent=1))
