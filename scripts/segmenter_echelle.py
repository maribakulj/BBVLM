#!/usr/bin/env python
"""Variante expérimentale d'échelle, exclusivement manifeste public/image."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from segmentation import segment,refine_lines,ink_network_height,atomic_json


def bounded_scale(width,height,glyph,target=20):
    if min(width,height,glyph,target)<=0:raise ValueError('dimensions d’échelle positives requises')
    global_height=max(32,round(height*target/glyph))
    if global_height<=1800 and width*global_height/height<=2400:
        return dict(strategy='full',network_height=global_height)
    th=max(1,min(height,2000,math.floor(1800*glyph/target)))
    network_height=min(1800,max(32,round(th*target/glyph)))
    tw=max(1,min(width,2400,math.floor(2400*th/network_height)))
    return dict(strategy='tiles',network_height=network_height,
                tile_height=th,tile_width=tw,overlap_y=min(400,th//5),overlap_x=min(1200,tw//2))


def run(manifest,output,split,family,routing='full'):
    m=json.loads(Path(manifest).read_text())
    if any(set(r)-{'id','family','split','image','image_sha256'} for r in m['pages']):
        raise ValueError('Manifeste privé interdit')
    for row in m['pages']:
        if row['split']!=split or (family and row['family']!=family):continue
        if hashlib.sha256(Path(row['image']).read_bytes()).hexdigest()!=row['image_sha256']:
            raise ValueError('Image modifiée')
        out=Path(output)/row['id'];out.mkdir(parents=True,exist_ok=True)
        height,proof=ink_network_height(row['image'])
        if routing=='bounded':
            plan=bounded_scale(*proof['image_size'],proof['glyph_height'],proof['target_glyph_height'])
        elif routing=='full':plan=dict(strategy='full',network_height=height)
        else:raise ValueError('routage d’échelle inconnu')
        proof['global_equivalent_network_height']=height
        proof['network_height']=plan['network_height'];proof['routing']=routing;proof['inference_plan']=plan
        proof['projected_glyph_height']=proof['glyph_height']*plan['network_height']/(plan.get('tile_height') or proof['image_size'][1])
        rows=segment(row['image'],cache_directory=out/'tile-cache',**plan)
        atomic_json(out/'segmentation.json',rows)
        atomic_json(out/'segmentation-ink.json',refine_lines(row['image'],rows))
        atomic_json(out/'parameters.json',dict(**proof,image_sha256=row['image_sha256'],criteria_met=False,
                    scope='image-only segmentation variant; full independent fixed-suite comparison still required'))
        print(json.dumps(dict(id=row['id'],lines=len(rows),network_height=plan['network_height'],strategy=plan['strategy'],criteria_met=False)),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('manifest');ap.add_argument('output')
    ap.add_argument('--split',choices=('dev','reserved'),required=True);ap.add_argument('--family')
    ap.add_argument('--routing',choices=('full','bounded'),default='full')
    a=ap.parse_args();run(a.manifest,a.output,a.split,a.family,a.routing)
