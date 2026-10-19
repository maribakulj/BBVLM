#!/usr/bin/env python
"""Passe image-only sur la suite fixe, sans accès aux références."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import time
import shutil
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from segmentation import segment,refine_lines


def run(manifest, outputs, split, strategy='auto',cache_from=None):
    manifest=json.loads(Path(manifest).read_text())
    allowed={'id','family','split','image','image_sha256'}
    if any(set(row)!=allowed for row in manifest['pages']):
        raise ValueError('Refus du manifeste contenant des références')
    root=Path(outputs);root.mkdir(parents=True,exist_ok=True)
    report=[]
    for row in manifest['pages']:
        if row['split']!=split:continue
        if hashlib.sha256(Path(row['image']).read_bytes()).hexdigest()!=row['image_sha256']:
            raise ValueError('Image modifiée : '+row['id'])
        out=root/row['id'];out.mkdir(parents=True,exist_ok=True)
        if cache_from:
            source=Path(cache_from)/row['id']/'segmentation-tiles'
            target=out/'segmentation-tiles';target.mkdir(exist_ok=True)
            if source.resolve()==target.resolve():raise ValueError('Source de cache et essai doivent être distincts')
            for cached in source.glob('*.json'):
                if cached.name!='state.json' and not (target/cached.name).exists():shutil.copy2(cached,target/cached.name)
        config=dict(image_sha256=row['image_sha256'],strategy=strategy,version='blla-rectangles-v1')
        config_path=out/'segmentation-config.json';dest=out/'segmentation.json'
        # auto-v2 change uniquement le routage des petits canevas. Réutiliser
        # les sorties achevées lorsque cette branche est inactive, sans refaire
        # une inférence en l'absence d'anciens checkpoints par tuile.
        if cache_from and strategy=='auto-v2' and Image.open(row['image']).height>=1800 and not dest.exists():
            old=Path(cache_from)/row['id'];previous=old/'segmentation-config.json'
            expected=dict(image_sha256=row['image_sha256'],strategy='auto',version='blla-rectangles-v1')
            if previous.exists() and json.loads(previous.read_text())==expected and (old/'segmentation.json').exists():
                shutil.copy2(old/'segmentation.json',dest);config_path.write_text(json.dumps(config,indent=2))
                (out/'reused-source-output.json').write_text(json.dumps(dict(
                    source=str((old/'segmentation.json').resolve()),source_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
                    image_sha256=row['image_sha256'],reason='auto-v2 short-canvas branch inactive; large-page detector unchanged'),indent=2))
        if dest.exists() and config_path.exists():
            if json.loads(config_path.read_text())!=config:raise ValueError('Configuration différente : '+str(out))
            lines=json.loads(dest.read_text());seconds=None
        else:
            t=time.time();lines=segment(row['image'],strategy,cache_directory=out/'segmentation-tiles');seconds=time.time()-t
            dest.write_text(json.dumps(lines,ensure_ascii=False,indent=2))
            config_path.write_text(json.dumps(config,indent=2))
        # Toutes les lignes restent présentes dans les deux variantes.
        refined=refine_lines(row['image'],lines)
        (out/'segmentation-ink.json').write_text(json.dumps(refined,ensure_ascii=False,indent=2))
        record=dict(id=row['id'],lines=len(lines),seconds=seconds,criteria_met=False)
        report.append(record);print(json.dumps(record),flush=True)
        (root/'segmentation-state.json').write_text(json.dumps(dict(split=split,strategy=strategy,completed=report),indent=2))
    return report


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('manifest');ap.add_argument('outputs')
    ap.add_argument('--split',choices=('dev','reserved'),required=True)
    ap.add_argument('--strategy',choices=('full','tiles','auto','auto-v2'),default='auto')
    ap.add_argument('--cache-from',help='Copy cached tiles; source trial remains untouched')
    args=ap.parse_args();run(args.manifest,args.outputs,args.split,args.strategy,args.cache_from)
