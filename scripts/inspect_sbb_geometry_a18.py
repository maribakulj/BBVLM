"""Audit derivatives: sampled source/candidate boxes and worst emitted case.

These images are explicitly NOT blind reader inputs or reference replacements.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw
from lxml import etree as E
from audit_sbb_reference_a18 import box

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'experiments/loop/reference-a18'


def main():
    split = json.loads((BASE/'split.json').read_text())
    sample = json.loads((BASE/'private-reference.json').read_text())
    gap = json.loads((ROOT/'experiments/loop/gap-ablation-a19/report.json').read_text())
    rows = {(r['work'],r['line']):r for r in gap['per_line_sbb']}
    worst = sorted([r for r in rows.values() if r['ious']], key=lambda r:min(r['ious']))[:3]
    for page in split['pages']:
        if page['role'] != 'audit':
            continue
        wanted = [r['line_id'] for r in sample if r['work']==page['work']][:2]
        wanted += [r['line'] for r in worst if r['work']==page['work'] and r['line'] not in wanted]
        im = Image.open(BASE/'source'/page['image']).convert('RGB')
        root = E.parse(str(BASE/'source'/page['xml']))
        panels = []
        for line in root.findall('.//{*}TextLine'):
            if line.get('id') not in wanted:
                continue
            b=box(line); x0=max(0,int(b[0])-10); y0=max(0,int(b[1])-15)
            x1=min(im.width,int(b[2])+11); y1=min(im.height,int(b[3])+15)
            crop=im.crop((x0,y0,x1,y1)); d=ImageDraw.Draw(crop)
            for w in line.findall('{*}Word'):
                a=box(w);d.rectangle([a[0]-x0,a[1]-y0,a[2]-x0,a[3]-y0],outline=(0,150,0),width=2)
            r=rows[(page['work'],line.get('id'))]
            for a in r['prediction']['boxes']:
                d.rectangle([a[0]-x0,a[1]-y0,a[2]-x0-1,a[3]-y0-1],outline=(200,0,200),width=1)
            if crop.width>1600:
                crop=crop.resize((1600,round(crop.height*1600/crop.width)))
            panel=Image.new('RGB',(max(700,crop.width),crop.height+25),'white')
            ImageDraw.Draw(panel).text((2,2),f"{line.get('id')} GT=green proposal=purple minIoU={min(r['ious']) if r['ious'] else 'abstain'}",fill='black')
            panel.paste(crop,(0,25));panels.append(panel)
        if panels:
            canvas=Image.new('RGB',(max(p.width for p in panels),sum(p.height for p in panels)), 'white')
            y=0
            for p in panels:canvas.paste(p,(0,y));y+=p.height
            dest=BASE/'visual-audit'/f"{page['work']}.png"
            dest.parent.mkdir(exist_ok=True);canvas.save(dest)
    print(json.dumps({'worst':[{k:r[k] for k in ('work','line','ious','prediction')} for r in worst]},indent=2))


if __name__ == '__main__':
    main()
