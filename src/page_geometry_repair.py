"""Réparer les enveloppes et conserver les mots sûrs des lignes partielles."""
from copy import deepcopy
from collections import Counter
import json
from pathlib import Path
import re

import cv2

from page_anchors import save_json, sha256
from page_text_view import compact_line_text_view
from page_word_ownership import refine, VERSION


def _independent_reading_agreement(row):
    """Ressemblance entre le texte imposé et la lecture CTC indépendante."""
    from rapidfuzz.distance import Levenshtein
    from page_alignment import _search_text
    imposed=_search_text(row.get('text',''))[0];reading=_search_text(row.get('auxiliary_text') or '')[0]
    if not imposed or not reading:return 0.
    return Levenshtein.normalized_similarity(imposed,reading)


def repair(image, directory,contrast='adaptive'):
    directory=Path(directory)
    annotations=json.loads((directory/'annotations.json').read_text())
    alignment=json.loads((directory/'page-alignment.json').read_text())
    geometry=json.loads((directory/'geometry-report.json').read_text())
    originals={a['line_id']:a for a in alignment['assignments']}
    rows,audit=refine(cv2.imread(str(image),cv2.IMREAD_GRAYSCALE),annotations,contrast=contrast)
    bad=set()
    for pair in audit['conflicts']:
        bad.add(tuple(pair['first']));bad.add(tuple(pair['second']))
    for row in rows:
        for wi,word in enumerate(row.get('words',[])):
            if word.get('ownership_status')!='observed':bad.add((row['id'],wi))
    result=[];assignments=[];replacements={};word_ids={};excluded=[]
    for row in rows:
        lid=row['id'];words=row.get('words',[]);original=originals.get(lid)
        if not words or original is None or not row.get('assignment_resolved'):
            result.append(row)
            if original is not None:assignments.append(original)
            replacements[lid]=[lid]
            continue
        agreement=_independent_reading_agreement(row)
        if row.get('cout',float('inf'))>geometry['ink_suspicion_threshold'] and agreement>=.85:
            # Le coût compare l'encre à un gabarit de police rendu ; il échoue
            # sur l'italique, le gras d'affiche, les exposants. La lecture CTC
            # de la ligne, indépendante de Gemini, confirme ici le même texte.
            row['ink_cost_override']=dict(cost=row['cout'],threshold=geometry['ink_suspicion_threshold'],
                independent_ctc_similarity=round(agreement,4),minimum_similarity=.85)
        elif row.get('cout',float('inf'))>geometry['ink_suspicion_threshold']:
            row.update(status='ajustement_encre_suspect',alto_eligible=False,training_eligible=False)
            result.append(row);assignments.append(original);replacements[lid]=[lid]
            continue
        tokens=list(re.finditer(r'\S+',row['text']))
        if [t.group() for t in tokens]!=[w['text'] for w in words]:
            raise ValueError('Mots incohérents avant réparation')
        runs=[];start=None
        for wi in range(len(words)+1):
            keep=wi<len(words) and (lid,wi) not in bad
            if keep and start is None:start=wi
            if not keep and start is not None:runs.append((start,wi));start=None
        replacements[lid]=[]
        partial=len(runs)!=1 or runs[0]!=(0,len(words))
        if partial:
            excluded.extend(dict(line_id=lid,word_index=i,text=w['text'],reason='shared_or_unresolved_ink')
                            for i,w in enumerate(words) if (lid,i) in bad)
        if not runs:
            row.update(status='encre_mots_ambigue',alto_eligible=False,training_eligible=False)
            result.append(row)
        for index,(first,last) in enumerate(runs,1):
            rid=f'{lid}_G{index}' if partial else lid
            row_copy=deepcopy(row);matched=deepcopy(original)
            ca=tokens[first].start();cb=tokens[last-1].end()
            spans=row['source_spans'];sa=spans[ca][0];sb=spans[cb-1][1]
            if not partial:sa=0;sb=len(row['source_text']);ca=0;cb=len(row['text'])
            source=row['source_text'][sa:sb];view=compact_line_text_view(source)
            matched.update(line_id=rid,text=source,start=original['start']+sa,end=original['start']+sb)
            ws=deepcopy(words[first:last]);box=row['bbox']
            row_copy.update(id=rid,line_id=rid,source_line_id=lid,text=view['text'],source_text=source,
                            start=matched['start'],end=matched['end'],source_spans=view['source_spans'],
                            text_view_transform=view['transform'],words=ws,
                            status='retenue',geometry_status='retenue',geometry_valid=True,
                            alto_eligible=True,training_eligible=True,partial_source_line=partial)
            if partial:
                # Une sous-ligne ne prétend pas couvrir les mots retirés.
                box=[min(w['x0'] for w in ws),min(w['y0'] for w in ws),
                     max(w['x1']+1 for w in ws),max(w['y1']+1 for w in ws)]
                row_copy['bbox']=box;row_copy['baseline']=[];row_copy['polygon']=[]
                matched['bbox']=box;matched['baseline']=[];matched['polygon']=[]
                if row_copy.get('chars') is not None:row_copy['chars']=row_copy['chars'][ca:cb]
                details=row_copy.get('alignment') or {}
                if details.get('character_position_sources') is not None:
                    details['character_position_sources']=details['character_position_sources'][ca:cb]
                if row_copy.get('character_realignments'):
                    row_copy['character_realignments']=[
                        {**r,'start':r['start']-ca,'end':r['end']-ca,'word_index':r['word_index']-first}
                        for r in row_copy['character_realignments']
                        if r['start']>=ca and r['end']<=cb and first<=r['word_index']<last]
            for i in range(first,last):word_ids[(lid,i)]=f'{rid}_W{i-first+1:02d}'
            assignments.append(matched);result.append(row_copy);replacements[lid].append(rid)
    assignments.sort(key=lambda a:a['start'])
    segments=[];offset=0;plain=alignment['plain_text']
    for a in assignments:
        if a['start']<offset:raise ValueError('Tranches de transcription superposées')
        if a['start']>offset:
            s=plain[offset:a['start']];segments.append(dict(start=offset,end=a['start'],text=s,status='unmatched_text' if s.strip() else 'formatting_whitespace'))
        segments.append(dict(start=a['start'],end=a['end'],text=a['text'],status='matched',line_id=a['line_id']))
        offset=a['end']
    if offset<len(plain):
        s=plain[offset:];segments.append(dict(start=offset,end=len(plain),text=s,status='unmatched_text' if s.strip() else 'formatting_whitespace'))
    assert ''.join(s['text'] for s in segments)==plain
    alignment.update(assignments=assignments,segments=segments,reading_order=[a['line_id'] for a in assignments])
    count=sum(sum(not c.isspace() for c in a['text']) for a in assignments)
    alignment['text_coverage'].update(matched_nonspace_characters=count,fraction=count/alignment['text_coverage']['nonspace_characters'])
    for block in alignment['blocks']:
        block['line_ids']=[new for old in block['line_ids'] for new in replacements.get(old,[old])]
    permitted=[]
    for pair in audit['safe_overlaps']:
        a=word_ids.get(tuple(pair['first']));b=word_ids.get(tuple(pair['second']))
        if a and b:permitted.append([a,b])
    save_json(directory/'annotations.json',result)
    save_json(directory/'page-alignment.json',alignment)
    save_json(directory/'ownership-audit.json',{**audit,'excluded_words':excluded,
              'retained_words':len(word_ids),'original_word_proposals':sum(len(r.get('words',[])) for r in annotations),
              'source_text_unchanged':True,'repair_version':VERSION})
    save_json(directory/'ownership-overlap-permissions.json',dict(image_sha256=sha256(image),
              annotations_sha256=sha256(directory/'annotations.json'),basis='zero_shared_owned_ink_pixels',pairs=permitted))
    geometry.update(ownership_repair=True,original_statuses=geometry.get('original_statuses',geometry['statuses']),
                    statuses=dict(Counter(r['status'] for r in result)),
                    original_lines=len(annotations), lines_total=len(result),
                    lines_exported=sum(r.get('alto_eligible',False) for r in result),
                    retained_words_after_ownership=len(word_ids),excluded_ambiguous_words=len(excluded),
                    exported_fragments=sum(r.get('alto_eligible',False) for r in result))
    geometry['coverage']=geometry['lines_exported']/len(result) if result else 0
    save_json(directory/'geometry-report.json',geometry)
    return alignment,result
