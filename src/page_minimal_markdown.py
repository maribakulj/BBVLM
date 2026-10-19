"""Prompt utilisateur minimal ; identité du job conservée hors du prompt."""
import hashlib
import json
from pathlib import Path
import uuid
import time

from lecture import LineRequest,ReaderUnavailable
from native_page_history import conversation_hint
from page_native_markdown import NativeMarkdownReader


TASK='Je veux l’OCR complet de cette page en Markdown.'


class MinimalMarkdownReader(NativeMarkdownReader):
    def __init__(self,pane,directory,timeout=900):
        super().__init__(pane,directory,timeout)
        self.revision='whole-page-minimal-out-of-band-v4'

    def _prepare(self,image,requests,directory,scale):
        if scale!=1 or requests!=[LineRequest('PAGE',(0,0,*image.size))] or self.source_path is None:
            raise ValueError('Une page source entière est requise')
        cid=conversation_hint(getattr(self,'native_cwd',None))
        if cid is None:raise ReaderUnavailable('Conversation native absente')
        code,_,error=self._call('prompt',self.pane,'/clear')
        if code:raise ReaderUnavailable('Contexte vierge non établi : '+error)
        directory=Path(directory).resolve();directory.mkdir(parents=True,exist_ok=False)
        manifest=dict(job_id=uuid.uuid4().hex,kind='page_markdown_native',native_conversation_id=cid,
                      request_binding='exact_fresh_human_prompt_out_of_band_UUID',scale=1,
                      native_request_not_before=time.time(),
                      image=str(self.source_path),image_sha256=hashlib.sha256(self.source_path.read_bytes()).hexdigest(),
                      size=list(image.size),source_pixels=True,native_views=[],
                      lines=[dict(id='PAGE',bbox=[0,0,*image.size])])
        prompt=TASK+'\n'+str(self.source_path)
        (directory/'request.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
        (directory/'prompt.txt').write_text(prompt,encoding='utf-8')
        return manifest,prompt
