"""Render every A22 proposed box for post-score visual audit."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/loop'
OUT=BASE/'reserve-a22';SOURCE=BASE/'reference-a18'

def main():
    refs={r['id']:r for r in json.loads((OUT/'private-reference.json').read_text())}
    report=json.loads((OUT/'report.json').read_text())
    panels=[]
    for row in report['geometry']['per_line']:
        if not row['predicted_words']: continue
        ref=refs[row['id']];im=Image.open(SOURCE/'source'/ref['source_image']).convert('RGB')
        x0,y0,x1,y1=ref['crop_bbox'];crop=im.crop((x0,y0,x1,y1));draw=ImageDraw.Draw(crop)
        for w in ref['words']:
            a=w['bbox'];draw.rectangle([a[0]-x0,a[1]-y0,a[2]-x0,a[3]-y0],outline=(0,150,0),width=2)
        for a in row['prediction']['boxes']:
            draw.rectangle([a[0]-x0,a[1]-y0,a[2]-x0-1,a[3]-y0-1],outline=(200,0,200),width=1)
        panel=Image.new('RGB',(max(900,crop.width),crop.height+35),'white')
        ImageDraw.Draw(panel).text((3,3),f"{row['id']} GT green / A19 purple / IoU {min(row['matched_ious']):.3f}-{max(row['matched_ious']):.3f}",fill='black')
        panel.paste(crop,(0,35));panels.append(panel)
    canvas=Image.new('RGB',(max(p.width for p in panels),sum(p.height for p in panels)),'white')
    y=0
    for panel in panels: canvas.paste(panel,(0,y));y+=panel.height
    dest=OUT/'visual-audit/proposed.png';dest.parent.mkdir(exist_ok=True);canvas.save(dest)
    (OUT/'visual-audit/report.json').write_text(json.dumps({
      'scope':'all A22 emitted boxes; post-score audit derivative',
      'lines':[r['id'] for r in report['geometry']['per_line'] if r['predicted_words']],
      'words':sum(r['predicted_words'] for r in report['geometry']['per_line']),
      'overlay_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
      'colors':{'source_word_boxes':'green','candidate_boxes':'purple'},
      'root_visual_observation':'All seven proposals are inside/plausibly coincident with source word boxes; last six exhibit small ink-tight versus polygon margins consistent with measured IoU. This is not independent human adjudication of source perfection.'
    },indent=2)+'\n')
    print(dest)

if __name__=='__main__':main()
