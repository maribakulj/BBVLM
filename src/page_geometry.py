"""Placement d'une lecture de page déjà appariée, sans nouvelle lecture.

Les boîtes de ligne sont demi-ouvertes, les boîtes internes de mot inclusives.
Le texte et le statut d'appariement sont conservés même si le placement échoue.
L'ALTO initial contient les placements contrôlés, sans prétendre avoir reconnu
les articles ou certifié la transcription complète.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
import os
import time
from pathlib import Path
from types import SimpleNamespace
import unicodedata

import cv2
import numpy as np

import alto
import correct
from export_training import polygon
import ink
from placement_cache import PlacementCache
from page_text_view import compact_line_text_view


IMPLEMENTATION_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
MATCHED_STATUSES = frozenset({'matched', 'assigned', 'aligned', 'appariee', 'appariement_resolu'})


CHECKPOINT_SECONDS = 30


_WORKER = {}


def _placement_workers(boxer, pending):
    """Processus de placement : BBVLM_PLACEMENT_WORKERS (défaut 3), seulement pour
    ForceCTC (reconstructible dans un autre processus) et assez de lignes."""
    if type(boxer).__name__ != 'ForceCTC' or pending < 40:
        return 1
    try:
        return max(1, int(os.environ.get('BBVLM_PLACEMENT_WORKERS', '3')))
    except ValueError:
        return 1


def _worker_init(image, spec):
    import torch
    torch.set_num_threads(1)
    from boxers.forcectc import ForceCTC
    _WORKER['gray'] = cv2.imread(image, cv2.IMREAD_GRAYSCALE)
    _WORKER['boxer'] = ForceCTC(**spec)


def _worker_place(annotation):
    try:
        _place(_WORKER['gray'], annotation, _WORKER['boxer'])
    except Exception as exc:
        annotation.update(status='erreur_geometrie', reason=f'{type(exc).__name__}: {exc}')
    return annotation


def _write_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def _valid_box(box, width, height):
    return (isinstance(box, (list, tuple)) and len(box) == 4
            and all(isinstance(v, (int, float)) and math.isfinite(v) and int(v) == v for v in box)
            and 0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height)


def _place(gray, annotation, boxer):
    """Un seul placement imposé ; aucune correction ni relecture de texte."""
    height, width = gray.shape
    text = annotation['text']
    if not text.strip():
        annotation['status'] = 'texte_absent'
        return
    if '\n' in text or '\r' in text:
        annotation['status'] = 'texte_multiligne_non_apparie'
        return
    if text != unicodedata.normalize('NFC', text):
        annotation['status'] = 'normalisation_non_nfc'
        return
    box, source = annotation.get('bbox'), annotation.get('reading_bbox')
    if not _valid_box(box, width, height) or not _valid_box(source, width, height):
        annotation['status'] = 'geometrie_ligne_invalide'
        return
    box, source = [int(v) for v in box], [int(v) for v in source]
    line = SimpleNamespace(text=text, words=text.split(), line_box=tuple(source), word_boxes=[])
    try:
        boxes = boxer.boxes(gray, line)
        annotation['alignment'] = deepcopy(getattr(boxer, 'last_alignment', None))
        annotation['chars'] = deepcopy(getattr(boxer, 'last_char_positions', None))
    except Exception as exc:
        annotation.update(status=('alphabet_aligneur_incompatible' if 'hors alphabet' in str(exc)
                                  else 'alignement_non_resolu'), reason=str(exc))
        return
    if len(boxes) != len(line.words):
        annotation['status'] = 'compte_mots_incoherent'
        return
    # Ne pas tronquer silencieusement des coordonnées flottantes ou non finies.
    if any(not isinstance(b, (tuple, list, np.ndarray)) or len(b) != 4
           or any(not isinstance(v, (int, float, np.number)) or not np.isfinite(v) or int(v) != v for v in b)
           for b in boxes):
        annotation['status'] = 'geometrie_invalide'
        return
    boxes = [tuple(int(v) for v in b) for b in boxes]
    if (any(not (0 <= a <= c < width and 0 <= b <= d < height) for a, b, c, d in boxes)
            or any(a[2] >= b[0] for a, b in zip(boxes, boxes[1:]))):
        annotation['status'] = 'geometrie_invalide'
        return
    words = [dict(text=word, x0=b[0], y0=b[1], x1=b[2], y1=b[3], synthetic=False)
             for word, b in zip(line.words, boxes)]
    annotation['words'] = words
    measured = [min(b[0] for b in boxes), min(b[1] for b in boxes),
                max(b[2] for b in boxes) + 1, max(b[3] for b in boxes) + 1]
    expanded = [min(box[0], measured[0]), min(box[1], measured[1]),
                max(box[2], measured[2]), max(box[3], measured[3])]
    if expanded != list(box):
        annotation['geometry_bbox_before_words'] = list(box)
        annotation['bbox'] = expanded
    chars = annotation.get('chars')
    if chars is not None and (len(chars) != len(text) or any(
            not isinstance(c, (tuple, list)) or len(c) != 3
            or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in c)
            or not (0 <= c[0] <= c[1] <= width and 0 <= c[2] <= 1) for c in chars)):
        annotation['status'] = 'caracteres_invalides'
        return
    try:
        cost, _, _ = correct.cout_ligne(gray, source[0], source[2], source[1], source[3],
                                       (source[1] + source[3]) // 2, text, ink.line_scale(source))
        cost = cost / max(1, len(line.words)) if math.isfinite(cost) and cost < 1e8 else 99.0
    except Exception as exc:
        annotation.update(status='controle_encre_non_resolu', reason=str(exc))
        return
    annotation.update(cout=round(cost, 3), status='placee')


def _global_checks(annotations):
    """Même contrôle d'encre et de collisions que produire, sans toucher au texte."""
    placed = [a for a in annotations if a['status'] == 'placee']
    active, collisions = [], set()
    for lid, word in sorted(((a['id'], w) for a in placed for w in a['words']),
                            key=lambda item: item[1]['y0']):
        active = [(other, box) for other, box in active if box['y1'] >= word['y0']]
        for other, box in active:
            if other != lid and min(box['x1'], word['x1']) >= max(box['x0'], word['x0']):
                collisions.update((lid, other))
        active.append((lid, word))
    costs = [a['cout'] for a in placed if a['id'] not in collisions]
    threshold = (correct.seuil_auto(costs) if len(costs) >= 8 else 1.0) * 2
    for annotation in placed:
        if annotation['id'] in collisions:
            annotation['status'] = 'superposition_inter_lignes'
        elif annotation['cout'] > threshold:
            annotation['status'] = 'ajustement_encre_suspect'
        elif not annotation['assignment_resolved']:
            annotation.update(status='appariement_non_resolu', geometry_valid=True)
        else:
            annotation.update(status='retenue', geometry_valid=True, training_eligible=True,
                              alto_eligible=True)
    return threshold


def _alto_bytes(image, width, height, annotations, boxer_name):
    blocks = []
    for annotation in annotations:
        if not annotation['alto_eligible']:
            continue
        box = annotation['bbox']
        line = dict(id=annotation['id'], text=annotation['text'], words=annotation['words'],
                    bbox=[box[0], box[1], box[2] - 1, box[3] - 1],
                    polygon=polygon(box), baseline=annotation.get('baseline', []))
        blocks.append(dict(id='B_' + annotation['id'], lines=[line],
                           x0=box[0], y0=box[1], x1=box[2] - 1, y1=box[3] - 1))
    data = alto.build(width, height, Path(image).name, blocks, 'BBVLM page Markdown + ' + boxer_name,
                      'Texte de page conservé dans les artefacts de transcription ; placements '
                      'contrôlés uniquement. Aucun article ni ordre des blocs certifié. '
                      'annotations.json conserve aussi les lignes non résolues.')
    return data, alto.validate(data)


def place_assignments(image, assignments, boxer=None, output_dir=None, metadata=None):
    """Place ``{line_id|id, bbox, text, status}`` et conserve chaque proposition.

    ``detector_bbox`` (ou ``reading_bbox``) permet un crop plus large que bbox.
    ``assignment_resolved`` explicite prime ; sinon les statuts matched/assigned
    sont éligibles. Un autre statut reste dans les annotations et peut recevoir
    une géométrie diagnostique, jamais une certification d'appariement implicite.
    ``output_dir`` ajoute checkpoints et ALTO ; ``metadata`` garde la provenance
    du lecteur (provider/model/job_id), sans invoquer celui-ci.
    """
    image = Path(image)
    gray = cv2.imread(str(image), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise ValueError(f'image illisible : {image}')
    height, width = gray.shape
    metadata = deepcopy(metadata or {})
    page_reading_uncertain = metadata.get('page_reading_uncertain', metadata.get('uncertain'))
    if page_reading_uncertain is not None and not isinstance(page_reading_uncertain, bool):
        raise ValueError('Incertitude de lecture de page non booléenne')
    rows = deepcopy(list(assignments))
    annotations, seen = [], set()
    for row in rows:
        lid = row.get('line_id', row.get('id'))
        if not isinstance(lid, str) or not lid or lid in seen:
            raise ValueError('identifiants de ligne absents ou dupliqués')
        if row.get('id', lid) != lid:
            raise ValueError(f'identifiants de ligne contradictoires : {lid}')
        if not isinstance(row.get('text'), str):
            raise ValueError(f'texte non textuel : {lid}')
        seen.add(lid)
        assignment_status = row.get('status', 'unknown')
        explicit_resolved = row.get('assignment_resolved')
        if explicit_resolved is not None and not isinstance(explicit_resolved, bool):
            raise ValueError(f'assignment_resolved doit être booléen : {lid}')
        resolved = (explicit_resolved if explicit_resolved is not None
                    else assignment_status in MATCHED_STATUSES)
        assignment_uncertain = bool(row.get('uncertain', False) or not resolved)
        text_view = compact_line_text_view(row['text'])
        annotation = dict(row, id=lid, assignment_status=assignment_status,
                          text=text_view['text'], source_text=row['text'],
                          source_spans=text_view['source_spans'], text_view_transform=text_view['transform'],
                          assignment_resolved=resolved,
                          reading_bbox=deepcopy(row.get('reading_bbox', row.get('detector_bbox', row.get('bbox')))),
                          provider=metadata.get('provider', 'page_markdown'), model=metadata.get('model', 'unknown'),
                          uncertain=bool(assignment_uncertain or page_reading_uncertain is not False),
                          assignment_uncertain=assignment_uncertain,
                          page_reading_uncertain=page_reading_uncertain, reading_certified=False,
                          status='placement_en_attente', geometry_valid=False,
                          training_eligible=False, alto_eligible=False)
        if assignment_uncertain:
            annotation['assignment_resolved'] = False
        for key in ('job_id', 'model_display_terminal'):
            if metadata.get(key):
                annotation['reading_job_id' if key == 'job_id' else key] = metadata[key]
        annotations.append(annotation)
    directory = Path(output_dir) if output_dir is not None else None
    image_sha256 = hashlib.sha256(image.read_bytes()).hexdigest()
    if directory is not None:
        directory.mkdir(parents=True, exist_ok=True)
        # L'intégralité du texte précède toute tentative de placement coûteuse.
        _write_json(directory / 'assignments.json', rows)
        _write_json(directory / 'annotations.json', annotations)
        (directory / 'transcription.txt').write_text('\n'.join(a['source_text'] for a in annotations), encoding='utf-8')
    if boxer is None:
        from boxers.forcectc import ForceCTC
        boxer = ForceCTC(boundary_mode='ink_clean_local', char_alignment='word')
    cache = None
    cache_error = None
    if directory is not None:
        try:
            signature = getattr(boxer, 'cache_signature', None)
            if signature:
                cache = PlacementCache(directory / 'geometry-cache', image_sha256, signature,
                                       dict(page_geometry=IMPLEMENTATION_SHA256,
                                            ink=hashlib.sha256(Path(ink.__file__).read_bytes()).hexdigest(),
                                            correct=hashlib.sha256(Path(correct.__file__).read_bytes()).hexdigest()))
        except (OSError, ValueError) as exc:
            cache_error = str(exc)
    # Point de reprise périodique : réécrire annotations.json (jusqu'à ~20 Mo)
    # après chaque ligne coûtait ~90 % du temps de placement ; le cache par
    # ligne suffit à reprendre une page interrompue.
    last_checkpoint = time.monotonic()
    keys, pending = {}, []
    for index, annotation in enumerate(annotations):
        if cache:
            request = SimpleNamespace(id=annotation['id'], bbox=annotation.get('reading_bbox') or [])
            keys[index] = cache.key(request, SimpleNamespace(**annotation), dict(bbox=annotation.get('bbox')))
            saved = cache.load(keys[index])
            if saved:
                annotations[index] = saved['annotation']
                continue
        pending.append(index)

    def finished(index, annotation):
        nonlocal last_checkpoint
        annotations[index] = annotation
        if cache:
            cache.store(keys[index], annotation, [], [], 0)
        if directory is not None and time.monotonic() - last_checkpoint >= CHECKPOINT_SECONDS:
            _write_json(directory / 'annotations.json', annotations)
            last_checkpoint = time.monotonic()

    workers = _placement_workers(boxer, len(pending))
    if workers > 1:
        # Lignes indépendantes : chaque processus charge l'image et son propre
        # modèle (un fil torch chacun) ; résultats rangés par indice de ligne.
        from concurrent.futures import ProcessPoolExecutor
        import multiprocessing
        spec = dict(model_path=boxer.model_path, fallback_model_path=boxer.fallback_model_path,
                    boundary_mode=boxer.boundary_mode, char_alignment=boxer.char_alignment)
        with ProcessPoolExecutor(workers, mp_context=multiprocessing.get_context('spawn'),
                                 initializer=_worker_init, initargs=(str(image), spec)) as pool:
            for index, annotation in zip(pending, pool.map(_worker_place, [annotations[i] for i in pending],
                                                           chunksize=4)):
                finished(index, annotation)
    else:
        for index in pending:
            annotation = annotations[index]
            try:
                _place(gray, annotation, boxer)
            except Exception as exc:
                annotation.update(status='erreur_geometrie', reason=f'{type(exc).__name__}: {exc}')
            finished(index, annotation)
    threshold = _global_checks(annotations)
    for annotation in annotations:
        annotation['geometry_status'] = annotation['status']
    counts = dict(Counter(a['status'] for a in annotations))
    kept = sum(a['alto_eligible'] for a in annotations)
    report = dict(lines_total=len(annotations), lines_preserved=len(annotations),
                  lines_placed=sum(bool(a.get('words')) for a in annotations), lines_exported=kept,
                  coverage=kept / len(annotations) if annotations else 0, statuses=counts,
                  text_changed=any(a['text'] != a['source_text'] for a in annotations),
                  lexical_text_changed=False, source_text_preserved=True,
                  layout_whitespace_normalized_lines=sum(a['text'] != a['source_text'] for a in annotations),
                  reading_calls=0, criteria_met=False,
                  page_reading_uncertain=page_reading_uncertain, reading_certified=False,
                  ink_suspicion_threshold=round(threshold, 3),
                  coordinate_convention='line bbox: half-open; internal words: inclusive',
                  geometry_cache=dict(hits=cache.hits, saved=cache.saved) if cache else None)
    if cache_error:
        report['geometry_cache_error'] = cache_error
    provenance = dict(image=image.name, image_sha256=image_sha256, taille=[width, height],
                      lecture=metadata.get('provider', 'page_markdown'), geometrie=getattr(boxer, 'name', type(boxer).__name__),
                      lecture_provenance=metadata, lignes_detectees=len(annotations), lignes_retenues=kept,
                      page_reading_uncertain=page_reading_uncertain, reading_certified=False,
                      lignes_ecartees=len(annotations) - kept, lignes_reprises=0,
                      complet=bool(annotations) and kept == len(annotations),
                      cer_zero_certifie=False, olr='non_execute', implementation_sha256=IMPLEMENTATION_SHA256)
    if directory is not None:
        _write_json(directory / 'annotations.json', annotations)
        try:
            xml, validation = _alto_bytes(image, width, height, annotations, provenance['geometrie'])
            (directory / 'page.alto.xml').write_bytes(xml)
            report['alto_validation'] = validation
        except Exception as exc:
            # Un problème XML ne détruit ni la VT ni les diagnostics sauvegardés.
            report['alto_validation'] = dict(valid=False, error=str(exc))
            (directory / 'page.alto.xml').unlink(missing_ok=True)
        _write_json(directory / 'geometry-report.json', report)
        _write_json(directory / 'provenance.json', provenance)
    return dict(annotations=annotations, report=report, provenance=provenance)
