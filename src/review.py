"""Relecture visuelle ciblée sur des pics CTC faibles, sans référence.

Les hypothèses sont des sorties Gemini de production. Le CTC signale des
zones à examiner ; il ne fournit jamais une transcription de remplacement.
Le résultat doit être réaligné avant export de positions ou de mots.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from lecture import HerdrGeminiReader,LineRequest,prepare_job,ResponseError


def targets(annotations,width,height,threshold=.05,include_punctuation=False):
    rows=[]
    for a in annotations:
        chars=a.get('chars') or [];text=a['text']
        if len(chars)!=len(text):continue
        box=a.get('reading_bbox',a['bbox']);h=box[3]-box[1]
        for i,(symbol,pos) in enumerate(zip(text,chars)):
            if symbol.isspace() or pos[2]>=threshold and not (include_punctuation and symbol in ',.;:!?=¬⸗-'):continue
            center=(pos[0]+pos[1])/2
            alignment=a.get('alignment') or {}
            if alignment.get('frames') and alignment['input_width']>2*alignment['padding']:
                step=alignment['input_width']/alignment['frames']*(box[2]-box[0])/(alignment['input_width']-2*alignment['padding'])
                if pos[1]-pos[0]>step*1.5:
                    # Le premier pic est celui du corps du caractère, plutôt
                    # que le milieu d'un diacritique forcé plus loin à droite.
                    center=pos[0]+step/2
            bbox=[max(0,int(center-h*.65)),max(0,int(box[1])),
                  min(width,int(center+h*.65)+1),min(height,int(box[3]))]
            if bbox[2]<=bbox[0] or bbox[3]<=bbox[1]:continue
            rows.append(dict(id=f'C_{a["id"]}_{i:04d}',line_id=a['id'],index=i,
                             current_symbol=symbol,production_hypothesis=text,bbox=bbox,
                             source_line_bbox=box,focus_x=center-bbox[0],ctc_support=pos[2]))
    return rows


class Reviewer(HerdrGeminiReader):
    def __init__(self,pane,directory,metadata,**kw):
        self.metadata={r['id']:r for r in metadata}
        signature=hashlib.sha256(json.dumps(metadata,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        super().__init__(pane,directory,revision='glyph-review-v2-blind-'+signature,**kw)

    def _prepare(self,image,requests,directory,scale):
        manifest,_=prepare_job(image,requests,directory,scale)
        contexts={};data=[]
        for row in manifest['lines']:
            spec=self.metadata[row['id']];lid=spec['line_id']
            if lid not in contexts:
                path=Path(directory)/f'context-{len(contexts)+1:04d}.png'
                image.crop(tuple(spec['source_line_bbox'])).save(path)
                contexts[lid]=str(path.resolve())
            context=spec['production_hypothesis'];i=spec['index']
            public={k:v for k,v in spec.items() if k not in {'current_symbol','production_hypothesis'}}
            data.append({**public,'masked_production_context':context[:i]+'□'+context[i+1:],
                         'crop':row['crop'],'context_image':contexts[lid]})
        source=Path(directory)/'production-targets.json'
        source.write_text(json.dumps(data,ensure_ascii=False,indent=2))
        prompt=(f'BBVLM relecture de glyphes, même chaîne de production, requête {manifest["job_id"]}. '
                f'Lis UNIQUEMENT {source.resolve()} et les images explicitement listées dans ce JSON. '
                'Le texte masked_production_context est une première lecture automatique Gemini '
                'dont la cible est cachée par □, pas une référence et pas une réponse à suivre. '
                'Le CTC signale seulement des '
                'zones visuelles faibles ; il ne fournit aucun caractère correct de substitution. '
                'Pour chaque ID, ouvre son crop natif. focus_x indique le x approximatif du '
                'caractère cible dans le recadrage, index sa position dans la ligne hypothétique. '
                'Lis le caractère IMPRIMÉ cible à partir des pixels, accents/tilde/macron, '
                's long, casse et ponctuation fidèles. Le contexte aide seulement à localiser '
                'le glyphe : aucune modernisation ou correction lexicale. '
                'Si la cible ne peut être identifiée sans ambiguïté, rends uncertain=true '
                'avec text_parts=["?"]. Aucune recherche, aucun autre fichier, '
                'aucun shell, code, référence, OCR externe ni écriture. '
                f'JSON indenté exclusivement : job_id="{manifest["job_id"]}", provider="gemini", '
                'model=nom utilisé, lines=[{id:ID,text_parts:[un seul caractère NFC],uncertain:bool}]. '
                'Une propriété par ligne, un ID par entrée. Aucun texte hors JSON.')
        (Path(directory)/'prompt.txt').write_text(prompt,encoding='utf-8')
        return manifest,prompt


def review(image,annotations,pane,directory,batch_size=8,include_punctuation=False):
    im=Image.open(image).convert('RGB');metadata=targets(annotations,im.width,im.height,include_punctuation=include_punctuation)
    reader=Reviewer(pane,directory,metadata)
    readings=[]
    for start in range(0,len(metadata),batch_size):
        batch=metadata[start:start+batch_size]
        readings.extend(reader.read_lines(im,[LineRequest(r['id'],tuple(r['bbox'])) for r in batch]))
    values={r.id:r for r in readings}
    edits={};unresolved=[]
    for target in metadata:
        value=values[target['id']]
        if len(value.text)!=1:
            raise ResponseError('Relecture cible doit rendre un caractère NFC unique')
        if value.uncertain:
            unresolved.append(target['id']);continue
        if value.text!=target['current_symbol']:
            edits.setdefault(target['line_id'],[]).append(dict(index=target['index'],
                 before=target['current_symbol'],after=value.text,provider=value.provider,model=value.model,
                 job_source='glyph-review',target_id=target['id']))
    rows=[];unresolved_lines={t['line_id'] for t in metadata if t['id'] in unresolved}
    for a in annotations:
        text=list(a['text'])
        for edit in edits.get(a['id'],[]):text[edit['index']]=edit['after']
        rows.append(dict(id=a['id'],text=''.join(text),original_text=a['text'],bbox=a['bbox'],
                         provider=a['provider'],model=a['model'],uncertain=a['uncertain'] or a['id'] in unresolved_lines,
                         review_edits=edits.get(a['id'],[]),status='requires_realignment'))
    return dict(lines=rows,targets=len(metadata),reviewed=len(readings),unresolved=unresolved,
                changes=sum(map(len,edits.values())),scope='production reading review; no geometry certified',
                jobs=reader.journal)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('image');ap.add_argument('annotations');ap.add_argument('output')
    ap.add_argument('--gemini-pane',required=True)
    ap.add_argument('--punctuation',action='store_true');args=ap.parse_args()
    output=Path(args.output)
    result=review(args.image,json.loads(Path(args.annotations).read_text()),args.gemini_pane,output.parent/'glyph-review-jobs',
                  include_punctuation=args.punctuation)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({k:result[k] for k in ('targets','reviewed','changes','unresolved','scope')}))
