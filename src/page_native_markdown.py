"""Lecture Markdown naturelle avec vues natives de la page, sans lignes imposées."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import uuid

from lecture import LineRequest, Reading, ReaderUnavailable, ResponseError, _terminal_text
from page_markdown import PageMarkdownReader
from native_page_history import conversation_hint, identified_markdown, input_view_audit, resolve_conversation


def tile_boxes(size,tile_size=1536,overlap=192):
    if tile_size<256 or not 0<=overlap<tile_size:
        raise ValueError('Taille/chevauchement de vues invalide')
    def starts(extent):
        last=max(0,extent-tile_size)
        values=list(range(0,last+1,tile_size-overlap))
        if values[-1]!=last:values.append(last)
        return values
    width,height=size
    return [(x,y,min(x+tile_size,width),min(y+tile_size,height))
            for y in starts(height) for x in starts(width)]


class NativeMarkdownReader(PageMarkdownReader):
    allow_format_recovery=False

    def __init__(self,pane,directory,timeout=900,tile_size=1536):
        super().__init__(pane,directory,timeout)
        self.tile_size=tile_size
        self.revision=f'whole-page-markdown-native-v2-tiles-{tile_size}'

    def _prepare(self,image,requests,directory,scale):
        if scale!=1 or requests!=[LineRequest('PAGE',(0,0,*image.size))] or self.source_path is None:
            raise ValueError('Page source entière requise')
        cid=conversation_hint(getattr(self,'native_cwd',None))
        if cid is None:raise ReaderUnavailable('Conversation native absente ; aucun envoi Markdown ambigu')
        directory=Path(directory).resolve();directory.mkdir(parents=True,exist_ok=False)
        job_id=uuid.uuid4().hex
        views=[]
        for i,box in enumerate(tile_boxes(image.size,self.tile_size),1):
            path=directory/f'view-{i:03d}.png'
            image.crop(box).convert('RGB').save(path)
            views.append(dict(path=str(path),source_bbox=list(box),source_pixels=True,
                              image_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        manifest=dict(job_id=job_id,kind='page_markdown_native',native_conversation_id=cid,
            scale=1,image=str(self.source_path),image_sha256=hashlib.sha256(self.source_path.read_bytes()).hexdigest(),
            size=list(image.size),source_pixels=True,lines=[dict(id='PAGE',bbox=[0,0,*image.size])],
            native_views=views,tile_size=self.tile_size,overlap=192)
        prompt=(f'BBVLM, requête {job_id}. Transcris entièrement cette page en Markdown : '
                f'{self.source_path}. Conserve tout le texte visible, graphies, casse, accents et '
                'ponctuation, sans résumé ni correction. Titres et paragraphes simples, ordre naturel '
                'des colonnes et articles. Pour lire le petit texte, consulte TOUTES ces vues de la '
                'même page à résolution source : '+json.dumps(views,ensure_ascii=False)+'. '
                'Les coordonnées servent seulement à repérer les vues ; elles se chevauchent. '
                'Fusionne la lecture sans répéter les chevauchements et sans inventer les mots coupés. '
                'Une partie illisible se note [illisible], sans supprimer le reste lisible. '
                'Réponds directement avec le Markdown complet, sans JSON, métadonnées ni découpage '
                'en segments. Lis seulement les images listées, aucun autre fichier, shell, recherche '
                'ou OCR externe. Aucune écriture de fichier : BBVLM sauvegarde ta réponse.')
        (directory/'request.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
        (directory/'prompt.txt').write_text(prompt)
        return manifest,prompt

    def _read(self,requests,job_id):
        code,value,error=self._call('read',self.pane,'--source','recent-unwrapped','--lines','1000')
        if code or value is None:raise ReaderUnavailable('Terminal natif inaccessible : '+error)
        self.last_terminal=_terminal_text(value['result'])
        code,state,error=self._call('get',self.pane)
        agent=(state or {}).get('result',{}).get('agent',{})
        if code or agent.get('agent') not in ('agy','gemini') or agent.get('agent_status') not in ('idle','done'):
            raise ReaderUnavailable('Markdown natif encore actif ; récupérer ce UUID sans nouveau prompt')
        displays=re.findall(r'(Gemini\s+[\d.]+\s+(?:Flash|Pro)\s*·\s*\w+)\s*$',self.last_terminal,re.MULTILINE)
        if not displays:raise ReaderUnavailable('Modèle Gemini natif non attesté')
        directory=self.current_job_directory
        manifest=json.loads((directory/'request.json').read_text())
        out_of_band=manifest.get('request_binding')=='exact_fresh_human_prompt_out_of_band_UUID'
        not_before=manifest.get('native_request_not_before')
        cid,resolution=resolve_conversation([manifest['native_conversation_id'],conversation_hint(agent.get('cwd'))],
            (directory/'prompt.txt').read_text(),job_id,out_of_band=out_of_band,native_not_before=not_before)
        if cid!=manifest['native_conversation_id']:
            manifest['native_conversation_id']=cid
            (directory/'native-conversation-resolution.json').write_text(json.dumps(resolution,indent=2))
            (directory/'request.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
        continuation_path=directory/'native-authorized-continuations.json'
        continuations=json.loads(continuation_path.read_text()) if continuation_path.exists() else []
        markdown,proof=identified_markdown(cid,
            (directory/'prompt.txt').read_text(),job_id,authorized_continuations=continuations,
            prior_image_request=manifest.get('prior_image_request'),out_of_band=out_of_band,native_not_before=not_before,
            allow_empty=getattr(self,'allow_empty_response',False))
        proof['input_views']=input_view_audit(manifest['native_conversation_id'],
            (directory/'prompt.txt').read_text(),job_id,
            [manifest['image']]+[v['path'] for v in manifest['native_views']],
            authorized_continuations=continuations,out_of_band=out_of_band,native_not_before=not_before)
        text=unicodedata.normalize('NFC',markdown.replace('\r\n','\n'))
        uncertain=not text.strip() or '[illisible]' in text.lower() or bool(proof.get('trailing_native_errors'))
        model=displays[-1]
        value=dict(job_id=job_id,kind='page_markdown',provider='gemini',model=model,
                   model_claim_source='native_display_not_self_reported',
                   native_history_provenance=proof,
                   reading_status=proof.get('response_completeness','native_response_saved_pending_independent_evaluation'),
                   uncertainty_basis='literal_illisible_empty_or_native_interruption_not_quality_certificate',
                   lines=[dict(id='PAGE',text=text,uncertain=uncertain)])
        (directory/'native-history-recovery.json').write_text(json.dumps(proof,indent=2))
        return value,[Reading('PAGE',text,uncertain,'gemini',model,job_id=job_id,model_display_terminal=model)]
