#!/usr/bin/env python
"""Comparaison isolée de cellules CTC dans des mots automatiques FIXES.

Sélection : tous les mots retenus défectueux, plus un contrôle régulier parmi
les autres. Aucun texte ou position de référence ; aucune modification du boxer.
"""
from contextlib import nullcontext
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
import argparse
import hashlib
import json
import re
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'src/boxers')]
import numpy as np
from PIL import Image
import torch
import forcectc
from native_frame_ctc import source_frame_alignment


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(text,positions,crop,alignment):
    width=alignment['input_width'];frames=alignment['frames'];padding=alignment['padding']
    frame_width=width/frames*(crop[2]-crop[0])/(width-2*padding)
    counts=Counter();issues=[];previous_end=None
    for index,(char,(left,right,confidence)) in enumerate(zip(text,positions)):
        reasons=[]
        if right<=left:reasons.append('nonpositive_width')
        if left<crop[0] or right>crop[2]:reasons.append('outside_source_crop')
        if previous_end is not None and left<previous_end-1e-8:reasons.append('overlap')
        if right>left and right-left<frame_width-1e-6 and (abs(left-crop[0])<1e-6 or abs(right-crop[2])<1e-6):
            reasons.append('partially_native_cell')
        for reason in reasons:counts[reason]+=1
        if reasons:issues.append(dict(index=index,char=char,reasons=reasons))
        previous_end=right
    return dict(issues=issues,issue_counts=dict(counts),frame_width=frame_width,
                coordinate_consistent=not issues,glyph_geometry_certified=False)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('image');ap.add_argument('annotations');ap.add_argument('output')
    args=ap.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    torch.set_num_threads(2);torch.set_num_interop_threads(2)
    rows=json.loads(Path(args.annotations).read_text())
    with Image.open(args.image) as image:gray=np.asarray(image.convert('L'))
    all_words=[]
    for row in rows:
        if not row.get('alto_eligible'):continue
        details=(row.get('alignment') or {}).get('word_alignments',[])
        words=list(re.finditer(r'\S+',row['text']))
        if len(words)!=len(details):raise ValueError('Annotation sans positions forcées par mot')
        for wi,(word,detail) in enumerate(zip(words,details)):
            positions=row['chars'][word.start():word.end()]
            measured=audit(word.group(),positions,detail['source_box'],detail['alignment'])
            all_words.append(dict(line_id=row['id'],word_index=wi,text=word.group(),
                source_box=detail['source_box'],model_path=detail['alignment']['model_path'],
                original_positions=positions,original_audit=measured))
    candidates=[{**w,'selection':'all_defective_words' if not w['original_audit']['coordinate_consistent'] else 'regular_control'}
                for i,w in enumerate(all_words) if not w['original_audit']['coordinate_consistent'] or i%37==0]
    models={};records=[];start=time.time()
    manifest=dict(image=str(Path(args.image).resolve()),image_sha256=digest(args.image),
        annotations=str(Path(args.annotations).resolve()),annotations_sha256=digest(args.annotations),
        implementation={str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),ROOT/'src/native_frame_ctc.py',ROOT/'src/boxers/forcectc.py']},
        source_words=len(all_words),selected_words=len(candidates),production_promoted=False,
        glyph_geometry_certified=False,selection_policy='all defective retained words + every 37th retained word control',
        model_sha256={w['model_path']:digest(w['model_path']) for w in candidates})
    (out/'selection.json').write_text(json.dumps(dict(manifest=manifest,words=candidates),ensure_ascii=False,indent=2))
    for number,word in enumerate(candidates,1):
        crop=word['source_box'];record={**word,'variants':{}}
        for policy in ['unmasked','intersects','center','contained']:
            boxer=forcectc.ForceCTC(word['model_path'])
            if word['model_path'] in models:boxer._model=models[word['model_path']]
            context=nullcontext([]) if policy=='unmasked' else source_frame_alignment(forcectc,policy)
            try:
                with context as mask_audit:
                    boxer.align(gray,SimpleNamespace(text=word['text'],line_box=crop))
                record['variants'][policy]=dict(status='aligned',positions=boxer.last_char_positions,
                    alignment=boxer.last_alignment,mask_audit=mask_audit,
                    audit=audit(word['text'],boxer.last_char_positions,crop,boxer.last_alignment))
                models[word['model_path']]=boxer._model
            except (ValueError,RuntimeError) as exc:
                record['variants'][policy]=dict(status='refused',reason=str(exc))
        records.append(record)
        (out/f'word-{number:03d}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))
    summary={}
    for policy in ['unmasked','intersects','center','contained']:
        counts=Counter();aligned=consistent=0
        for record in records:
            value=record['variants'][policy]
            if value['status']=='aligned':
                aligned+=1;counts.update(value['audit']['issue_counts'])
                consistent+=value['audit']['coordinate_consistent']
        summary[policy]=dict(selected=len(records),aligned=aligned,refused=len(records)-aligned,
                             coordinate_consistent=consistent,issue_counts=dict(counts),
                             glyph_geometry_certified=False)
    if any(digest(ROOT/key)!=value for key,value in manifest['implementation'].items()):
        raise RuntimeError('Implémentation modifiée pendant la comparaison')
    result=dict(manifest=manifest,seconds=time.time()-start,summary=summary,production_promoted=False)
    (out/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
