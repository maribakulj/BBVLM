#!/usr/bin/env python
"""Distingue intersections de rectangles et encre partagée, sans référence.

Diagnostic seulement : ne modifie aucun refus ni critère gelé de production.
Les masques locaux restent des observations imparfaites, jamais du gold.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from ink import alignment_mask


def audit(image,segmentation,annotations,output,polygon=False):
    gray=cv2.imread(str(image),0)
    layout={r['id']:r for r in json.loads(Path(segmentation).read_text())}
    rows=json.loads(Path(annotations).read_text());by={a['id']:a for a in rows};masks={}
    for a in rows:
        if not a.get('words'):continue
        mask,ox,oy=alignment_mask(gray,a['reading_bbox'],clean_upper_branches=True,clean_below_baseline=True)
        if polygon:
            shape=np.zeros_like(mask)
            cv2.fillPoly(shape,[np.rint(np.asarray(layout[a['id']]['polygon'])-[ox,oy]).astype(np.int32)],255)
            mask=cv2.bitwise_and(mask,shape)
        masks[a['id']]=(mask,ox,oy)
    active=[];pairs=[]
    for lid,w in sorted(((a['id'],w) for a in rows if a.get('words') for w in a['words']),key=lambda a:a[1]['y0']):
        active=[(other,b) for other,b in active if b['y1']>=w['y0']]
        for other,b in active:
            if other==lid:continue
            x0=max(b['x0'],w['x0']);x1=min(b['x1'],w['x1'])+1
            y0=max(b['y0'],w['y0']);y1=min(b['y1'],w['y1'])+1
            if x0>=x1:continue
            def native_pixels(key):
                mask,ox,oy=masks[key];result=np.zeros((y1-y0,x1-x0),bool)
                a=max(x0,ox);b=max(y0,oy);c=min(x1,ox+mask.shape[1]);d=min(y1,oy+mask.shape[0])
                if a<c and b<d:result[b-y0:d-y0,a-x0:c-x0]=mask[b-oy:d-oy,a-ox:c-ox]>0
                return result
            p,q=native_pixels(other),native_pixels(lid)
            pairs.append(dict(line_ids=[other,lid],words=[b['text'],w['text']],
                              intersection=[x0,y0,x1,y1],rectangle_area=(x1-x0)*(y1-y0),
                              shared_mask_pixels=int(np.count_nonzero(p&q)),
                              mask_pixels=[int(np.count_nonzero(p)),int(np.count_nonzero(q))]))
        active.append((lid,w))
    summary=dict(rectangle_intersections=len(pairs),shared_mask_intersections=sum(p['shared_mask_pixels']>0 for p in pairs),
                 rectangle_only_intersections=sum(p['shared_mask_pixels']==0 for p in pairs),
                 affected_lines=len({i for p in pairs for i in p['line_ids']}),
                 criteria_met=False,refusals_modified=False,
                 scope='image-only ink diagnostic; not a geometric certificate or change to frozen zero-overlap criterion',
                 mask_mode='automatic_detector_polygon' if polygon else 'rectangle',pairs=pairs)
    Path(output).write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k!='pairs'}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('image');ap.add_argument('segmentation');ap.add_argument('annotations');ap.add_argument('output')
    ap.add_argument('--polygon',action='store_true');a=ap.parse_args()
    audit(a.image,a.segmentation,a.annotations,a.output,a.polygon)
