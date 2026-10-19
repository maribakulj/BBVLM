#!/usr/bin/env python
"""Diagnostic de géométrie sur lectures existantes, sans entrée de référence.

Le manifeste ne contient que image, lignes détectées et réponse de lecture.
Chaque modèle est évalué une fois ; ses pics imposés sont rejoués avec deux
frontières. Les lectures incertaines restent signalées, sans export training.
"""
from pathlib import Path
import argparse
import json
import sys
import cv2

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'src/boxers')]
from forcectc import ForceCTC,word_geometry
from lecture import JSONReader,LineRequest
from produire import Ligne
from PIL import Image


def replay(manifest,output):
    manifest=json.loads(Path(manifest).read_text())
    allowed={'id','image','lines','response'}
    if any(set(p)!=allowed for p in manifest['pages']):
        raise ValueError('Manifeste de rejeu doit contenir uniquement images/lignes/réponses')
    boxer=ForceCTC(boundary_mode='midpoint');out=Path(output);out.mkdir(parents=True,exist_ok=True)
    for page in manifest['pages']:
        requests=[LineRequest(r['id'],tuple(r['bbox'])) for r in json.loads(Path(page['lines']).read_text())]
        image=Image.open(page['image']);gray=cv2.imread(page['image'],0)
        readings=JSONReader(page['response']).read_lines(image,requests)
        variants={'midpoint':[],'ink':[],'ink_clean':[],'ink_clean_baseline':[]}
        for request,reading in zip(requests,readings):
            if not reading.text.strip():
                for mode in variants:variants[mode].append(dict(id=request.id,bbox=list(request.bbox),text=reading.text,status='absent',training_eligible=False))
                continue
            boxer.boxes(gray,Ligne(reading.text,request.bbox))
            chars=boxer.last_char_positions;alignment=boxer.last_alignment
            step=alignment['input_width']/alignment['frames']*(request.bbox[2]-request.bbox[0])/(alignment['input_width']-2*alignment['padding'])
            centers={i:p[0]+step/2 for i,p in enumerate(chars)}
            for mode in variants:
                row=dict(id=request.id,bbox=list(request.bbox),text=reading.text,uncertain=reading.uncertain,
                         provider=reading.provider,model=reading.model,chars=chars,
                         scope='geometry-only diagnostic; input line boxes may be external',training_eligible=False)
                try:
                    boxes,meta=word_geometry(gray,request.bbox,reading.text,centers,mode)
                    row.update(words=[dict(text=w,x0=b[0],y0=b[1],x1=b[2],y1=b[3],synthetic=False) for w,b in zip(reading.text.split(),boxes)],
                               alignment={**alignment,'word_geometry':meta},status='placed_diagnostic')
                except ValueError as exc:row.update(status='refused',reason=str(exc))
                variants[mode].append(row)
        directory=out/page['id'];directory.mkdir(exist_ok=True)
        for mode,rows in variants.items():
            (directory/f'{mode}.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
        print(json.dumps(dict(id=page['id'],lines=len(requests),uncertain=sum(r.uncertain for r in readings),
                             ink_refused=sum(r['status']=='refused' for r in variants['ink']))),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('manifest');ap.add_argument('output');a=ap.parse_args()
    replay(a.manifest,a.output)
