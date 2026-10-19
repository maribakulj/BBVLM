#!/usr/bin/env python
"""Comparer le filtre d'encre sur toutes les images d'un split public.

Seulement images et segmentation automatique ; sans VT, mots ni références.
Les résultats mesurent une hypothèse géométrique et ne certifient aucun export.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from baseline_ink import BaselineInk
from ink import alignment_mask


def run(manifest,segmentation,output,split,source_geometry='ink'):
    public=json.loads(Path(manifest).read_text())
    allowed={'id','family','split','image','image_sha256'}
    if any(set(r)!=allowed for r in public['pages']):raise ValueError('Manifeste public seul autorisé')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);summaries=[]
    for page in public['pages']:
        if page['split']!=split:continue
        image=Path(page['image']);digest=hashlib.sha256(image.read_bytes()).hexdigest()
        if digest!=page['image_sha256']:raise ValueError('Image modifiée : '+page['id'])
        source=Path(segmentation)/page['id'];config=json.loads((source/'segmentation-config.json').read_text())
        if config['image_sha256']!=digest:raise ValueError('Cache d’une autre image')
        source_file=source/('segmentation-ink.json' if source_geometry=='ink' else 'segmentation.json')
        rows=json.loads(source_file.read_text());gray=cv2.imread(str(image),0)
        native=BaselineInk(gray,rows);out=output/page['id'];out.mkdir(parents=True,exist_ok=True)
        result=[];audits=[]
        for row in rows:
            mask,ox,oy=alignment_mask(gray,row['bbox'],clean_upper_branches=True,clean_below_baseline=True)
            (filtered,ox,oy),audit=native.filter_mask(row['id'],mask,ox,oy)
            points=np.argwhere(filtered>0);r=dict(row)
            if audit.get('unsupported_baseline'):
                r['candidate_status']='unsupported_baseline_original_detection_preserved'
            elif len(points):
                y0,x0=points.min(axis=0);y1,x1=points.max(axis=0)+1
                r['bbox']=[int(ox+x0),int(oy+y0),int(ox+x1),int(oy+y1)]
                r['candidate_status']='native_ink_observed'
            else:r['candidate_status']='native_ink_unresolved_original_detection_preserved'
            result.append(r);audits.append(dict(id=row['id'],**audit,mask_pixels=int(np.count_nonzero(mask)),
                                               filtered_pixels=int(np.count_nonzero(filtered))))
        (out/'segmentation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
        summary=dict(id=page['id'],lines=len(rows),boxes_changed=sum(a['bbox']!=b['bbox'] for a,b in zip(rows,result)),
                     unresolved=sum(r['candidate_status']!='native_ink_observed' for r in result),
                     removed_pixels=sum(a['removed_pixels'] for a in audits),criteria_met=False,promoted=False)
        provenance=dict(image_sha256=digest,source_geometry=source_geometry,source_segmentation=str(source_file),
            source_segmentation_sha256=hashlib.sha256(source_file.read_bytes()).hexdigest(),
            implementation_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (Path(__file__),ROOT/'src/baseline_ink.py',ROOT/'src/ink.py')},
            native=native.audit,scope='all split images; source-only line geometry diagnostic; no VT or full-pipeline certificate')
        (out/'audit.json').write_text(json.dumps(dict(summary=summary,provenance=provenance,lines=audits),indent=2))
        summaries.append(summary);print(json.dumps(summary),flush=True)
        del native,gray
    (output/'summary.json').write_text(json.dumps(dict(split=split,pages=summaries,criteria_met=False,promoted=False),indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('manifest');ap.add_argument('segmentation');ap.add_argument('output')
    ap.add_argument('--split',choices=('dev','reserved'),required=True)
    ap.add_argument('--source-geometry',choices=('raw','ink'),default='ink');args=ap.parse_args()
    run(args.manifest,args.segmentation,args.output,args.split,args.source_geometry)
