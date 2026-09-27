"""Inspect fixed-assignment A35 regressions without tuning the refiner."""
import json
from PIL import Image, ImageDraw
import evaluate_native_refinement_a35 as run


def main():
    cases = json.loads((run.OUT / 'fixed-assignment-cases.json').read_text())
    selected = sorted(cases, key=lambda x: x['delta'])[:8]
    paths = {}
    for name in run.DATASETS:
        source = run.BASE / name
        split = json.loads((source / 'split.json').read_text())
        paths.update({(name, p['page']): source / 'source' / p['image'] for p in split['pages']})
    canvas = Image.new('RGB', (1200, 8*170), 'white')
    draw = ImageDraw.Draw(canvas)
    for row, case in enumerate(selected):
        image = Image.open(paths[case['dataset'], case['page']]).convert('RGB')
        coords = [case[k] for k in ('native', 'refined', 'reference')]
        context = [max(0, min(c[0] for c in coords)-25), max(0, min(c[1] for c in coords)-15),
                   min(image.width, max(c[2] for c in coords)+25), min(image.height, max(c[3] for c in coords)+15)]
        draw.text((5, row*170+2), f"{case['dataset']} {case['line']} #{case['prediction_index']} IoU {case['old_iou']:.3f}->{case['new_iou']:.3f}", fill='black')
        for column, (label, box) in enumerate([('unmarked context', context), ('native crop', case['native']), ('A32 crop', case['refined'])]):
            draw.text((column*400+5, row*170+18), label, fill='black')
            crop = image.crop(box)
            if crop.width <= 0 or crop.height <= 0:
                continue
            scale = min(3, 390/crop.width, 125/crop.height)
            crop = crop.resize((max(1, round(crop.width*scale)), max(1, round(crop.height*scale))))
            canvas.paste(crop, (column*400+5, row*170+36))
    canvas.save(run.OUT / 'regressions-clean.png')
    (run.OUT / 'visual-audit-cases.json').write_text(json.dumps(selected, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    main()
