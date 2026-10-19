"""Vérification visuelle aveugle des mots d'une ligne refusée par coût de police.

Le coût historique reste publié. Un refus n'est levé que par lecture de TOUS
les mots recadrés, cohérence géométrique et nouvel alignement forcé au mot.
Ni texte attendu ni référence n'est transmis au lecteur de vérification.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from PIL import Image
from lecture import HerdrGeminiReader,LineRequest,prepare_job


def restore_checked_annotations(annotations_file,checked):
    annotations_file=Path(annotations_file)
    current=hashlib.sha256(annotations_file.read_bytes()).hexdigest()
    if current==checked['input_annotations_sha256']:
        content=json.dumps(checked['annotations'],ensure_ascii=False,indent=2).encode()
        if hashlib.sha256(content).hexdigest()!=checked['output_annotations_sha256']:
            raise ValueError('Vérification de mots corrompue')
        tmp=annotations_file.with_suffix('.tmp');tmp.write_bytes(content);tmp.replace(annotations_file)
    elif current!=checked['output_annotations_sha256']:
        raise ValueError('Annotations modifiées après vérification de mots ; nouveau dossier requis')


class WordReader(HerdrGeminiReader):
    def _prepare(self,image,requests,directory,scale):
        manifest,_=prepare_job(image,requests,directory,scale,input_style='sheets')
        prompt=(f'BBVLM vérification visuelle aveugle, requête {manifest["job_id"]}. '
                f'Lis UNIQUEMENT {Path(directory).resolve() / "request.json"} et les images explicitement listées. '
                'Ouvre TOUTES les detail_sheets : chaque ID est un recadrage de mot à pixels natifs, '
                'éventuellement divisé en morceaux chevauchants portant leurs intervalles. '
                'Le fichier ne contient AUCUN texte attendu. Transcris exactement les glyphes visibles, '
                'casse, accents, ligatures, s long et ponctuation compris. Ne complète aucun mot tronqué, '
                'ne normalise aucun signe de césure et ne corrige pas la langue. '
                'uncertain=true si un bord coupe un glyphe, si le mot manque ou si un signe est ambigu. '
                'Aucune recherche, référence, autre fichier, code, shell ou écriture. '
                f'JSON indenté uniquement : job_id="{manifest["job_id"]}",provider="gemini",model=nom utilisé, '
                'lines=[{id:ID,text_parts:[segments de 16 caractères maximum],uncertain:bool}]. '
                'Une propriété/segment par ligne. Tous les IDs exactement une fois, aucun texte hors JSON.')
        (Path(directory)/'prompt.txt').write_text(prompt)
        return manifest,prompt


def geometry_support(annotation):
    words=annotation.get('words') or [];text=annotation['text'];alignment=annotation.get('alignment') or {}
    if alignment.get('character_scope')!='word':return False,'forced_word_alignment_required'
    if not words or [m.group() for m in re.finditer(r'\S+',text)]!=[w['text'] for w in words]:
        return False,'word_text_mismatch'
    if any(not b['ink_free'] for b in alignment.get('word_geometry',{}).get('boundaries',[])):
        return False,'boundary_cuts_ink'
    details=alignment.get('word_alignments') or []
    if len(details)!=len(words) or any(not math.isfinite(d['alignment']['support_min']) or
                                      d['alignment']['support_min']<=0 for d in details):
        return False,'missing_or_nonfinite_word_support'
    chars=annotation.get('chars') or []
    if len(chars)!=len(text):return False,'missing_character_positions'
    for m,w in zip(re.finditer(r'\S+',text),words):
        if any(not w['x0']<=chars[i][0]<=chars[i][1]<=w['x1']+1 for i in range(m.start(),m.end())):
            return False,'character_outside_native_word'
    return True,'geometry_supported; reading still to verify'


def verify(image,annotations,pane,directory,batch_size=16):
    targets=[a for a in annotations if a.get('status')=='ajustement_encre_suspect']
    metadata=[];results=[]
    for a in targets:
        supported,reason=geometry_support(a)
        if not supported:
            results.append(dict(line_id=a['id'],accepted=False,reason=reason));continue
        source=a.get('reading_bbox',a['bbox']);raw=a.get('raw_text',a['text']).split()
        if len(raw)!=len(a['words']):raise ValueError('Raw transcription incompatible with production words')
        for i,(w,expected) in enumerate(zip(a['words'],raw)):
            metadata.append(dict(id=f'W_{a["id"]}_{i:03d}',line_id=a['id'],index=i,expected=expected,
                                 bbox=[w['x0'],source[1],w['x1']+1,source[3]]))
    signature=hashlib.sha256(json.dumps(metadata,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    reader=WordReader(pane,directory,revision='blind-words-v1-'+signature,input_style='sheets')
    image=Image.open(image).convert('RGB');values={}
    for start in range(0,len(metadata),batch_size):
        batch=metadata[start:start+batch_size]
        values.update({r.id:r for r in reader.read_lines(image,[LineRequest(m['id'],tuple(m['bbox'])) for m in batch])})
    for a in targets:
        rows=[m for m in metadata if m['line_id']==a['id']]
        if not rows:continue
        evidence=[dict(id=m['id'],index=m['index'],expected_production_word=m['expected'],
                       observed=values[m['id']].text,uncertain=values[m['id']].uncertain,
                       provider=values[m['id']].provider,model=values[m['id']].model,
                       native_crop=m['bbox']) for m in rows]
        accepted=all(not e['uncertain'] and e['expected_production_word']==e['observed'] for e in evidence)
        results.append(dict(line_id=a['id'],accepted=accepted,reason='all_native_words_verified' if accepted else 'visual_word_disagreement',words=evidence))
    decisions={r['line_id']:r for r in results};output=[]
    for a in annotations:
        row=dict(a)
        if a['id'] in decisions:
            row['word_verification']=decisions[a['id']]
            if decisions[a['id']]['accepted']:
                row.update(training_eligible=True,status='retenue_verification_mots',previous_status=a['status'])
        output.append(row)
    return dict(annotations=output,decisions=results,jobs=reader.journal,
                scope='image-only intrinsic verification, no independent certificate',criteria_met=False)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('image');ap.add_argument('annotations');ap.add_argument('output')
    ap.add_argument('--gemini-pane',required=True);args=ap.parse_args();out=Path(args.output)
    result=verify(args.image,json.loads(Path(args.annotations).read_text()),args.gemini_pane,out.parent/'word-verification-jobs')
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(dict(targets=len(result['decisions']),accepted=sum(r['accepted'] for r in result['decisions']),criteria_met=False)))
