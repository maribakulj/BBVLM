"""VT autonome de page entière ; aucune segmentation ou référence en entrée."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import unicodedata
import uuid

from PIL import Image

from lecture import HerdrGeminiReader, LineRequest, ResponseError, validate_response


def validate_page_response(value, requests, job_id=None):
    if len(requests) != 1 or requests[0].id != 'PAGE':
        raise ValueError('Une seule page entière attendue')
    if not isinstance(value, dict) or value.get('kind') != 'page_markdown':
        raise ResponseError('Réponse page_markdown attendue')
    rows = value.get('lines')
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ResponseError('Une seule transcription PAGE attendue')
    row = rows[0]
    text = row.get('text')
    if 'text_parts' in row:
        parts = row['text_parts']
        if 'text' in row or not isinstance(parts, list) or not parts or \
                any(not isinstance(p, str) for p in parts):
            raise ResponseError('Segments Markdown invalides')
        text = ''.join(parts)
    if not isinstance(text, str) or any(ord(c) < 32 and c not in '\n\t' for c in text):
        raise ResponseError('Markdown absent ou caractères de contrôle invalides')
    # Réutiliser les contrôles d'identité/provenance sans autoriser les retours
    # de page dans le protocole diplomatique des lignes.
    checked = {**value, 'lines': [{**row, 'text': '', 'linebreak': None}]}
    checked['lines'][0].pop('text_parts', None)
    reading = validate_response(checked, requests, job_id)[0]
    return [replace(reading, text=unicodedata.normalize('NFC', text))]


class PageMarkdownReader(HerdrGeminiReader):
    """Même relais durable, avec un protocole de page et un cache distincts."""
    validate_response = staticmethod(validate_page_response)
    terminal_lines = 1000
    text_part_length = 64

    def __init__(self, pane, directory, timeout=900):
        super().__init__(pane, directory, timeout, revision='whole-page-markdown-v1')
        self.source_path = None

    def _prepare(self, image, requests, directory, scale):
        if scale != 1 or len(requests) != 1 or requests[0] != LineRequest('PAGE', (0, 0, *image.size)):
            raise ValueError('La VT de page doit lire tous les pixels source')
        if self.source_path is None:
            raise ValueError('Chemin image source absent')
        source = self.source_path
        directory = Path(directory).resolve()
        directory.mkdir(parents=True, exist_ok=False)
        job_id = uuid.uuid4().hex
        manifest = dict(job_id=job_id, kind='page_markdown', scale=1,
                        image=str(source), image_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                        size=list(image.size), source_pixels=True,
                        lines=[dict(id='PAGE', bbox=[0, 0, *image.size])])
        from native_page_history import conversation_hint
        manifest['native_conversation_id']=conversation_hint(getattr(self,'native_cwd',None))
        prompt = (f'BBVLM, transcription de page entière, requête {job_id}. '
                  f'Ouvre cette seule image source : {source}. '
                  'Fais son OCR complet en Markdown, dans son ordre naturel de lecture. '
                  'Transcris tous les titres, colonnes, articles, annonces, notes et textes visibles. '
                  'Conserve les mots, graphies, casse, accents et ponctuation ; aucun résumé, '
                  'aucune correction du texte, aucune complétion inventée. '
                  'Utilise des titres et paragraphes Markdown simples ; garde les lignes imprimées '
                  'à l’intérieur des paragraphes, sans compléter les mots coupés en fin de ligne. '
                  'Ne fournis aucune boîte ni coordonnées. Une difficulté de mise en page ne doit '
                  'pas supprimer de texte lisible. Si une partie est illisible, garde les parties '
                  'lisibles et indique uncertain=true. '
                  'Tu peux lire uniquement cette image ; aucun autre fichier, recherche, shell, '
                  'OCR externe ou écriture de fichier. BBVLM sauvegarde lui-même le Markdown. '
                  'Pour transporter le Markdown intact par le terminal, réponds uniquement avec '
                  f'un objet JSON indenté : job_id="{job_id}", kind="page_markdown", '
                  'provider="gemini", model=nom utilisé, '
                  'lines=[{id:"PAGE",text_parts:[segments Markdown],uncertain:bool}]. '
                  'Chaque segment contient au maximum 64 caractères et apparaît seul sur sa ligne '
                  'JSON, sans indentation sur les lignes des segments. Limite aussi chaque ligne '
                  'de segment à 68 colonnes JSON, en comptant guillemets et échappements. '
                  'Les retours du Markdown sont échappés en \\n dans les chaînes JSON. '
                  'La concaténation des segments doit reproduire EXACTEMENT le Markdown, espaces '
                  'et retours compris. Aucun texte hors JSON.')
        (directory/'request.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        (directory/'prompt.txt').write_text(prompt, encoding='utf-8')
        return manifest, prompt

    def _read(self, requests, job_id):
        terminal_result=None
        terminal_error=None
        try:
            terminal_result=super()._read(requests,job_id)
        except ResponseError as exc:
            terminal_error=exc
        directory=getattr(self,'current_job_directory',None)
        if directory is not None:
            manifest=json.loads((directory/'request.json').read_text())
            code,state,_=self._call('get',self.pane)
            agent=(state or {}).get('result',{}).get('agent',{})
            if not code and agent.get('agent') in ('agy','gemini') and agent.get('agent_status') in ('idle','done'):
                from native_page_history import identified_response
                try:
                    value,readings,proof=identified_response(manifest.get('native_conversation_id'),
                        (directory/'prompt.txt').read_text(),requests,job_id,self.validate_response)
                except ResponseError:
                    pass
                else:
                    value['native_history_provenance']=proof
                    (directory/'native-history-recovery.json').write_text(json.dumps(proof,indent=2))
                    return value,readings
        if terminal_result is not None:
            return terminal_result
        raise terminal_error

    def read_page(self, source, output):
        self.source_path = Path(source).resolve()
        output = Path(output).resolve()
        output.mkdir(parents=True, exist_ok=True)
        with Image.open(self.source_path) as image:
            image.load()
            reading = self.read_lines(image, [LineRequest('PAGE', (0, 0, *image.size))])[0]
        # Sauvegarde AVANT toute tentative de segmentation, géométrie ou OLR.
        artifact = output/'vt.gemini.md'
        temporary = artifact.with_suffix('.tmp')
        temporary.write_text(reading.text, encoding='utf-8')
        temporary.replace(artifact)
        provenance = dict(kind='page_markdown', image=str(self.source_path),
                          image_sha256=hashlib.sha256(self.source_path.read_bytes()).hexdigest(),
                          job_id=reading.job_id, provider=reading.provider, model_claim=reading.model,
                          model_display_terminal=reading.model_display_terminal,
                          uncertain=reading.uncertain, characters=len(reading.text),
                          artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),
                          normalization='NFC', geometry_required=False,
                          complete_pipeline_certified=False, jobs=self.journal)
        if self.journal:
            native_response=json.loads((Path(self.journal[-1]['directory'])/'response.json').read_text())
            for key in ('native_history_provenance','model_claim_source','uncertainty_basis','reading_status'):
                if key in native_response:provenance[key]=native_response[key]
            if native_response.get('model_claim_source')=='native_display_not_self_reported':
                provenance['model_claim']=None
                provenance['model_native']=reading.model
        target = output/'vt-provenance.json'
        temporary = target.with_suffix('.tmp')
        temporary.write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(target)
        return reading
