#!/usr/bin/env python
"""Essai image-only : composantes entières et baselines BLLA automatiques.

Rejoue tous les IDs, avec les mêmes transcriptions et ancres CTC sauvegardées.
Ne lit aucune référence. Les positions de caractères restent historiques ;
les sorties servent à la notation et ne constituent pas un export certifié.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'src/boxers'),str(ROOT/'scripts')]
import forcectc
from baseline_ink import BaselineInk
from rejouer_masque_lignes import finalise


def replay(image,directory,output):
    directory=Path(directory);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    image_hash=hashlib.sha256(Path(image).read_bytes()).hexdigest()
    for name in ('pipeline-config.json','segmentation-config.json'):
        if json.loads((directory/name).read_text()).get('image_sha256')!=image_hash:
            raise ValueError('Image et checkpoints incohérents : '+name)
    gray=cv2.imread(str(image),0)
    if gray is None:raise ValueError('Image native illisible')
    segmentation=directory/'segmentation.json'
    rows=json.loads(segmentation.read_text());layout={r['id']:r for r in rows}
    local={};cache_hashes={}
    for path in sorted((directory/'geometry-cache').glob('*.json')):
        if path.name=='state.json':continue
        data=json.loads(path.read_text());a=data['annotation'];lid=a['id']
        if lid in local:raise ValueError('Checkpoints concurrents pour '+lid)
        local[lid]=a;cache_hashes[lid]=hashlib.sha256(path.read_bytes()).hexdigest()
    if set(local)!=set(layout):raise ValueError('Rejeu complet requis : chaque ID automatique doit être présent')
    native=BaselineInk(gray,rows)
    variants={name:[] for name in ('rectangle','baseline_filter','baseline_components','baseline_components_full')}
    original_mask=forcectc.alignment_mask;audits=[]
    for lid,row in layout.items():
        source=local[lid]
        if source['status']!='placee':
            for result in variants.values():result.append(json.loads(json.dumps(source)))
            continue
        alignment=source['alignment'];box=source['reading_bbox']
        positions=alignment.get('line_char_positions',source['chars'])
        if len(positions)!=len(source['text']):raise ValueError('Ancres et texte incohérents : '+lid)
        step=alignment['input_width']/alignment['frames']*(box[2]-box[0])/(alignment['input_width']-2*alignment['padding'])
        centers={i:p[0]+step/2 for i,p in enumerate(positions)}
        expanded=native.component_box(lid,box)
        details=dict(id=lid,source_box=box,component_box=expanded,variants={})
        for mode,result in variants.items():
            a=json.loads(json.dumps(source));crop=expanded if mode.endswith('_full') else box
            a['geometry_replay_scope']='diagnostic; historical character positions unchanged; not training certification'
            def owner_mask(*args,**kwargs):
                if mode=='baseline_filter':
                    result,audit=native.filter_mask(lid,*original_mask(*args,**kwargs))
                    details['variants'][mode]=audit
                    return result
                return native.mask(lid,crop)
            try:
                forcectc.alignment_mask=original_mask if mode=='rectangle' else owner_mask
                boxes,meta=forcectc.word_geometry(gray,crop,a['text'],centers,'ink_clean_baseline')
                a['words']=[dict(text=w,x0=b[0],y0=b[1],x1=b[2],y1=b[3],synthetic=False)
                            for w,b in zip(a['text'].split(),boxes)]
                if mode!='rectangle':meta['component_ownership']=native.audit['version']
                a['alignment']['word_geometry']=meta
                before=row['bbox']
                a['bbox']=[min(before[0],min(b[0] for b in boxes)),min(before[1],min(b[1] for b in boxes)),
                           max(before[2],max(b[2] for b in boxes)+1),max(before[3],max(b[3] for b in boxes)+1)]
                if mode!='rectangle':
                    mask,ox,oy=native.mask(lid,expanded);covered=np.zeros_like(mask,bool)
                    for x0,y0,x1,y1 in boxes:
                        covered[max(0,y0-oy):y1-oy+1,max(0,x0-ox):x1-ox+1]=True
                    details['variants'].setdefault(mode,{}).update(owned_ink_pixels=int(np.count_nonzero(mask)),
                        owned_ink_outside_words=int(np.count_nonzero((mask>0)&~covered)))
            except ValueError as exc:
                a.update(status='mask_replay_refused',reason=str(exc))
                details['variants'].setdefault(mode,{}).update(refused=str(exc))
            finally:forcectc.alignment_mask=original_mask
            result.append(a)
        audits.append(details)
    summary={}
    for mode,result in variants.items():
        summary[mode]=finalise(result)
        (output/(mode+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2))
    provenance=dict(image_sha256=image_hash,
        segmentation_sha256=hashlib.sha256(segmentation.read_bytes()).hexdigest(),
        cache_sha256=cache_hashes,implementation_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (Path(__file__),ROOT/'src/baseline_ink.py',ROOT/'src/boxers/forcectc.py',ROOT/'scripts/rejouer_masque_lignes.py')},
        anchors='parent line CTC, including line_char_positions for historical word-scope caches',
        reference_inputs=False,criteria_met=False,promoted=False)
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2))
    np.savez_compressed(output/'native-components.npz',stats=native.stats,owners=native.owners,
                        line_ids=np.array([r['id'] for r in rows]))
    (output/'ownership-audit.json').write_text(json.dumps(dict(native=native.audit,lines=audits),indent=2))
    (output/'summary.json').write_text(json.dumps(dict(variants=summary,criteria_met=False,promoted=False,
        scope='complete paired geometry diagnostic; independent scores required; no glyph certification'),indent=2))
    print(json.dumps(summary,ensure_ascii=False),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('image');ap.add_argument('directory');ap.add_argument('output')
    args=ap.parse_args();replay(args.image,args.directory,args.output)
