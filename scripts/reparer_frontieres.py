#!/usr/bin/env python
"""Reprendre seulement les frontières CTC refusées, depuis leurs caches."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import cv2
from page_anchors import save_json,sha256
from page_geometry import _place
from page_owned_line_mask import OwnedLineBoxer
from boxers.forcectc import ForceCTC


def run(image,source,output,limit=None):
    source=Path(source);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    config=dict(image_sha256=sha256(image),
                implementation_sha256=sha256(ROOT/'src/page_owned_line_mask.py'),
                source=str(source.resolve()),
                source_config_sha256=sha256(source/'page-pipeline-config.json'),
                algorithms={name:sha256(ROOT/'src'/name) for name in
                            ('page_geometry.py','boxers/forcectc.py','ink.py','correct.py','page_word_ownership.py')})
    cp=output/'config.json'
    if cp.exists() and json.loads(cp.read_text())!=config:raise ValueError('Configuration différente')
    save_json(cp,config)
    rows=[]
    for path in (source/'geometry-cache').glob('*.json'):
        if path.name=='state.json':continue
        value=json.loads(path.read_text())
        if 'annotation' in value:rows.append(value['annotation'])
    rows.sort(key=lambda r:r['id'])
    if len({r['id'] for r in rows})!=len(rows):raise ValueError('Cache contient plusieurs variantes par ligne')
    gray=cv2.imread(str(image),0)
    boxer=OwnedLineBoxer(gray,rows,ForceCTC(boundary_mode='ink_clean_local',char_alignment='word'))
    attempted=0;recovered=0;result=[]
    for row in rows:
        if row['status']=='alignement_non_resolu' and row.get('reason')=='frontière de mots sans séparation d’encre observée' and (limit is None or attempted<limit):
            attempted+=1;target=output/'lines'/(row['id']+'.json')
            if target.exists():new=json.loads(target.read_text())
            else:
                new=deepcopy(row);new['previous_geometry_failure']=new.pop('reason')
                boxer.current=new;_place(gray,new,boxer)
                save_json(target,new)
            if new['status']=='placee':
                recovered+=1;row=new
            print(json.dumps(dict(line=row['id'],attempted=attempted,recovered=recovered,status=new['status'])),flush=True)
        result.append(row)
    save_json(output/'annotations.json',result)
    report=dict(attempted=attempted,recovered=recovered,remaining=attempted-recovered,
                text_changed=False,source_image_changed=False)
    save_json(output/'report.json',report)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('image');p.add_argument('source');p.add_argument('output');p.add_argument('--limit',type=int)
    a=p.parse_args();print(json.dumps(run(a.image,a.source,a.output,a.limit)))
