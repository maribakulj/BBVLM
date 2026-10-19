#!/usr/bin/env python
"""Rejeu isolé de l'encre terminale, sans référence ni modification du source."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import cv2
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from terminal_geometry import repair

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('image');ap.add_argument('annotations');ap.add_argument('output')
    ap.add_argument('--hyphen-min-aspect',type=float,default=2.5);args=ap.parse_args()
    source=Path(args.annotations);annotations=json.loads(source.read_text())
    result=repair(cv2.imread(args.image,0),annotations,args.hyphen_min_aspect)
    result.update(image_sha256=hashlib.sha256(Path(args.image).read_bytes()).hexdigest(),
                  input_annotations_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  implementation_sha256=hashlib.sha256((ROOT/'src/terminal_geometry.py').read_bytes()).hexdigest())
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(dict(repaired=sum(d['accepted'] for d in result['decisions']),remaining_zero_intervals=len(result['unresolved']),criteria_met=False)))
