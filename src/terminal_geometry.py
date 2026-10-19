"""Essai source-only de ponctuation terminale exclue du rectangle du mot.

Seuls les intervalles CTC nuls déclenchent la recherche. Le texte ne change
jamais. Un signe absent/ambigu n'est pas remplacé par une largeur arbitraire.
Les rectangles et intervalles précédents restent dans la provenance.
"""
from __future__ import annotations
from copy import deepcopy
import math
import re
import cv2
import numpy as np


def repair(gray,annotations,hyphen_min_aspect=2.5):
    if gray is None or gray.ndim!=2 or gray.dtype!=np.uint8:
        raise ValueError('Image native uint8 requise')
    if not math.isfinite(hyphen_min_aspect) or hyphen_min_aspect<1.4:
        raise ValueError('Proportion horizontale expérimentale invalide')
    # Ne pas binariser le mot tronqué d'abord : une composante touchant son
    # bord pourrait être un fragment de ponctuation accepté à tort comme entier.
    rows=deepcopy(annotations);decisions=[];height,width=gray.shape
    for a in rows:
        text=a['text'];chars=a.get('chars') or [];words=a.get('words') or []
        tokens=list(re.finditer(r'\S+',text))
        if len(chars)!=len(text) or len(tokens)!=len(words):continue
        for wi,(token,word) in enumerate(zip(tokens,words)):
            i=token.end()-1;sign=text[i]
            if chars[i][1]>chars[i][0]:continue
            original_box=[word['x0'],word['y0'],word['x1']+1,word['y1']+1]
            h=original_box[3]-original_box[1]
            raw=sign
            if i==len(text)-1 and a.get('linebreak',{}):raw=a['linebreak']['raw']
            decision=dict(line_id=a['id'],index=i,char=sign,raw_terminal=raw,previous=deepcopy(chars[i]),
                          previous_word_bbox=original_box,accepted=False)
            if sign not in ',.-' or i==token.start() or token.group()!=word['text']:
                decision['reason']='unsupported_terminal_or_word_correspondence';decisions.append(decision);continue
            if sign=='-' and raw not in ('-','='):
                decision['reason']='unsupported_native_hyphen_shape';decisions.append(decision);continue
            source=a.get('reading_bbox',a['bbox'])
            max_gap=.8*h if sign=='-' else .4*h
            left=max(0,math.floor(chars[i-1][1]-.4*h))
            right=min(width,words[wi+1]['x0'] if wi+1<len(words) else width,
                      math.ceil(original_box[2]+max_gap+h))
            top=max(0,math.floor(source[1]));bottom=min(height,math.ceil(source[3]+h*.25))
            if right-left<3 or bottom-top<3:
                decision['reason']='native_search_empty';decisions.append(decision);continue
            crop=gray[top:bottom,left:right]
            window=max(15,int(h*.75)|1)
            mask=cv2.adaptiveThreshold(crop,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV,window,12)
            _,_,stats,_=cv2.connectedComponentsWithStats(mask,8)
            candidates=[]
            for x,y,w,ch,area in stats[1:]:
                bb=[int(x+left),int(y+top),int(x+w+left),int(y+ch+top)]
                if area<3 or bb[0]<chars[i-1][1] or bb[0]-original_box[2]>max_gap:continue
                if x==0 or y==0 or x+w==crop.shape[1] or y+ch==crop.shape[0]:continue
                if sign=='-':
                    valid=w>=hyphen_min_aspect*ch and ch<=.35*h and w<=1.2*h and abs((bb[1]+bb[3])/2-(original_box[1]+original_box[3])/2)<=.3*h
                else:
                    valid=ch<=.4*h and w<=.35*h and original_box[3]-.2*h<=bb[3]<=original_box[3]+.25*h
                if valid:candidates.append(dict(bbox=bb,area=int(area)))
            candidates.sort(key=lambda c:(-c['area'],c['bbox'][0]))
            decision.update(search_bbox=[left,top,right,bottom],candidates=candidates)
            chosen=[]
            if sign=='-' and raw=='=':
                pairs=[]
                for ci,c in enumerate(candidates):
                    for d in candidates[ci+1:]:
                        cb,db=c['bbox'],d['bbox']
                        overlap=max(0,min(cb[2],db[2])-max(cb[0],db[0]))/min(cb[2]-cb[0],db[2]-db[0])
                        gap=max(0,cb[1]-db[3],db[1]-cb[3])
                        if overlap>=.8 and gap<=.3*h:pairs.append([c,d])
                if len(pairs)==1:chosen=pairs[0]
            elif candidates and candidates[0]['area']/sum(c['area'] for c in candidates)>=.85:
                chosen=[candidates[0]]
            if not chosen:
                decision['reason']='native_terminal_missing_or_ambiguous';decisions.append(decision);continue
            bb=[min(c['bbox'][0] for c in chosen),min(c['bbox'][1] for c in chosen),
                max(c['bbox'][2] for c in chosen),max(c['bbox'][3] for c in chosen)]
            extended=[min(original_box[0],bb[0]),min(original_box[1],bb[1]),
                      max(original_box[2],bb[2]),max(original_box[3],bb[3])]
            # Préserver un intervalle de blanc positif vers le mot suivant.
            if wi+1<len(words) and extended[2]>=words[wi+1]['x0']:
                decision['reason']='no_native_gap_to_next_word';decisions.append(decision);continue
            word.update(x0=extended[0],y0=extended[1],x1=extended[2]-1,y1=extended[3]-1)
            chars[i]=[float(bb[0]),float(bb[2]),0.]
            previous_gaps=[]
            if wi+1<len(words):
                for index in range(token.end(),tokens[wi+1].start()):
                    previous_gaps.append(dict(index=index,position=deepcopy(chars[index])))
                    chars[index]=[float(extended[2]),float(words[wi+1]['x0']),0.]
            old_line=deepcopy(a['bbox'])
            a['bbox']=[min(old_line[0],extended[0]),min(old_line[1],extended[1]),
                       max(old_line[2],extended[2]),max(old_line[3],extended[3])]
            decision.update(accepted=True,position=deepcopy(chars[i]),native_bbox=bb,
                            native_components=chosen,word_bbox=extended,previous_line_bbox=old_line,
                            line_bbox=deepcopy(a['bbox']),previous_gaps=previous_gaps,
                            reason='isolated_native_terminal_ink',position_confidence='unknown',
                            source='native image components; previous forced alignment preserved')
            a.setdefault('character_position_repairs',[]).append(deepcopy(decision))
            a['alignment']=a.get('alignment') or {}
            sources=a['alignment'].setdefault('character_position_sources',['unspecified']*len(chars))
            if len(sources)!=len(chars):raise ValueError('Sources de caractères incohérentes')
            sources[i]='native_terminal_extension; ctc_support_unknown'
            a['alignment'].setdefault('native_terminal_word_extensions',[]).append(deepcopy(decision))
            decisions.append(decision)
    unresolved=[dict(line_id=a['id'],index=i,char=ch,position=a['chars'][i]) for a in rows
                if len(a.get('chars') or [])==len(a['text']) for i,ch in enumerate(a['text'])
                if not ch.isspace() and a['chars'][i][1]<=a['chars'][i][0]]
    return dict(annotations=rows,decisions=decisions,unresolved=unresolved,hyphen_min_aspect=hyphen_min_aspect,promoted=False,criteria_met=False,
                scope='experimental source-only terminal native-ink extension; all IDs/text retained; glyph fidelity/whole-page collisions/reader compatibility still require independent checks')
