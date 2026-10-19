"""Réparer les seuls intervalles CTC hors des mots d'un essai d'encre.

Le texte, les mots, leurs boîtes et l'ordre restent intacts. La source native,
le crop, le modèle et les anciens intervalles accompagnent chaque tentative.
L'absence de chemin physique conserve le rejet, jamais une largeur inventée.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re
from types import SimpleNamespace

import cv2


VERSION = 'word-character-realignment-after-foreign-components-v1'


def repair(gray, annotations, align_word, word_exclusions=None):
    """``align_word(model_path,text,crop)`` rend positions + provenance CTC."""
    rows = deepcopy(annotations)
    exclusions = {(item['line_id'], item['word_index']): deepcopy(item) for item in word_exclusions or []}
    decisions = []
    for annotation in rows:
        text, chars = annotation['text'], annotation.get('chars') or []
        if len(chars) != len(text):
            continue
        for wi, (token, word) in enumerate(zip(re.finditer(r'\S+', text), annotation.get('words') or [])):
            start, end = token.span()
            if token.group() != word['text']:
                raise ValueError('Texte et mots incohérents : ' + annotation['id'])
            if not any(chars[i][0] < word['x0'] or chars[i][1] > word['x1']+1 for i in range(start, end)):
                continue
            source = annotation['reading_bbox']
            crop = [word['x0'], source[1], word['x1']+1, source[3]]
            model_path = (annotation.get('alignment') or {}).get('model_path')
            previous = deepcopy(chars[start:end])
            decision = dict(line_id=annotation['id'], word_index=wi, text=token.group(), start=start, end=end,
                            source_box=crop, previous=previous, model_path=model_path, accepted=False,
                            raw_input_sha256=hashlib.sha256(gray[crop[1]:crop[3], crop[0]:crop[2]].tobytes()).hexdigest(),
                            raw_input_shape=[crop[3]-crop[1], crop[2]-crop[0]], raw_input_dtype=str(gray.dtype))
            try:
                exclusion = exclusions.get((annotation['id'], wi))
                if exclusion:
                    if exclusion['text'] != token.group():
                        raise ValueError('Audit source et mot différents')
                    decision['source_audit_exclusion'] = exclusion
                    raise ValueError('Rejet documenté sur image source : ' + exclusion['reason'])
                if not model_path:
                    raise ValueError('Modèle historique absent')
                result = align_word(model_path, token.group(), crop)
                decision['ctc_attempt'] = deepcopy(result)
                if result.get('error'):
                    raise ValueError(result['error'])
                positions = result['positions']
                if result['alignment'].get('model_path') != model_path:
                    raise ValueError('Le modèle effectif diffère du modèle historique')
                if len(positions) != end-start or any(
                        not isinstance(c, (list, tuple)) or len(c) != 3
                        or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in c)
                        or not (crop[0] <= c[0] < c[1] <= crop[2] and 0 <= c[2] <= 1) for c in positions):
                    raise ValueError('Caractère nul, hors du crop ou incohérent')
                chars[start:end] = deepcopy(positions)
                decision.update(accepted=True, positions=deepcopy(positions), reason='same_model_native_word_ctc')
                alignment = annotation['alignment']
                sources = alignment.setdefault('character_position_sources', ['historical_ctc']*len(text))
                if len(sources) != len(text):
                    raise ValueError('Provenance historique de caractères incohérente')
                for i in range(start, end):
                    sources[i] = 'word_ctc_after_foreign_ink_removal; native_frames_only'
            except Exception as exc:
                # Si la réparation n'est pas entièrement validée, ne conserver
                # aucun intervalle partiel ni fabriquer de support physique.
                chars[start:end] = previous
                decision.update(accepted=False, reason=f'{type(exc).__name__}: {exc}')
                annotation['character_status'] = 'repositionnement_caracteres_non_resolu'
                if annotation.get('training_eligible'):
                    annotation['previous_geometry_status'] = annotation['status']
                    annotation['status'] = annotation['character_status']
                annotation['training_eligible'] = False
                annotation['alto_eligible'] = False
            annotation.setdefault('character_realignments', []).append(deepcopy(decision))
            decisions.append(decision)
    assert [(a['id'], a['text'], a.get('words'), a.get('bbox'), a.get('source_text')) for a in rows] == [
        (a['id'], a['text'], a.get('words'), a.get('bbox'), a.get('source_text')) for a in annotations]
    unresolved = [dict(line_id=a['id'], word=w['text'], index=i, position=a['chars'][i])
        for a in rows if len(a.get('chars') or []) == len(a['text'])
        for token, w in zip(re.finditer(r'\S+', a['text']), a.get('words') or [])
        for i in range(token.start(), token.end())
        if a['chars'][i][0] < w['x0'] or a['chars'][i][1] > w['x1']+1]
    return dict(annotations=rows, decisions=decisions, unresolved=unresolved,
                source_text_and_word_geometry_unchanged=True, promoted=False, criteria_met=False)


def replay(image, directory, output, word_exclusions=None):
    from boxers import forcectc
    from native_frame_ctc import source_frame_alignment
    image, directory, output = Path(image), Path(directory), Path(output)
    raw_path = directory/'candidate-annotations.json'
    annotations = json.loads(raw_path.read_text())
    source_provenance = json.loads((directory/'provenance.json').read_text())
    image_sha256 = hashlib.sha256(image.read_bytes()).hexdigest()
    if source_provenance['image_sha256'] != image_sha256:
        raise ValueError('Image différente de l’essai source')
    gray = cv2.imread(str(image), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise ValueError('Image native illisible')
    models = {}
    def align_word(model_path, text, crop):
        model_hash = hashlib.sha256(Path(model_path).read_bytes()).hexdigest()
        boxer = models.setdefault(model_path, forcectc.ForceCTC(model_path=model_path))
        error = None
        with source_frame_alignment(forcectc) as frames:
            try:
                boxer.align(gray, SimpleNamespace(text=text, line_box=tuple(crop)))
            except Exception as exc:
                error = f'{type(exc).__name__}: {exc}'
        return dict(positions=deepcopy(boxer.last_char_positions), alignment=deepcopy(boxer.last_alignment),
                    source_frame_constraint=deepcopy(frames), model_sha256=model_hash,
                    forcectc_implementation_sha256=forcectc.IMPLEMENTATION_SHA256, error=error)
    exclusions = json.loads(Path(word_exclusions).read_text()) if word_exclusions else []
    result = repair(gray, annotations, align_word, exclusions)
    output.mkdir(parents=True, exist_ok=True)
    (output/'candidate-annotations.json').write_text(json.dumps(result['annotations'], ensure_ascii=False, indent=2))
    (output/'character-realignment-audit.json').write_text(json.dumps({k: v for k, v in result.items() if k != 'annotations'}, ensure_ascii=False, indent=2))
    summary = dict(version=VERSION, lines=len(annotations), words_attempted=len(result['decisions']),
        words_realigned=sum(d['accepted'] for d in result['decisions']), unresolved_characters=len(result['unresolved']),
        ctc_calls=sum('ctc_attempt' in d for d in result['decisions']),
        source_audit_rejections=sum('source_audit_exclusion' in d for d in result['decisions']),
        retained=sum(bool(a.get('training_eligible')) for a in result['annotations']),
        reading_calls=0, source_text_and_word_geometry_unchanged=True, promoted=False, criteria_met=False)
    (output/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    (output/'provenance.json').write_text(json.dumps(dict(image_sha256=image_sha256,
        source_directory=str(directory.resolve()), source_annotations_sha256=hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_frame_implementation_sha256=hashlib.sha256(Path(__file__).with_name('native_frame_ctc.py').read_bytes()).hexdigest(),
        reference_inputs=False, promoted=False), indent=2))
    return summary


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('image')
    parser.add_argument('directory')
    parser.add_argument('output')
    parser.add_argument('--word-exclusions')
    args = parser.parse_args()
    print(json.dumps(replay(args.image, args.directory, args.output, args.word_exclusions), ensure_ascii=False, indent=2))
