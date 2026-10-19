#!/usr/bin/env python
"""Rejeu image-only des masques depuis les placements CTC sauvegardés.

Les polygones proviennent du détecteur automatique, jamais d'une référence.
Les transcriptions/ancres restent identiques ; toute ligne reste dans le résultat.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'src/boxers')]
import forcectc
import correct


def finalise(rows):
    active=[];collisions=set()
    for lid,word in sorted(((a['id'],w) for a in rows if a.get('words') and a['status']=='placee' for w in a['words']),key=lambda item:item[1]['y0']):
        active=[(other,box) for other,box in active if box['y1']>=word['y0']]
        for other,box in active:
            if other!=lid and min(box['x1'],word['x1'])>=max(box['x0'],word['x0']):collisions.update((lid,other))
        active.append((lid,word))
    placed=[a for a in rows if a['status']=='placee' and a['id'] not in collisions]
    threshold=correct.seuil_auto([a['cout'] for a in placed]) if len(placed)>=8 else 1.
    for a in rows:
        a['training_eligible']=False
        if a['id'] in collisions:a['status']='superposition_inter_lignes'
        elif a['status']=='placee':
            if a['cout']>threshold*2:a['status']='ajustement_encre_suspect'
            else:a.update(status='retenue',training_eligible=True)
    return dict(lines=len(rows),retained=sum(a['training_eligible'] for a in rows),
                statuses=dict(Counter(a['status'] for a in rows)),threshold=threshold*2)


def replay(image,directory,output):
    directory=Path(directory);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    gray=cv2.imread(str(image),0)
    layout={a['id']:a for a in json.loads((directory/'segmentation.json').read_text())}
    local={}
    for path in (directory/'geometry-cache').glob('*.json'):
        if path.name=='state.json':continue
        data=json.loads(path.read_text());a=data['annotation']
        if a['id'] in local:raise ValueError('Plusieurs checkpoints pour une ligne : sélectionner un essai exact')
        local[a['id']]=a
    if set(local)!=set(layout):raise ValueError('Rejeu incomplet : tous les IDs détectés sont requis')
    variants={'rectangle':[],'detector_polygon':[]};original_mask=forcectc.alignment_mask;audits=[]
    for lid,row in layout.items():
        source=local[lid]
        if source['status']!='placee':
            for rows in variants.values():rows.append(json.loads(json.dumps(source)))
            continue
        alignment=source['alignment'];chars=source['chars'];box=source['reading_bbox']
        step=alignment['input_width']/alignment['frames']*(box[2]-box[0])/(alignment['input_width']-2*alignment['padding'])
        centers={i:p[0]+step/2 for i,p in enumerate(chars)}
        clipping={}
        def polygon_mask(*args,**kwargs):
            mask,ox,oy=original_mask(*args,**kwargs);area=np.zeros_like(mask)
            points=np.rint(np.asarray(row['polygon'])-[ox,oy]).astype(np.int32)
            cv2.fillPoly(area,[points],255)
            masked=cv2.bitwise_and(mask,area)
            clipping.update(pixels_before=int(np.count_nonzero(mask)),pixels_after=int(np.count_nonzero(masked)))
            return masked,ox,oy
        for mode,rows in variants.items():
            a=json.loads(json.dumps(source));a['mask_replay_scope']='automatic source geometry only; independent scores required'
            try:
                forcectc.alignment_mask=original_mask if mode=='rectangle' else polygon_mask
                boxes,meta=forcectc.word_geometry(gray,box,a['text'],centers,'ink_clean_baseline')
                a['words']=[dict(text=w,x0=b[0],y0=b[1],x1=b[2],y1=b[3],synthetic=False) for w,b in zip(a['text'].split(),boxes)]
                a['alignment']['word_geometry']=meta
                before=layout[lid]['bbox']
                a['bbox']=[min(before[0],min(b[0] for b in boxes)),min(before[1],min(b[1] for b in boxes)),
                           max(before[2],max(b[2] for b in boxes)+1),max(before[3],max(b[3] for b in boxes)+1)]
            except ValueError as exc:a.update(status='mask_replay_refused',reason=str(exc))
            finally:forcectc.alignment_mask=original_mask
            rows.append(a)
        audits.append(dict(id=lid,**clipping))
    summary={}
    for mode,rows in variants.items():
        summary[mode]=finalise(rows)
        (output/(mode+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2))
    (output/'mask-audit.json').write_text(json.dumps(audits,indent=2))
    (output/'summary.json').write_text(json.dumps(dict(variants=summary,criteria_met=False,
         scope='paired geometry-only automatic polygon experiment; source chars unchanged, not training certification'),indent=2))
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('image');ap.add_argument('directory');ap.add_argument('output');args=ap.parse_args()
    replay(args.image,args.directory,args.output)
