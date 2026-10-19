#!/usr/bin/env python
"""Rejeu isolé des positions de ponctuation, aucune entrée de référence."""
import argparse
import json
from pathlib import Path
import sys
import cv2
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from char_geometry import repair_terminal

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('image');ap.add_argument('annotations');ap.add_argument('output');a=ap.parse_args()
    result=repair_terminal(cv2.imread(a.image,0),json.loads(Path(a.annotations).read_text()))
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(dict(repaired=sum(d['accepted'] for d in result['decisions']),unresolved=len(result['unresolved']),criteria_met=False)))
