#!/usr/bin/env python
"""Rejeu isolé de copies physiques, sans suppression d'IDs ni référence."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import cv2
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from duplicate_fragments import detect,conserve_fragment_ink
from rejouer_masque_lignes import finalise

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('image');ap.add_argument('annotations');ap.add_argument('output')
    ap.add_argument('--mask-source',choices=('local_clean','global_source'),default='local_clean');args=ap.parse_args()
    rows=json.loads(Path(args.annotations).read_text());result=detect(cv2.imread(args.image,0),rows,args.mask_source)
    if args.mask_source=='global_source':result=conserve_fragment_ink(result)
    aliases={d['child_id']:d for d in result['decisions']}
    for row in result['annotations']:
        if row['id'] in aliases:
            row['status']='fragment_physique_duplique';row['duplicate_fragment']=aliases[row['id']]
        elif row['status'] in ('retenue','superposition_inter_lignes','ajustement_encre_suspect'):
            row['status']='placee'
    result['replay']=finalise(result['annotations'])
    result['source_annotations_sha256']=hashlib.sha256(Path(args.annotations).read_bytes()).hexdigest()
    result['implementation_sha256']=hashlib.sha256(Path(ROOT/'src/duplicate_fragments.py').read_bytes()).hexdigest()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    (out/'annotations.json').write_text(json.dumps(result['annotations'],ensure_ascii=False,indent=2))
    (out/'duplicate-diagnostic.json').write_text(json.dumps({k:v for k,v in result.items() if k!='annotations'},ensure_ascii=False,indent=2))
    print(json.dumps(dict(duplicates=len(aliases),replay=result['replay'],criteria_met=False)))
