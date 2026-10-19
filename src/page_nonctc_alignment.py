"""Ablation source-only de deux boxers sans réseau OCR ni alignement CTC.

Les méthodes historiques ne sont pas changées. Le wrapper refuse leurs secours
sans observation d'encre et conserve exactement le texte et ses offsets.
Une géométrie calculée reste un diagnostic non certifié, jamais du training.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sys
from types import SimpleNamespace

import numpy as np

import ink


VERSION = 'nonctc-observed-ink-ablation-v1'
BOXERS = Path(__file__).resolve().parent/'boxers'


def tokens_with_offsets(text):
    return [dict(text=m.group(), start=m.start(), end=m.end()) for m in re.finditer(r'\S+', text)]


def align_crop(gray, text, method, *, backend=None):
    """Boîtes inclusives dans le crop ; aucun retour aux coordonnées natives ici."""
    if method not in {'dtw_snap', 'inkgap_dp'}:
        raise ValueError('Méthode sans CTC inconnue')
    if not isinstance(text, str):
        raise TypeError('La transcription figée doit être une chaîne')
    tokens = tokens_with_offsets(text)
    result = dict(version=VERSION, method=method, text=text,
        text_sha256=hashlib.sha256(text.encode()).hexdigest(), tokens=tokens,
        words=[], status='not_run', training_eligible=False, reading_certified=False,
        glyphs_certified=False, ctc_calls=0, recognition_calls=0, fallback_used=False)
    if gray.ndim != 2 or gray.size == 0 or not tokens:
        return dict(result, status='invalid_crop_or_empty_text')
    height, width = gray.shape
    box = [0, 0, width, height]
    mask, ox, oy = ink.line_mask(gray, box)
    runs = ink.x_runs(mask, ink.line_scale(box)['run_area_min'])
    result['ink'] = dict(pixels=int(np.count_nonzero(mask)), horizontal_runs=len(runs),
                         mask_origin=[ox, oy], shape=list(mask.shape))
    if not np.any(mask):
        return dict(result, status='no_observed_ink')
    if method == 'inkgap_dp' and len(runs) < len(tokens):
        # partition() répartirait sinon les mots proportionnellement aux fontes.
        return dict(result, status='proportional_fallback_forbidden')
    line = SimpleNamespace(words=[t['text'] for t in tokens], text=text, line_box=box)
    if backend is None:
        sys.path.insert(0, str(BOXERS))
        if method == 'dtw_snap':
            from dtwsnap import DTWSnap
            backend = DTWSnap()
        else:
            from inkgap import InkGapDP
            backend = InkGapDP()
    try:
        boxes = backend.boxes(gray, line)
    except Exception as exc:
        return dict(result, status='algorithm_failed', error_type=type(exc).__name__, error=str(exc))
    if len(boxes) != len(tokens):
        return dict(result, status='word_count_mismatch')
    previous_right = -1
    for token, coords in zip(tokens, boxes):
        coords = np.asarray(coords, float)
        if coords.shape != (4,) or not np.isfinite(coords).all() or not np.equal(coords, np.rint(coords)).all():
            return dict(result, status='invalid_word_geometry')
        x0, y0, x1, y1 = map(int, coords)
        if not (0 <= x0 <= x1 < width and 0 <= y0 <= y1 < height) or x0 <= previous_right:
            return dict(result, status='invalid_or_overlapping_word_geometry')
        local = mask[y0-oy:y1-oy+1, x0-ox:x1-ox+1]
        if not np.any(local):
            # DTWSnap conserve normalement sa boîte brute dans ce cas.
            return dict(result, words=[], status='word_interval_without_observed_ink')
        result['words'].append(dict(token, bbox=[x0, y0, x1, y1], observed_ink_pixels=int(np.count_nonzero(local))))
        previous_right = x1
    return dict(result, status='geometry_observed_unvalidated')


def implementation_provenance():
    files = [Path(__file__), Path(ink.__file__), *(BOXERS/name for name in ('dtwsnap.py', 'dtw.py', 'band.py', 'inkgap.py'))]
    return {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
