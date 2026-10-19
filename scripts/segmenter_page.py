#!/usr/bin/env python
"""Segmentation automatique reprenable d'une image, sans référence."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from page_anchors import load_automatic_lines,save_json,sha256
from segmentation import segment,refine_lines


def run(image,output):
    image=Path(image).resolve();output=Path(output)
    config=dict(version='blla-rectangles-v1',image_sha256=sha256(image),strategy='auto',
                line_refinement='ink',implementation_sha256=sha256(ROOT/'src/segmentation.py'))
    target=output/'segmentation-config.json'
    if target.exists() and json.loads(target.read_text())!=config:
        raise ValueError('Configuration de segmentation modifiée ; nouveau dossier requis')
    save_json(target,config)
    if (output/'segmentation.json').exists():return load_automatic_lines(image,output)
    rows=segment(image,strategy='auto',cache_directory=output/'segmentation-tiles')
    save_json(output/'segmentation.json',refine_lines(image,rows))
    return load_automatic_lines(image,output)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image');parser.add_argument('output');args=parser.parse_args()
    print(json.dumps(dict(lines=len(run(args.image,args.output)))))
