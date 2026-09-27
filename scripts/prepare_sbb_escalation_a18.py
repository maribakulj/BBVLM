"""Route only reader-declared uncertainty; supply target-line mask, no text GT.

Masking changes presentation; the Sol follow-up is not a controlled model-only
comparison. Original crops remain alongside masked crops, never overwritten.
"""
from pathlib import Path
import json
import cv2
import numpy as np
from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'experiments/loop/reference-a18'


def main(selection='uncertain', output_dir=None):
    raw = json.loads((BASE/'luna-response.json').read_text())
    lines = raw['lines'] if isinstance(raw, dict) else raw
    if selection not in ('uncertain', 'not_uncertain'):
        raise ValueError(selection)
    ids = {r['id'] for r in lines if bool(r.get('uncertain')) == (selection == 'uncertain')}
    # Text fields in this private binding are never included in reader inputs.
    binding = json.loads((BASE/'private-reference.json').read_text())
    split = json.loads((BASE/'split.json').read_text())
    pages = {r['work']:r for r in split['pages'] if r['role']=='audit'}
    out=output_dir or BASE/'sol-input';out.mkdir(parents=True, exist_ok=True)
    items=[]
    for row in binding:
        if row['id'] not in ids:
            continue
        p=pages[row['work']]
        root=E.parse(str(BASE/'source'/p['xml']))
        line=next(l for l in root.findall('.//{*}TextLine') if l.get('id')==row['line_id'])
        points=np.array([list(map(float,s.split(','))) for s in line.find('{*}Coords').get('points').split()])
        image=cv2.imread(str(BASE/'source'/p['image']))
        x0,y0,x1,y1=row['crop_bbox'];crop=image[y0:y1,x0:x1].copy()
        mask=np.zeros(crop.shape[:2],np.uint8)
        cv2.fillPoly(mask,[np.rint(points-[x0,y0]).astype(np.int32)],255)
        # One pixel of tolerance for the annotation boundary, fixed for all.
        mask=cv2.dilate(mask,np.ones((3,3),np.uint8))
        crop[mask==0]=255
        path=out/f"{row['id']}.png";cv2.imwrite(str(path),crop)
        items.append({'id':row['id'],'image':str(path.relative_to(ROOT)),
                      'original_image':str((BASE/'input'/f"{row['id']}.png").relative_to(ROOT))})
    request={'items':items, 'selection':f'all Luna {selection}; no score or GT used for item selection',
        'task':'Transcribe only the isolated target line in each mask; original image supplied for glyph context. No neighboring lines. Preserve visible historical spelling/case, long s, abbreviation marks and punctuation. Do not insert ellipses for line continuations. Use readable Unicode, flag glyph-encoding uncertainty rather than guessing private-use codes. JSON lines [{id,text,uncertain,reason}].',
        'confound':'target polygon presentation and model changed together; not pure model ablation'}
    (out/'request.json').write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
    print(len(items))


if __name__=='__main__':main()
