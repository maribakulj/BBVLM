"""Diagnostic conservateur de fragments détectés deux fois, sans référence.

Texte Gemini, ancres CTC et encre native doivent corroborer la copie physique.
Le diagnostic ne modifie ni transcription, ni boîte, ni éligibilité ; toute
application reste un essai séparé qui conserve les IDs et décisions d'origine.
"""
import copy
import re
import cv2
import numpy as np
from ink import alignment_mask


def detect(gray,annotations,mask_source='local_clean'):
    if gray is None:raise ValueError('image native requise')
    if mask_source not in ('local_clean','global_source'):raise ValueError('source de masque inconnue')
    masks={};valid=[a for a in annotations if a.get('words') and not a.get('uncertain')
                   and len(a.get('chars') or [])==len(a['text'])]
    global_mask=None;window=None
    if mask_source=='global_source' and valid:
        heights=[a.get('reading_bbox',a['bbox'])[3]-a.get('reading_bbox',a['bbox'])[1] for a in valid]
        window=max(15,int(np.median(heights)*.75)|1)
        global_mask=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY_INV,window,12)>0
    def priority(a):
        b=a.get('reading_bbox',a['bbox'])
        return len(a['text'].strip()),b[2]-b[0],a['id']
    def mask(a):
        if a['id'] not in masks:
            if global_mask is None:
                pixels,ox,oy=alignment_mask(gray,a.get('reading_bbox',a['bbox']),
                                           clean_upper_branches=True,clean_below_baseline=True)
            else:
                ox,oy,x1,y1=a.get('reading_bbox',a['bbox']);pixels=global_mask[oy:y1,ox:x1]
            cells=np.zeros_like(pixels)
            for w in a['words']:
                left,top=max(0,w['x0']-ox),max(0,w['y0']-oy)
                right,bottom=min(pixels.shape[1],w['x1']+1-ox),min(pixels.shape[0],w['y1']+1-oy)
                if left<right and top<bottom:cells[top:bottom,left:right]=255
            masks[a['id']]=(pixels.astype(bool)&cells.astype(bool),ox,oy,pixels.astype(bool))
        return masks[a['id']]
    decisions=[]
    for child in sorted(valid,key=priority):
        text=child['text'];cbox=child.get('reading_bbox',child['bbox']);height=cbox[3]-cbox[1]
        candidates=[]
        for parent in valid:
            if priority(parent)<=priority(child):continue
            pbox=parent.get('reading_bbox',parent['bbox']);h=min(height,pbox[3]-pbox[1])
            if abs((cbox[1]+cbox[3]-pbox[1]-pbox[3])/2)>.35*h:continue
            if min(cbox[2],pbox[2])<=max(cbox[0],pbox[0]):continue
            for match in re.finditer(re.escape(text),parent['text']):
                distances=[abs(sum(child['chars'][i][:2])/2-sum(parent['chars'][j][:2])/2)
                           for i,j in enumerate(range(match.start(),match.end())) if not text[i].isspace()]
                if not distances or max(distances)>max(2,.18*h):continue
                cm,cx,cy,_=mask(child);pm,px,py,raw_parent=mask(parent);n=int(np.count_nonzero(cm))
                if global_mask is not None:
                    # Une boîte de mot ancienne peut perdre le point d'un i.
                    # Identifier son mot via le texte/CTC, garder son étendue x
                    # observée et le y de la ligne source ; l'encre du fragment
                    # devra ensuite être conservée par une expansion native.
                    target_words=[w for token,w in zip(re.finditer(r'\S+',parent['text']),parent['words'])
                                  if token.start()<match.end() and token.end()>match.start()]
                    support=np.zeros_like(pm)
                    for w in target_words:
                        left,right=max(0,w['x0']-px),min(pm.shape[1],w['x1']+1-px)
                        if left<right:support[:,left:right]=True
                    pm=raw_parent&support
                if n<8:continue
                x0,y0=max(cx,px),max(cy,py);x1,y1=min(cx+cm.shape[1],px+pm.shape[1]),min(cy+cm.shape[0],py+pm.shape[0])
                if x0>=x1 or y0>=y1:continue
                shared=int(np.count_nonzero(cm[y0-cy:y1-cy,x0-cx:x1-cx]&pm[y0-py:y1-py,x0-px:x1-px]))
                fraction=shared/n
                if fraction<.98:continue
                candidates.append(dict(parent_id=parent['id'],parent_text_offset=[match.start(),match.end()],
                    max_ctc_center_distance=max(distances),native_pixels=n,shared_native_pixels=shared,
                    native_shared_fraction=fraction,parent_priority=priority(parent)))
        if candidates:
            chosen=max(candidates,key=lambda c:(c['parent_priority'],c['native_shared_fraction'],-c['max_ctc_center_distance']))
            decisions.append(dict(child_id=child['id'],**chosen,
                reason='production substring + compatible CTC anchors + >=98% same native word-mask pixels'))
    aliases={d['child_id']:d['parent_id'] for d in decisions}
    offsets={d['child_id']:d['parent_text_offset'][0] for d in decisions}
    for decision in decisions:
        canonical=decision['parent_id'];path=[canonical];start=decision['parent_text_offset'][0]
        while canonical in aliases:
            start+=offsets[canonical]
            canonical=aliases[canonical]
            if canonical in path:raise ValueError('cycle de copies physiques')
            path.append(canonical)
        decision['canonical_id']=canonical;decision['alias_path']=path
        decision['canonical_text_offset']=[start,start+len(next(a['text'] for a in valid if a['id']==decision['child_id']))]
    return dict(decisions=decisions,annotations=copy.deepcopy(annotations),criteria_met=False,
                mask_source=mask_source,global_window=window,
                scope='experimental production-evidence duplicate diagnostic; every original ID/text/box retained')


def conserve_fragment_ink(result):
    """Union de boîtes natives connues ; jamais retrait d'encre ni texte changé."""
    rows=result['annotations'];by={a['id']:a for a in rows};repairs=[]
    for d in result['decisions']:
        child,parent=by[d['child_id']],by[d['canonical_id']]
        start=d['canonical_text_offset'][0]
        if parent['text'][start:d['canonical_text_offset'][1]]!=child['text']:
            raise ValueError('Correspondance canonique de texte incohérente')
        tokens=list(re.finditer(r'\S+',parent['text']))
        for token,word in zip(re.finditer(r'\S+',child['text']),child['words']):
            first,last=start+token.start(),start+token.end()
            matches=[i for i,t in enumerate(tokens) if t.start()<=first and t.end()>=last]
            if len(matches)!=1:raise ValueError('Fragment sans mot canonique unique')
            canonical=parent['words'][matches[0]];before=[canonical[k] for k in ('x0','y0','x1','y1')]
            box=[min(before[0],word['x0']),min(before[1],word['y0']),
                 max(before[2],word['x1']),max(before[3],word['y1'])]
            if box!=before:
                canonical.update(zip(('x0','y0','x1','y1'),box))
                repair=dict(child_id=child['id'],canonical_id=parent['id'],word_index=matches[0],before=before,after=box,
                            reason='conserve native fragment ink in its canonical word; inclusive pixels')
                repairs.append(repair);parent.setdefault('duplicate_ink_repairs',[]).append(repair)
        b=parent['bbox'];words=parent['words']
        parent['bbox']=[min(b[0],min(w['x0'] for w in words)),min(b[1],min(w['y0'] for w in words)),
                        max(b[2],max(w['x1'] for w in words)+1),max(b[3],max(w['y1'] for w in words)+1)]
    result['ink_conservation_repairs']=repairs
    return result
