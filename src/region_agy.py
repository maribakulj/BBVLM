"""Lecture Gemini d'une région en mode non interactif (``agy -p``), une session neuve par appel.

Remplace la fenêtre herdr : l'image de la région et ses vues de détail sont
jointes par ``@chemin`` ; la réponse, le nombre de jetons et les images
réellement ouvertes (journal de conversation d'agy, lecture seule) sont
tracés dans vt-provenance.json, au format attendu par transcrire_regions.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import time
import unicodedata
import uuid

HISTORY = Path.home() / '.gemini/antigravity-cli/conversations'
NO_TOOLS = ('N’exécute aucune commande et n’utilise aucun outil autre que la lecture des images '
            'jointes : réponds directement, uniquement par la transcription.')


def observed_paths(conversation_id):
    """Chemins d'images ouverts par l'agent (outil de lecture), d'après sa base."""
    db = HISTORY / f'{conversation_id}.db'
    if not db.exists():
        return []
    found = set()
    with sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True) as con:
        for (payload,) in con.execute('SELECT step_payload FROM steps'):
            if payload:
                text = payload.decode('utf-8', 'ignore') if isinstance(payload, bytes) else str(payload)
                found.update(re.findall(r'"AbsolutePath":"([^"]+)"', text))
    return sorted(found)


def read_region(directory, image, views, task, model='gemini-3.8-flash-medium', timeout=900, attempts=3):
    directory = Path(directory).resolve()
    image = Path(image).resolve()
    names = [image.name] + [Path(v).name for v in views]
    prompt = task + '\n\nImage de la région : @' + names[0]
    if views:
        prompt += '\nVues de détail, dans l’ordre : ' + ' '.join('@' + n for n in names[1:])
    prompt += ('\nOuvre d’abord l’image jointe et lis-la. Si tu ne peux pas la voir, réponds uniquement '
               'IMAGE_ABSENTE : n’écris jamais un texte que tu n’as pas lu sur l’image.')
    prompt += '\nNe lis aucun autre fichier. ' + NO_TOOLS
    log, response, envelope, opened, saw_image, cid = [], '', {}, [], False, None
    for attempt in range(attempts):
        started = time.time()
        try:
            run = subprocess.run(['agy', '-p', prompt, '--print-timeout', f'{timeout-60}s',
                                  '--output-format', 'json', '--model', model],
                                 cwd=directory, capture_output=True, text=True, timeout=timeout)
            envelope = json.loads(run.stdout) if run.stdout.strip().startswith('{') else {}
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            envelope = {}
        response = (envelope.get('response') or '').strip()
        cid = envelope.get('conversation_id')
        opened = observed_paths(cid) if cid else []
        saw_image = str(image) in opened
        log.append(dict(attempt=attempt, seconds=round(time.time()-started, 1), status=envelope.get('status'),
                        usage=envelope.get('usage'), conversation_id=cid, image_opened=saw_image))
        # Seule une réponse COMPLÈTE est acceptée : un flux coupé puis repris
        # jusqu'au délai rend un texte partiel (statut ERROR), donc faux. Et
        # l'image DOIT avoir été ouverte : sans elle, Gemini a déjà rendu un
        # texte entier, plausible et inventé (La Presse 0476474, 4 régions/27).
        if response and 'IMAGE_ABSENTE' in response:
            saw_image = False
        if response and envelope.get('status') == 'SUCCESS' and saw_image:
            break
    text = unicodedata.normalize('NFC', re.sub(r'^```(?:markdown)?\s*|\s*```$', '', response).strip()) + '\n'
    (directory / 'vt.gemini.md').write_text(text, encoding='utf-8')
    paths = opened
    complete = bool(response) and envelope.get('status') == 'SUCCESS' and saw_image
    job = uuid.uuid4().hex
    provenance = dict(
        kind='page_markdown', image=str(image), image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
        job_id=job, provider='gemini', model_claim=None, model_native=model,
        uncertain=(not complete) or '[illisible]' in text, characters=len(text),
        artifact_sha256=hashlib.sha256((directory / 'vt.gemini.md').read_bytes()).hexdigest(),
        normalization='NFC', geometry_required=False, complete_pipeline_certified=False,
        prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
        native_history_provenance=dict(source='agy_print_json_and_sqlite_read_only', conversation_id=cid,
                                       input_views=dict(observed_paths=paths),
                                       trailing_native_errors=[] if complete else [dict(status=envelope.get('status'),
                                           image_opened=saw_image,
                                           message='réponse incomplète, absente, ou image non ouverte après les essais')]),
        calls=log, reading_status=('native_response_saved_pending_independent_evaluation' if complete
                                   else 'incomplete_after_retries'))
    (directory / 'prompt.txt').write_text(prompt, encoding='utf-8')
    (directory / 'vt-provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2))
    return dict(text=text, job_id=job, uncertain=provenance['uncertain'], model=model, provenance=provenance)
