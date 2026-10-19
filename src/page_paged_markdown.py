"""Page entière → portions Markdown durables, indépendantes de la géométrie.

Une portion suivante ne fournit que la fin de la VT déjà reçue comme ancre.
Le marqueur de fin est une assertion de Gemini, jamais une mesure de couverture.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
import re
import uuid

from PIL import Image

from lecture import LineRequest, ReaderUnavailable, ResponseError
from native_page_history import conversation_hint
from page_native_markdown import NativeMarkdownReader


REVISION='whole-page-natural-paged-v3-6000'


def save_json(path,value):
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    temporary.replace(path)


def pagination_text(raw,job_id):
    marker=re.compile(r'(?m)^<!--BBVLM:'+re.escape(job_id)+r':(MORE|END|REFUSED)-->[ \t]*$')
    found=list(marker.finditer(raw))
    if len(found)!=1 or raw[found[0].end():].strip():
        raise ResponseError('Fin de portion absente/ambiguë ; conserver le natif, aucun renvoi aveugle')
    # Seuls la ligne de contrôle et son séparateur sont retirés ; le contenu
    # Unicode reçu, dont les espaces et retours, reste inchangé.
    content=raw[:found[0].start()]
    if not content.strip() and found[0].group(1)!='REFUSED':
        raise ResponseError('Portion vide sans refus explicite')
    return content,found[0].group(1)


class PagedPartReader(NativeMarkdownReader):
    def __init__(self,pane,directory,index,prefix,first_request=None,timeout=900):
        super().__init__(pane,directory,timeout)
        self.index=index;self.prefix=prefix;self.first_request=first_request
        self.revision=REVISION+f'-part-{index}-'+hashlib.sha256(prefix.encode()).hexdigest()

    def _prepare(self,image,requests,directory,scale):
        if scale!=1 or requests!=[LineRequest('PAGE',(0,0,*image.size))] or self.source_path is None:
            raise ValueError('Une page source entière est requise')
        cid=conversation_hint(getattr(self,'native_cwd',None))
        if cid is None:raise ReaderUnavailable('Conversation native non identifiée')
        if self.first_request and cid!=self.first_request['conversation_id']:
            raise ReaderUnavailable('Conversation changée pendant la pagination ; reprendre le contexte identifié')
        directory=Path(directory).resolve();directory.mkdir(parents=True,exist_ok=False)
        job_id=uuid.uuid4().hex
        manifest=dict(job_id=job_id,kind='page_markdown_native',native_conversation_id=cid,
                      scale=1,image=str(self.source_path),
                      image_sha256=hashlib.sha256(self.source_path.read_bytes()).hexdigest(),
                      size=list(image.size),source_pixels=True,native_views=[],
                      lines=[dict(id='PAGE',bbox=[0,0,*image.size])],
                      pagination_revision=REVISION,part_index=self.index,
                      prefix_sha256=hashlib.sha256(self.prefix.encode()).hexdigest())
        if self.first_request:
            manifest['prior_image_request']={key:self.first_request[key] for key in ('job_id','prompt','image')}
        if self.index==1:
            task=(f'Ouvre cette image fournie et fais son OCR COMPLET en Markdown : {self.source_path}. '
                  'Lis tous les titres, colonnes, articles, tableaux, annonces, notes et petits textes, '
                  'dans leur ordre naturel. ')
        else:
            task=('Continue la transcription de cette même image, exactement après la portion déjà '
                  'reçue. Ne répète aucun texte antérieur. Voici uniquement sa fin comme ancre, '
                  'ce n’est pas une référence ni un texte à corriger :\n'+
                  json.dumps(self.prefix[-700:],ensure_ascii=False)+'\n')
        prompt=(f'BBVLM requête {job_id}, portion {self.index}. '+task+
                'Conserve les graphies visibles, casse, accents, ponctuation et césures. '
                'Garde les lignes imprimées au sein des paragraphes. Aucun résumé, correction, '
                'texte complété ou commentaire. Une partie illisible se note [illisible], '
                'sans supprimer le reste. Donne au plus environ 6000 caractères de transcription '
                'dans cette réponse, en terminant une ligne imprimée ; nous demanderons la suite '
                'automatiquement. La page entière sera conservée même si elle exige plusieurs réponses. '
                'Réponds directement en Markdown, sans JSON. Termine sur une ligne séparée avec '
                f'<!--BBVLM:{job_id}:MORE--> s’il reste du texte à transcrire, '
                f'<!--BBVLM:{job_id}:END--> si tu as effectivement atteint la fin de toute la page, '
                f'ou <!--BBVLM:{job_id}:REFUSED--> en cas d’impossibilité. '
                f'Lis seulement cette image : {self.source_path}. Aucun autre fichier, shell, '
                'recherche, OCR externe ou écriture. BBVLM sauvegarde les réponses.')
        save_json(directory/'request.json',manifest)
        (directory/'prompt.txt').write_text(prompt,encoding='utf-8')
        return manifest,prompt

    def _read(self,requests,job_id):
        value,readings=super()._read(requests,job_id)
        directory=self.current_job_directory
        raw=readings[0].text
        (directory/'native-raw-markdown.md').write_text(raw,encoding='utf-8')
        if value['native_history_provenance'].get('trailing_native_errors'):
            raise ReaderUnavailable('Portion interrompue par une erreur native ; brut conservé, reprise à réparer')
        content,marker=pagination_text(raw,job_id)
        value['pagination']=dict(revision=REVISION,index=self.index,marker=marker,
                                 model_reported_complete=marker=='END',coverage_certified=False,
                                 content_sha256=hashlib.sha256(content.encode()).hexdigest())
        value['reading_status']='model_reported_'+marker.lower()+'_pending_independent_evaluation'
        value['lines'][0]['text']=content
        value['lines'][0]['uncertain']=value['lines'][0]['uncertain'] or marker=='REFUSED'
        return value,self.validate_response(value,requests,job_id)


class PagedMarkdownReader:
    def __init__(self,pane,directory,timeout=900,max_parts=64):
        self.pane=pane;self.directory=Path(directory);self.timeout=timeout;self.max_parts=max_parts

    def read_page(self,source,output):
        source=Path(source).resolve();output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
        source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
        state_path=output/'pagination-state.json'
        state=json.loads(state_path.read_text()) if state_path.exists() else dict(
            revision=REVISION,image=str(source),image_sha256=source_hash,parts=[],complete=False)
        if (state.get('revision'),state.get('image'),state.get('image_sha256'))!=(REVISION,str(source),source_hash):
            raise ReaderUnavailable('Source/protocole modifié pendant la pagination')
        prefix='';first_request=None;last=None
        for index in range(1,self.max_parts+1):
            if index<=len(state['parts']):
                saved=state['parts'][index-1];path=output/saved['path']
                if hashlib.sha256(path.read_bytes()).hexdigest()!=saved['sha256']:
                    raise ReaderUnavailable('Portion sauvegardée modifiée')
            part_output=output/'vt-parts'/f'{index:03d}'
            reader=PagedPartReader(self.pane,part_output/'page-lecture-jobs',index,prefix,first_request,self.timeout)
            last=reader.read_page(source,part_output)
            job=Path(reader.journal[-1]['directory'])
            value=json.loads((job/'response.json').read_text())
            if value.get('pagination',{}).get('index')!=index:
                raise ReaderUnavailable('Cache de portion incompatible')
            artifact=part_output/'vt.gemini.md'
            record=dict(index=index,path=str(artifact.relative_to(output)),
                        sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),job_id=last.job_id,
                        marker=value['pagination']['marker'],characters=len(last.text),
                        uncertain=last.uncertain,job_directory=str(job))
            if index<=len(state['parts']):
                if record!=state['parts'][index-1]:raise ReaderUnavailable('Provenance de portion modifiée')
            else:state['parts'].append(record)
            if first_request is None:
                manifest=json.loads((job/'request.json').read_text())
                proof=value['native_history_provenance']
                first_request=dict(job_id=last.job_id,prompt=(job/'prompt.txt').read_text(),image=str(source),
                                   conversation_id=proof['conversation_id'])
            prefix+=last.text
            temporary=output/'vt.gemini.tmp';temporary.write_text(prefix,encoding='utf-8')
            temporary.replace(output/'vt.gemini.md')
            state['complete']=record['marker']=='END';state['refused']=record['marker']=='REFUSED'
            state['next_part']=index+1
            save_json(state_path,state)
            save_json(output/'vt-provenance.json',dict(kind='page_markdown',image=str(source),
                image_sha256=source_hash,artifact_sha256=hashlib.sha256(prefix.encode()).hexdigest(),
                job_id=first_request['job_id'],provider='gemini',model_claim=None,
                model_display_terminal=last.model_display_terminal,model_native=last.model,
                uncertain=not state['complete'] or any(p['uncertain'] for p in state['parts']),
                characters=len(prefix),normalization='NFC',geometry_required=False,
                complete_pipeline_certified=False,pagination_revision=REVISION,parts=state['parts'],
                reading_status=('model_reported_complete_pending_independent_evaluation' if state['complete']
                                else 'refused_partial' if state['refused'] else 'partial_awaiting_next_portion'),
                model_reported_complete=state['complete'],coverage_certified=False))
            print(json.dumps(dict(part=index,characters=len(last.text),total_characters=len(prefix),
                                  marker=record['marker'],job_id=last.job_id)),flush=True)
            if state['complete']:
                return replace(last,text=prefix,job_id=first_request['job_id'],
                               uncertain=any(p['uncertain'] for p in state['parts']))
            if state['refused']:raise ReaderUnavailable('Refus de lecture explicite ; VT partielle conservée')
        raise ReaderUnavailable('Limite de portions atteinte ; couverture non acquise, VT partielle conservée')
