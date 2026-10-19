"""Segmenteur expérimental par composantes natives dans des régions détectées.

Les régions sont des sorties image-only PP-DocLayout, jamais des régions de
référence. Tous les candidats restent dans la sortie pour compter les erreurs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import time
import cv2
import numpy as np
from bb_layout import text_regions
from segmentation import deduplicate


def predicted_y(group, x, scale):
    slope,offset=group['fit']
    return slope*x+offset


def update_fit(group, scale):
    coords=np.array([[b[0]+b[2]/2,b[1]+b[3]] for b in group['anchors']])
    group['left']=min(b[0] for b in group['anchors'])
    group['right']=max(b[0]+b[2] for b in group['anchors'])
    group['fit']=(0.,float(np.median(coords[:,1])))
    if len(coords)>3 and np.ptp(coords[:,0])>scale*3:
        slope,offset=np.polyfit(coords[:,0],coords[:,1],1)
        if abs(slope)<=.06:group['fit']=(float(slope),float(offset))


def region_lines(gray, box):
    x0,y0,x1,y1=map(int,box);crop=gray[y0:y1,x0:x1]
    if min(crop.shape)<3:return []
    binary=cv2.adaptiveThreshold(crop,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV,51,12)
    _,_,stats,_=cv2.connectedComponentsWithStats(binary,8)
    raw=[tuple(map(int,s)) for s in stats[1:]]
    heights=[h for x,y,w,h,a in raw if h>=5 and a>=12 and .1*h<=w<=3*h and h<crop.shape[0]*.5]
    if not heights:return []
    scale=float(np.median(heights))
    anchors=[s for s in raw if s[3]>=scale*.6 and s[3]<=scale*3.5 and
             s[2]<=scale*8 and s[4]>=max(8,scale*scale*.03)]
    anchors.sort(key=lambda s:(s[0]+s[2]/2,s[1]))
    groups=[]
    for component in anchors:
        x,y,w,h,area=component;cx=x+w/2;bottom=y+h
        choices=[]
        for gi,group in enumerate(groups):
            previous=group['right']
            if x-previous>scale*4:continue
            residual=abs(bottom-predicted_y(group,cx,scale))
            if residual<=scale*.6:choices.append((residual,gi))
        if choices:
            group=groups[min(choices)[1]];group['anchors'].append(component);update_fit(group,scale)
        else:
            group=dict(anchors=[component],fragments=[]);update_fit(group,scale);groups.append(group)
    anchor_set=set(anchors)
    for component in raw:
        if component in anchor_set:continue
        x,y,w,h,area=component
        if area<3 or w>scale*8 or h>scale*3.5:continue
        cx=x+w/2;bottom=y+h;choices=[]
        for gi,group in enumerate(groups):
            left=group['left'];right=group['right']
            if cx<left-scale or cx>right+scale:continue
            residual=abs(bottom-predicted_y(group,cx,scale))
            if residual<=scale*1.5:choices.append((residual,gi))
        if choices:groups[min(choices)[1]]['fragments'].append(component)
    rows=[]
    for group in groups:
        parts=group['anchors']+group['fragments']
        a=min(s[0] for s in parts);b=min(s[1] for s in parts)
        c=max(s[0]+s[2] for s in parts);d=max(s[1]+s[3] for s in parts)
        bbox=[max(x0,x0+a-2),max(y0,y0+b-2),min(x1,x0+c+2),min(y1,y0+d+2)]
        baseline=[[x0+a,y0+predicted_y(group,a,scale)],
                  [x0+c,y0+predicted_y(group,c,scale)]]
        rows.append(dict(bbox=bbox,baseline=baseline,interior=True,source='native-components-v1',
                         anchors=len(group['anchors']),fragments=len(group['fragments']),component_height=scale))
    return rows


def segment(image, layout):
    if hashlib.sha256(Path(image).read_bytes()).hexdigest()!=layout['image_sha256']:
        raise ValueError('Régions de détection issues d’une autre image')
    cv2.setNumThreads(2)
    gray=cv2.imread(str(image),cv2.IMREAD_GRAYSCALE)
    if gray is None:raise ValueError('image illisible')
    rows=[]
    for region in text_regions(layout):
        a,b,c,d=region['bbox']
        box=[max(0,math.floor(a)-16),max(0,math.floor(b)-16),
             min(gray.shape[1],math.ceil(c)+16),min(gray.shape[0],math.ceil(d)+16)]
        rows.extend({**line,'detector_region_id':region['id']} for line in region_lines(gray,box))
    return deduplicate(rows)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('image');ap.add_argument('layout');ap.add_argument('output');args=ap.parse_args()
    t=time.time();rows=segment(args.image,json.loads(Path(args.layout).read_text()))
    Path(args.output).write_text(json.dumps(rows,ensure_ascii=False,indent=2))
    print(json.dumps(dict(lines=len(rows),seconds=time.time()-t,scope='experimental image-only segmentation; not certified')))
