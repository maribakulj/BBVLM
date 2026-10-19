"""Réparation expérimentale d'ancres ponctuelles hors encre, sans référence.

Une composante native dominante peut remplacer un intervalle CTC nul de
ponctuation terminale. Sa probabilité d'alignement n'est pas une confiance de
géométrie : la nouvelle position porte confiance inconnue0 et sa provenance.
"""
import copy
import re
import cv2
from ink import alignment_mask


def repair_terminal(gray,annotations):
    if gray is None or gray.ndim!=2:raise ValueError('image native en niveaux de gris requise')
    rows=copy.deepcopy(annotations);decisions=[]
    for a in rows:
        chars=a.get('chars',[])
        if len(chars)!=len(a['text']):
            decisions.append(dict(line_id=a['id'],accepted=False,reason='missing_or_inconsistent_character_positions'))
            continue
        for token,word in zip(re.finditer(r'\S+',a['text']),a.get('words',[])):
            i=token.end()-1
            if chars[i][1]>chars[i][0]:continue
            decision=dict(line_id=a['id'],index=i,char=a['text'][i],previous=chars[i],accepted=False)
            if token.group()!=word['text'] or a['text'][i] not in ',.' or i==token.start():
                decision['reason']='unsupported_terminal_or_word_correspondence';decisions.append(decision);continue
            box=[word['x0'],word['y0'],word['x1']+1,word['y1']+1]
            mask,ox,oy=alignment_mask(gray,box);height=box[3]-box[1]
            _,_,stats,_=cv2.connectedComponentsWithStats(mask,8)
            previous_center=(chars[i-1][0]+chars[i-1][1])/2
            candidates=[dict(bbox=[int(x+ox),int(y+oy),int(x+w+ox),int(y+h+oy)],area=int(area))
                        for x,y,w,h,area in stats[1:]
                        if x+ox>previous_center and h<=.4*height and w<=.35*height and area>=3
                        and y+h+oy>=box[3]-.2*height]
            candidates.sort(key=lambda c:c['area'],reverse=True)
            decision['candidates']=candidates
            if not candidates or candidates[0]['area']/sum(c['area'] for c in candidates)<.85:
                decision['reason']='native_component_missing_or_ambiguous';decisions.append(decision);continue
            chosen=candidates[0];left,top,right,bottom=chosen['bbox']
            if left<chars[i-1][1] or right>box[2]:
                decision['reason']='component_incompatible_with_neighbor_position';decisions.append(decision);continue
            chars[i]=[float(left),float(right),0.]
            decision.update(accepted=True,position=chars[i],native_bbox=chosen['bbox'],
                            reason='dominant_native_terminal_component',position_confidence='unknown',
                            source='image_connected_component; original forced-CTC anchor retained in previous')
            a.setdefault('character_position_repairs',[]).append(copy.deepcopy(decision))
            alignment=a['alignment']=a.get('alignment') or {}
            sources=alignment.setdefault('character_position_sources',['unspecified']*len(chars))
            if len(sources)!=len(chars):raise ValueError('provenance de caractères incohérente : '+a['id'])
            sources[i]='native_terminal_component; ctc_support_unknown'
            decisions.append(decision)
    unresolved=[dict(line_id=a['id'],index=i,char=ch,position=a['chars'][i]) for a in rows
                for i,ch in enumerate(a['text']) if not ch.isspace() and len(a.get('chars') or [])==len(a['text']) and a['chars'][i][1]<=a['chars'][i][0]]
    unresolved.extend(dict(line_id=a['id'],reason='missing_or_inconsistent_character_positions') for a in rows
                      if len(a.get('chars') or [])!=len(a['text']))
    return dict(annotations=rows,decisions=decisions,unresolved=unresolved,criteria_met=False,
                scope='experimental image-only terminal position repair; text and word boxes unchanged; independent glyph validation absent')
