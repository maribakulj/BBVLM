"""Ancres de localisation automatiques, jamais une transcription de référence.

Le texte de ces ancres sert seulement à retrouver les passages du Markdown.
Il n'est jamais recopié comme transcription finale. Les boîtes viennent de la
segmentation automatique et tous les échecs de décodage restent enregistrés.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

from PIL import Image


VERSION = 'automatic-page-anchors-v1'
IMPLEMENTATION_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def _reject_reference_fields(value):
    forbidden = {'gold', 'reference', 'reference_text', 'reference_bbox',
                 'ground_truth', 'word_boxes', 'human_text'}
    if isinstance(value, dict):
        if forbidden.intersection(value):
            raise ValueError('Une entrée de production contient des champs de référence')
        for child in value.values():
            _reject_reference_fields(child)
    elif isinstance(value, list):
        for child in value:
            _reject_reference_fields(child)


def load_automatic_lines(image, directory):
    """Importer uniquement un cache de segmentation lié à cette image."""
    directory = Path(directory)
    config = json.loads((directory / 'segmentation-config.json').read_text())
    if config.get('image_sha256') != sha256(image):
        raise ValueError('La segmentation vient d’une autre image')
    if config.get('version') != 'blla-rectangles-v1':
        raise ValueError('Provenance de segmentation automatique inconnue')
    rows = json.loads((directory / 'segmentation.json').read_text())
    _reject_reference_fields(rows)
    with Image.open(image) as page:
        width, height = page.size
    seen = set()
    for row in rows:
        if not isinstance(row.get('id'), str) or row['id'] in seen:
            raise ValueError('Identifiant de ligne absent ou dupliqué')
        seen.add(row['id'])
        if not str(row.get('source', '')).startswith('kraken-blla/'):
            raise ValueError('Une ligne ne déclare pas de détection automatique')
        for key in ('bbox', 'detector_bbox'):
            if key not in row and key == 'detector_bbox':
                continue
            box = row.get(key)
            if not isinstance(box, list) or len(box) != 4 or any(
                    not isinstance(v, (int, float)) or not math.isfinite(v) for v in box):
                raise ValueError('Boîte de ligne invalide')
            x0, y0, x1, y1 = box
            if not 0 <= x0 < x1 <= width or not 0 <= y0 < y1 <= height:
                raise ValueError('Boîte de ligne hors image')
    return rows


def cached_reading_anchors(image, directory):
    """Recycler des lectures Gemini existantes comme simples ancres spatiales."""
    directory = Path(directory)
    lines = load_automatic_lines(image, directory)
    readings_path = directory / 'readings.json'
    readings = json.loads(readings_path.read_text())
    _reject_reference_fields(readings)
    by_id = {}
    line_ids = {r['id'] for r in lines}
    for row in readings:
        if row['id'] in by_id or row['id'] not in line_ids:
            raise ValueError('Lecture auxiliaire avec ID dupliqué ou inconnu')
        if row.get('provider') != 'gemini' or not row.get('job_id'):
            raise ValueError('Lecture auxiliaire sans provenance Gemini')
        if not isinstance(row.get('text'), str):
            raise ValueError('Lecture auxiliaire invalide')
        by_id[row['id']] = row
    out = []
    for line in lines:
        reading = by_id.get(line['id'])
        out.append({**line, 'auxiliary_text': reading['text'] if reading else '',
                    'auxiliary_status': 'uncertain' if reading and reading.get('uncertain') else
                                        'available' if reading else 'missing',
                    'auxiliary_source': 'cached_gemini_line_reading',
                    'auxiliary_job_id': reading.get('job_id') if reading else None})
    return dict(version=VERSION, image_sha256=sha256(image), lines=out,
                purpose='localization_only', transcription_source=False,
                inputs={str(directory / 'segmentation.json'): sha256(directory / 'segmentation.json'),
                        str(readings_path): sha256(readings_path)})


def ctc_anchors(image, lines, output, model_path=None, decoder=None, model_signature=None):
    """Décodage local reprenable par ligne ; aucun appel Gemini ou référence.

    decoder est injectable pour tester les interruptions. En production le
    modèle et les pixels exacts font partie de la clé de cache.
    """
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    _reject_reference_fields(lines)
    image_digest = sha256(image)
    if decoder is None:
        import numpy as np
        import torch
        from boxers.forcectc import CHEMIN, _ligne_tenseur
        from boxers import forcectc
        from kraken.lib.models import load_any
        model_path = Path(model_path or CHEMIN)
        model_signature = {'path': str(model_path), 'sha256': sha256(model_path),
                           'preprocessing_sha256': sha256(forcectc.__file__)}
        model = load_any(model_path)
        with Image.open(image) as page:
            gray = np.asarray(page.convert('L'))

        def decoder(row):
            line = SimpleNamespace(line_box=tuple(row.get('detector_bbox', row['bbox'])))
            with torch.inference_mode():
                return model.predict_string(_ligne_tenseur(gray, line, model))[0]
    if model_signature is None:
        raise ValueError('Signature du décodeur requise pour un cache fiable')
    signature = dict(version=VERSION, implementation_sha256=IMPLEMENTATION_SHA256,
                     image_sha256=image_digest, model=model_signature,
                     segmentation_sha256=hashlib.sha256(json.dumps(lines, sort_keys=True).encode()).hexdigest())
    config = output / 'anchors-config.json'
    if config.exists() and json.loads(config.read_text()) != signature:
        raise ValueError('Configuration d’ancres modifiée ; employer un nouveau dossier')
    save_json(config, signature)
    rows = []
    for line in lines:
        key = hashlib.sha256(json.dumps({'signature': signature, 'line': line}, sort_keys=True).encode()).hexdigest()
        cache = output / 'line-cache' / (key + '.json')
        result = None
        if cache.exists():
            try:
                result = json.loads(cache.read_text())
                if (not isinstance(result, dict) or not isinstance(result.get('auxiliary_text'), str)
                        or result.get('auxiliary_status') not in {'available', 'decode_failed'}
                        or result['auxiliary_status'] == 'decode_failed' and
                           (result['auxiliary_text'] or not isinstance(result.get('auxiliary_error'), str))):
                    raise ValueError('Cache d’ancre incomplet')
            except (ValueError, UnicodeError):
                # Garder la preuve du cache défectueux ; seul le décodeur
                # automatique source est rejoué, jamais une lecture Gemini.
                digest = sha256(cache)
                cache.replace(cache.with_suffix('.invalid-' + digest[:12] + '.json'))
                result = None
        if result is None:
            try:
                text = decoder(line)
                if not isinstance(text, str):
                    raise ValueError('Le décodeur doit produire une chaîne')
                result = dict(auxiliary_text=text, auxiliary_status='available')
            except (ValueError, RuntimeError) as exc:
                result = dict(auxiliary_text='', auxiliary_status='decode_failed',
                              auxiliary_error=f'{type(exc).__name__}: {exc}')
            save_json(cache, result)
        rows.append({**line, **result, 'auxiliary_source': 'kraken_ctc'})
        save_json(output / 'anchors-state.json', dict(completed=len(rows), total=len(lines)))
    artifact = dict(**signature, lines=rows, purpose='localization_only', transcription_source=False)
    save_json(output / 'anchors.json', artifact)
    return artifact
