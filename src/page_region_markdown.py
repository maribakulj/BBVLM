"""Lectures natives ciblées, journalisées et reprises sans double envoi."""
import hashlib
import json
from pathlib import Path
import time
import uuid
import sqlite3

from lecture import LineRequest, ReaderUnavailable
from native_page_history import conversation_hint
from page_native_markdown import NativeMarkdownReader


class RegionMarkdownReader(NativeMarkdownReader):
    allow_empty_response=True
    def __init__(self, pane, directory, task, views=(), timeout=900):
        super().__init__(pane, directory, timeout)
        self.task = task
        self.views = [Path(p).resolve() for p in views]
        self.revision = 'region-native-v2-clear-ack-' + hashlib.sha256(
            json.dumps([task, [(str(p), hashlib.sha256(p.read_bytes()).hexdigest())
                              for p in self.views]], ensure_ascii=False).encode()).hexdigest()

    def _prepare(self, image, requests, directory, scale):
        if scale != 1 or requests != [LineRequest('PAGE', (0, 0, *image.size))]:
            raise ValueError('Une image source complète est requise')
        cid = conversation_hint(getattr(self, 'native_cwd', None))
        if cid is None:
            raise ReaderUnavailable('Conversation native absente')
        history=Path.home()/'.gemini/antigravity-cli/conversations'
        before=set(history.glob('*.db'))
        code, _, error = self._call('prompt', self.pane, '/clear')
        if code:
            raise ReaderUnavailable('Contexte vierge non établi : ' + error)
        # /clear est asynchrone dans agy 1.3 : attendre la nouvelle base vide,
        # sinon le prompt peut partir dans la conversation précédente.
        deadline=time.monotonic()+10
        fresh=None
        while time.monotonic()<deadline:
            candidates=[]
            for path in set(history.glob('*.db'))-before:
                try:
                    with sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True) as db:
                        if db.execute('SELECT count(*) FROM steps').fetchone()[0]==0:
                            candidates.append(path.stem)
                except sqlite3.Error:continue
            if len(candidates)>1:raise ReaderUnavailable('Plusieurs nouvelles conversations ; aucun prompt envoyé')
            if candidates:
                fresh=candidates[0];break
            time.sleep(.1)
        if fresh is None:raise ReaderUnavailable('Réinitialisation native non confirmée ; aucun prompt envoyé')
        cid=fresh
        directory = Path(directory).resolve()
        directory.mkdir(parents=True, exist_ok=False)
        manifest = dict(job_id=uuid.uuid4().hex, kind='page_markdown_native',
                        native_conversation_id=cid,
                        request_binding='exact_fresh_human_prompt_out_of_band_UUID',
                        native_request_not_before=time.time(), scale=1,
                        image=str(self.source_path),
                        image_sha256=hashlib.sha256(self.source_path.read_bytes()).hexdigest(),
                        size=list(image.size), source_pixels=True,
                        native_views=[dict(path=str(p), image_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                                      for p in self.views],
                        lines=[dict(id='PAGE', bbox=[0, 0, *image.size])])
        prompt = self.task + '\nImage : ' + str(self.source_path)
        if self.views:
            prompt += '\nVues de détail à lire dans cet ordre :\n' + '\n'.join(map(str, self.views))
        prompt += ('\nLis uniquement les images listées. Aucun autre fichier, recherche, shell, '
                   'OCR externe ou écriture de fichier. Réponds directement ; BBVLM sauvegarde ta réponse.')
        (directory / 'request.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        (directory / 'prompt.txt').write_text(prompt, encoding='utf-8')
        return manifest, prompt
