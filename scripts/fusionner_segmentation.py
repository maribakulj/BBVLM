#!/usr/bin/env python
"""Compléter des sorties automatiques figées, sans lire de référence."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import cv2
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from segmentation import atomic_json
from segmentation_fusion import fuse


def run(manifest,primary,supplement,output,split):
    manifest=json.loads(Path(manifest).read_text())
    allowed={'id','family','split','image','image_sha256'}
    if any(set(row)!=allowed for row in manifest['pages']):
        raise ValueError('Seules les images publiques sont autorisées')
    for row in manifest['pages']:
        if row['split']!=split:continue
        if hashlib.sha256(Path(row['image']).read_bytes()).hexdigest()!=row['image_sha256']:
            raise ValueError('Image source modifiée')
        out=Path(output)/row['id'];out.mkdir(parents=True,exist_ok=True)
        gray=cv2.imread(row['image'],cv2.IMREAD_GRAYSCALE)
        for name in ('segmentation.json','segmentation-ink.json'):
            paths=[Path(base)/row['id']/name for base in (primary,supplement)]
            if not all(path.exists() for path in paths):
                raise ValueError('Une passe automatique est incomplète : '+row['id'])
            inputs=[json.loads(path.read_text()) for path in paths]
            if any(not r.get('source','').startswith('kraken-blla/') or 'text' in r or 'words' in r
                   for rows in inputs for r in rows):
                raise ValueError('Seules les sorties automatiques BLLA sont autorisées')
            rows,audit=fuse(gray,*inputs)
            audit.update(image_sha256=row['image_sha256'],
                         input_sha256=[hashlib.sha256(path.read_bytes()).hexdigest() for path in paths],
                         implementation_sha256=hashlib.sha256((ROOT/'src/segmentation_fusion.py').read_bytes()).hexdigest())
            atomic_json(out/name,rows);atomic_json(out/(name.removesuffix('.json')+'-fusion-audit.json'),audit)
        print(json.dumps(dict(id=row['id'],lines=len(rows),added=audit['added'],criteria_met=False)),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('manifest');ap.add_argument('primary')
    ap.add_argument('supplement');ap.add_argument('output');ap.add_argument('--split',choices=('dev','reserved'),required=True)
    args=ap.parse_args();run(args.manifest,args.primary,args.supplement,args.output,args.split)
