"""Raccord horizontal image-only, borné par les régions et la ligne de base.

Variante expérimentale : conserver chaque ID et toutes les anciennes boîtes.
Aucune entrée de transcription ou de référence n'est admise.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from ink import alignment_mask
from bb_layout import text_regions


PARAMETERS=dict(region_coverage=.6,body_min_height=.3,body_max_height=.95,
                baseline_tolerance=.18,maximum_gap=1.3,component_margin=.25)


def grow_components(gray,source,corridor):
    x0,y0,x1,y1=map(int,source);height=y1-y0
    a,b,c,d=corridor
    roi=[max(0,min(x0,int(a)-4)),y0,min(gray.shape[1],max(x1,int(np.ceil(c))+4)),y1]
    mask,ox,oy=alignment_mask(gray,roi)
    _,labels,stats,_=cv2.connectedComponentsWithStats(mask,8)
    bodies=[]
    for k,(x,y,w,h,area) in enumerate(stats[1:],1):
        if height*.3<=h<=height*.95:
            bodies.append((k,x+ox,y+oy,w,h,area))
    anchors=[s for s in bodies if s[1]>=x0 and s[1]+s[3]<=x1]
    if len(anchors)<8:return None
    points=np.array([(s[1]+s[3]/2,s[2]+s[4]-1) for s in anchors],float)
    active=np.ones(len(points),bool);trend=np.array([0.,float(np.median(points[:,1]))])
    for _ in range(3):
        if active.sum()<8:break
        trend=np.polyfit(points[active,0],points[active,1],1)
        residual=points[:,1]-np.polyval(trend,points[:,0])
        active=np.abs(residual-np.median(residual))<=max(2,height*.08)
    if abs(trend[0])>.1:return None
    coherent=[s for s in bodies if abs(s[2]+s[4]-1-np.polyval(trend,s[1]+s[3]/2))<=height*.18]
    coherent.sort(key=lambda s:s[1]);left=x0;right=x1;selected=[]
    for s in reversed(coherent):
        if s[1]>=x0:continue
        if left-(s[1]+s[3])>height*1.3:break
        selected.append(s);left=min(left,s[1])
    for s in coherent:
        if s[1]+s[3]<=x1:continue
        if s[1]-right>height*1.3:break
        selected.append(s);right=max(right,s[1]+s[3])
    if not selected:return None
    # Accents et ponctuation proches de ces glyphes gardent leur vraie encre.
    for x,y,w,h,area in stats[1:]:
        x+=ox;y+=oy
        if any(max(0,s[1]-(x+w),x-(s[1]+s[3]))<=height*.25 and
               abs(y+h/2-(s[2]+s[4]/2))<=height*.6 for s in selected):
            left=min(left,int(x));right=max(right,int(x+w))
    return [max(0,int(left)-2),y0,min(gray.shape[1],int(right)+2),y1],dict(
            baseline_trend=trend.tolist(),baseline_anchors=len(anchors),grown_components=len(selected),
            corridor=list(corridor),parameters=PARAMETERS)


def repair(image,rows,layout):
    if layout['image_sha256']!=hashlib.sha256(Path(image).read_bytes()).hexdigest():
        raise ValueError('Régions PP issues d’une autre image')
    gray=cv2.imread(str(image),cv2.IMREAD_GRAYSCALE)
    if gray is None:raise ValueError('Image illisible')
    regions=text_regions(layout);result=[];changes=[]
    for row in rows:
        source=row.get('detector_bbox',row['bbox']);x0,y0,x1,y1=source;area=(x1-x0)*(y1-y0)
        choices=[]
        for region in regions:
            a,b,c,d=region['bbox']
            overlap=max(0,min(x1,c)-max(x0,a))*max(0,min(y1,d)-max(y0,b))/max(1,area)
            if overlap>=.6 and b<=(y0+y1)/2<=d:choices.append(((c-a)*(d-b),region))
        grown=None
        if choices:
            region=min(choices,key=lambda r:r[0])[1]
            grown=grow_components(gray,source,region['bbox'])
        if grown is None:
            result.append(dict(row));continue
        reading,proof=grown
        old=row['bbox'];box=[min(old[0],reading[0]),old[1],max(old[2],reading[2]),old[3]]
        if box==old:
            result.append(dict(row));continue
        updated={**row,'bbox':box,'detector_bbox':reading,'pre_repair_bbox':old,
                 'pre_repair_detector_bbox':source,'repair_source_region':region['id'],
                 'horizontal_repair':proof}
        result.append(updated);changes.append(dict(id=row['id'],before=old,after=box,region=region['id'],proof=proof))
    if [r['id'] for r in result]!=[r['id'] for r in rows]:
        raise ValueError('Réparation a modifié les IDs ou la couverture')
    return result,dict(version='pp-baseline-components-v2',parameters=PARAMETERS,changes=changes,
                      input_lines=len(rows),output_lines=len(result),all_ids_preserved=True,
                      criteria_met=False,scope='experimental image-only source repair; independent evaluation required')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('image');ap.add_argument('lines');ap.add_argument('layout');ap.add_argument('output');args=ap.parse_args()
    rows,audit=repair(args.image,json.loads(Path(args.lines).read_text()),json.loads(Path(args.layout).read_text()))
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    (out/'segmentation.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
    (out/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
    print(json.dumps(dict(lines=len(rows),changed=len(audit['changes']),all_ids_preserved=True,criteria_met=False)))
