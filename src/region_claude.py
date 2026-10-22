"""Lecture d'une région par Claude (claude -p, non interactif), même contrat que region_agy.read_region.

Session neuve par appel, seul outil permis : Read. La preuve d'ouverture de
l'image est l'appel Read visible dans le flux stream-json. Le texte est écrit
dans vt.gemini.md (nom historique du fichier de lecture d'une région).
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import unicodedata
import uuid

from region_agy import run_agy

LINES = ('IMPORTANT : une ligne imprimée = une ligne de ta réponse ; ne recolle jamais les lignes en '
         'paragraphes ; un mot coupé en fin de ligne garde son trait d’union en fin de ligne et sa suite '
         'commence la ligne suivante. N’écris en fin de ligne QUE les lettres imprimées sur cette ligne, '
         'jamais le mot complété (« batail- » reste « batail- », pas « bataill- » ni « bataillon »). '
         'N’ajoute aucune lettre, aucun mot ni aucune ligne qui ne soit pas imprimé, même si le mot '
         'semble incomplet. N’écris jamais de remarque, d’explication ni de phrase sur l’image ou sur ta '
         'lecture ; une partie indéchiffrable s’écrit [illisible], entre crochets, rien d’autre ; une région '
         'sans aucun texte imprimé (ornement, filet, image) se répond exactement VIDE. '
         'Une lettre à demi coupée au bord de l’image se transcrit comme la lettre visible, pas [illisible]. '
         'Utilise uniquement l’alphabet latin (aucune lettre cyrillique ou grecque d’apparence voisine).')

# Lettres d'apparence latine produites par le lecteur (cyrillique, API) : ramenées à la lettre latine
# imprimée. Remplacement à l'identique de forme, compté dans la provenance.
HOMOGLYPHS = str.maketrans('аеорсухіјѕԁԛАВЕКМНОРСТХІЈЅɔ', 'aeopcyxijsdqABEKMHOPCTXIJSc')


def _parse(stream):
    """(texte final, statut, chemins lus par Read, usage, coût) depuis la sortie stream-json."""
    text, status, opened, usage, cost = '', None, [], None, None
    for line in stream.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get('type') == 'assistant':
            for block in event.get('message', {}).get('content', []):
                if block.get('type') == 'tool_use' and block.get('name') == 'Read':
                    opened.append(str(block.get('input', {}).get('file_path', '')))
        elif event.get('type') == 'result':
            text = event.get('result') or ''
            status = 'SUCCESS' if event.get('subtype') == 'success' and not event.get('is_error') else 'ERROR'
            usage, cost = event.get('usage'), event.get('total_cost_usd')
    return text, status, opened, usage, cost


def _enlarge(path, directory, pixels=1.15e6, side=1568):
    from PIL import Image
    with Image.open(path) as im:
        factor = min(2.0, (pixels / (im.width * im.height)) ** .5, side / max(im.size))
        if factor < 1.1:
            return path
        target = directory / f'claude-{path.stem}.png'
        im.convert('RGB').resize((round(im.width*factor), round(im.height*factor)), Image.LANCZOS).save(target)
        return target


def read_region(directory, image, views, task, model='claude-haiku-5-5', timeout=240, attempts=3, expected_lines=None):
    """expected_lines : lignes détectées dans la région ; une réponse qui en rend moins des 3/4
    (lignes recollées en paragraphes) est redemandée en donnant ce nombre."""
    directory = Path(directory).resolve()
    source = Path(image).resolve()
    # Claude réduit toute image au-delà d'environ 1,15 Mpx / 1568 px de côté : les crops plus
    # petits sont agrandis jusqu'à cette limite (petits caractères, lettres au bord du crop).
    image, *views = [_enlarge(Path(p).resolve(), directory) for p in [source, *views]]
    paths = [str(image)] + [str(v) for v in views]
    prompt = ('Ouvre avec l’outil Read l’image de la région : ' + paths[0])
    if views:
        prompt += ', puis TOUTES les vues de détail, dans l’ordre : ' + ' '.join(paths[1:])
    prompt += ('. Réponds ensuite UNIQUEMENT par la transcription. ' + task + LINES +
               ' Si tu ne peux pas voir l’image, réponds uniquement IMAGE_ABSENTE : n’écris jamais un texte '
               'que tu n’as pas lu sur l’image. Ne lis aucun autre fichier et n’utilise aucun autre outil.')
    log, best, ask = [], None, prompt
    for attempt in range(attempts):
        started = time.time()
        try:
            out = run_agy(['claude', '-p', ask, '--model', model, '--allowedTools', 'Read',
                           '--output-format', 'stream-json', '--verbose'], directory, timeout)
        except subprocess.SubprocessError:
            out = ''
        response, status, opened, usage, cost = _parse(out or '')
        response = response.strip()
        saw_image = str(image) in opened and 'IMAGE_ABSENTE' not in response
        lines = sum(bool(l.strip()) for l in response.splitlines())
        # kraken compte souvent 1-2 lignes de trop (filets, ornements) : relance seulement s'il en manque
        # au moins 2 et 10 %, et plus du tout si la relance précédente n'a rien apporté
        merged = (bool(expected_lines) and expected_lines >= 8 and lines < expected_lines - max(2, .1 * expected_lines)
                  and not (best is not None and attempt and lines <= best[4]))
        log.append(dict(attempt=attempt, seconds=round(time.time()-started, 1), status=status, usage=usage,
                        cost_usd=cost, image_opened=saw_image, views_opened=sum(p in opened for p in paths[1:]),
                        lines=lines, expected_lines=expected_lines, merged_lines=merged))
        valid = bool(response) and status == 'SUCCESS' and saw_image
        if valid and (best is None or lines > best[4]):
            best = (response, status, opened, saw_image, lines)
        if valid and not merged:
            break
        if merged:
            ask = prompt + (f' ATTENTION : cette région compte environ {expected_lines} lignes imprimées ; '
                            f'ta réponse précédente n’en avait que {lines} : tu as recollé ou sauté des lignes. '
                            'Rends chaque ligne imprimée sur sa propre ligne, depuis la toute première en haut de l’image.')
    response, status, opened, saw_image, _ = best or (response, status, opened, saw_image, 0)
    empty = response.strip() == 'VIDE'
    text = '\n' if empty else unicodedata.normalize('NFC', re.sub(r'^```(?:markdown)?\s*|\s*```$', '', response).strip()) + '\n'
    homoglyphs = sum(c != d for c, d in zip(text, text.translate(HOMOGLYPHS)))
    text = text.translate(HOMOGLYPHS)
    (directory / 'vt.gemini.md').write_text(text, encoding='utf-8')
    complete = (empty or bool(response)) and status == 'SUCCESS' and saw_image
    job = uuid.uuid4().hex
    provenance = dict(
        kind='page_markdown', image=str(source), image_sent=str(image), image_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        job_id=job, provider='anthropic', model_claim=None, model_native=model,
        uncertain=(not complete) or '[illisible]' in text, characters=len(text),
        artifact_sha256=hashlib.sha256((directory / 'vt.gemini.md').read_bytes()).hexdigest(),
        normalization='NFC', geometry_required=False, complete_pipeline_certified=False,
        prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
        native_history_provenance=dict(source='claude_print_stream_json', input_views=dict(observed_paths=opened),
                                       trailing_native_errors=[] if complete else [dict(status=status,
                                           image_opened=saw_image,
                                           message='réponse incomplète, absente, ou image non ouverte après les essais')]),
        calls=log, homoglyphs_replaced=homoglyphs, reading_status=('native_response_saved_pending_independent_evaluation' if complete
                                   else 'incomplete_after_retries'))
    (directory / 'prompt.txt').write_text(prompt, encoding='utf-8')
    (directory / 'vt-provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2))
    return dict(text=text, job_id=job, uncertain=provenance['uncertain'], model=model, provenance=provenance)
