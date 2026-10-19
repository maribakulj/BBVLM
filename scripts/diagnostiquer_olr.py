#!/usr/bin/env python
"""Mesure native OLR seule, depuis une segmentation intégralement automatique.

Aucune entrée privée, VT, boîte de mot ou région humaine. Les sorties ne sont
pas éligibles à l'entraînement et ne certifient pas le pipeline complet.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from bb_layout import nontext_regions,text_regions
from olr_groups import infer


def run(manifest,page_id,segmentation,layout,pane,output,visual_detail='overview',prepare_only=False,mode='grouped',local_batch_groups=8):
    public=json.loads(Path(manifest).read_text())
    if any(set(r)-{'id','family','split','image','image_sha256'} for r in public['pages']):
        raise ValueError('Entrées privées interdites pour le diagnostic OLR')
    row=next(r for r in public['pages'] if r['id']==page_id)
    if hashlib.sha256(Path(row['image']).read_bytes()).hexdigest()!=row['image_sha256']:
        raise ValueError('Image modifiée')
    candidates=json.loads(Path(layout).read_text())
    if candidates['image_sha256']!=row['image_sha256']:raise ValueError('Autre image de layout')
    source=json.loads(Path(segmentation).read_text())
    if any(not r.get('source','').startswith('kraken-blla/') for r in source):
        raise ValueError('Segmentation automatique requise')
    annotations=[dict(id=r['id'],bbox=r['bbox'],text='',uncertain=True,
                      status='diagnostic_layout_only_no_vt',training_eligible=False) for r in source]
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    (out/'annotations.json').write_text(json.dumps(annotations,ensure_ascii=False,indent=2))
    if mode=='local':
        from olr_local import run as run_local
        provenance=dict(scope='OLR-only diagnostic; VT, word geometry and training export absent',
                        page_id=page_id,image_sha256=row['image_sha256'],
                        segmentation_sha256=hashlib.sha256(Path(segmentation).read_bytes()).hexdigest(),
                        layout_sha256=hashlib.sha256(Path(layout).read_bytes()).hexdigest(),criteria_met=False)
        (out/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2))
        print(json.dumps(run_local(row['image'],annotations,text_regions(candidates),nontext_regions(candidates),
                                  pane,out,local_batch_groups,prepare_only)))
        return
    if prepare_only:
        from olr_groups import groups,write_inputs
        geometry=groups(annotations,text_regions(candidates))
        files,overview=write_inputs(row['image'],annotations,geometry,nontext_regions(candidates),out,visual_detail)
        (out/'prepared-inputs.json').write_text(json.dumps(dict(page_id=page_id,scope='OLR-only no VT',
            visual_detail=visual_detail,groups=geometry,files=files,overview=overview,submitted=False,criteria_met=False),indent=2))
        print(json.dumps(dict(groups=len(geometry),files=len(files),submitted=False,criteria_met=False)))
        return
    result=infer(row['image'],annotations,pane,out/'olr-jobs',regions=nontext_regions(candidates),
                 text_regions=text_regions(candidates),scope='layout_only_no_vt',visual_detail=visual_detail)
    (out/'olr.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    provenance=dict(scope='OLR-only diagnostic; VT, word geometry and training export absent',
                    page_id=page_id,image_sha256=row['image_sha256'],
                    segmentation_sha256=hashlib.sha256(Path(segmentation).read_bytes()).hexdigest(),
                    layout_sha256=hashlib.sha256(Path(layout).read_bytes()).hexdigest(),criteria_met=False)
    (out/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2))
    print(json.dumps(dict(lines=len(annotations),blocks=len(result['blocks']),articles=len(result['articles']),
                         scope='OLR-only diagnostic',criteria_met=False)))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('manifest');ap.add_argument('page_id')
    ap.add_argument('segmentation');ap.add_argument('layout');ap.add_argument('output')
    ap.add_argument('--gemini-pane',required=True)
    ap.add_argument('--visual-detail',choices=('overview','native'),default='overview')
    ap.add_argument('--mode',choices=('grouped','local'),default='grouped')
    ap.add_argument('--local-batch-groups',type=int,default=8)
    ap.add_argument('--prepare-only',action='store_true');args=ap.parse_args()
    run(args.manifest,args.page_id,args.segmentation,args.layout,args.gemini_pane,args.output,args.visual_detail,args.prepare_only,
        args.mode,args.local_batch_groups)
