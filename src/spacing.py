"""Diagnostic d'espacement depuis l'encre et les pics CTC de production.

Ne reçoit aucune référence. Le texte proposé doit être réaligné avant export.
Les incertitudes restent explicites ; ce module n'est pas une certification.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import cv2
from ink import alignment_mask


def white_gap(occupied, a, b):
    a=max(0,int(np.ceil(a)));b=min(len(occupied),int(np.floor(b))+1)
    if b<=a:return 0
    best=run=0
    for value in occupied[a:b]:
        run=0 if value else run+1
        best=max(best,run)
    return best


def propose(gray, annotation):
    text=annotation['text'];chars=annotation.get('chars') or []
    result=dict(id=annotation['id'],text=text,original_text=text,bbox=annotation['bbox'],
                provider=annotation.get('provider','gemini'),model=annotation.get('model','unknown'),
                uncertain=annotation.get('uncertain',False),edits=[],status='diagnostic_only')
    if len(chars)!=len(text):
        return {**result,'reason':'no_matching_ctc_positions'}
    box=annotation.get('reading_bbox',annotation['bbox'])
    mask,ox,_=alignment_mask(gray,box)
    occupied=(mask>0).any(axis=0)
    indexes=[i for i,c in enumerate(text) if not c.isspace()]
    gaps=[]
    for i,j in zip(indexes,indexes[1:]):
        left=(chars[i][0]+chars[i][1])/2-ox
        right=(chars[j][0]+chars[j][1])/2-ox
        gaps.append(dict(left=i,right=j,width=white_gap(occupied,left,right),
                         present=bool(text[i+1:j]),support=min(chars[i][2],chars[j][2])))
    anchors=[g['width'] for g in gaps if g['support']>=.05 and g['present'] and
             text[g['left']].isalpha() and text[g['right']].isalpha()]
    within=[g['width'] for g in gaps if g['support']>=.05 and not g['present'] and
             text[g['left']].isalpha() and text[g['right']].isalpha()]
    if len(anchors)<2 or len(within)<8:
        return {**result,'reason':'insufficient_ink_gaps'}
    # Les blancs déjà lus servent d'ancres internes ; on ne suppose pas que
    # les deux groupes de tous les blancs séparent lettres et mots. Cette
    # supposition confondait les blancs internes des glyphes avec les espaces.
    low=float(np.percentile(within,80));high=float(np.median(anchors))
    threshold=(low+high)/2
    result['gap_model']=dict(intrachar_center=float(low),wordspace_center=float(high),threshold=threshold)
    result['gaps']=gaps
    result['version']='ctc-ink-spacing-v2'
    if high<max(6,1.5*low):return {**result,'reason':'spacing_clusters_overlap'}
    edits=[]
    for g in gaps:
        i,j=g['left'],g['right'];present=g['present'];width=g['width']
        if g['support']<.05:continue
        # Marges autour du seuil : aucune décision sur les blancs ambigus.
        if present and text[j] in ',.' and width < threshold*.8:
            edits.append(dict(start=i+1,end=j,replacement='',reason='punctuation_gap_like_intraword',pixels=width))
        elif not present and text[i].isalpha() and text[j].isalpha() and width>threshold*1.25:
            edits.append(dict(start=j,end=j,replacement=' ',reason='letter_gap_like_wordspace',pixels=width))
    proposal=text
    for edit in reversed(edits):
        proposal=proposal[:edit['start']]+edit['replacement']+proposal[edit['end']:]
    result.update(text=proposal,edits=edits,reason='image_only_spacing_proposal')
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('image');ap.add_argument('annotations');ap.add_argument('output');args=ap.parse_args()
    gray=cv2.imread(args.image,cv2.IMREAD_GRAYSCALE)
    if gray is None:raise ValueError('image illisible')
    data=[propose(gray,a) for a in json.loads(Path(args.annotations).read_text())]
    Path(args.output).write_text(json.dumps(data,ensure_ascii=False,indent=2))
    print(json.dumps(dict(lines=len(data),changed=sum(bool(a['edits']) for a in data),edits=sum(len(a['edits']) for a in data),
                         scope='diagnostic proposals; realignment and independent scoring required')))
