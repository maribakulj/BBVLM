"""A16: one frozen, additive ink-extension diagnostic on consumed page 0044.

This reads no reference transcript or reference geometry.  It diagnoses the
specific A15 failure in which visible terminal ink fell outside a native CTC
word interval.  Page 0044 is already consumed and cannot validate selection.
"""
from copy import deepcopy
from pathlib import Path
import json

import cv2
import numpy as np

from bbvlm import document as D
from bbvlm.__main__ import export_package
from bbvlm.refine import (extend_words_to_foreground, prepare_line_foreground,
                          select_edge_punctuation_extensions)


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'experiments/loop/spiritualist-v1'
SOURCE = BASE / 'predicted-alignment-a15-0044/package/document.json'
IMAGE = ROOT / 'corpora/spiritualist/companion/Spiritualist_Images/0044.png'
OUT = BASE / 'ink-extension-a16c-0044'
CONFIG = {
    'schema': 'bbvlm.ink-extension-config/1',
    'candidate': 'A16c',
    'binarization': 'otsu',
    'min_component_area': 2,
    'max_gap_height_ratio': .35,
    'margin_pixels': 0,
    'external_centroids_only': True,
    'edge_punctuation_only': True,
    'selection': 'edge-punctuation routing after A16a/A16b over-expansion; no grid search',
    'scope': 'consumed A15 partial-page diagnostic; never an independent gate',
}


def _rect_mask(shape, boxes, ox, oy):
    mask = np.zeros(shape, np.uint8)
    for box in boxes:
        x0 = max(0, int(np.floor(box[0] - ox)))
        y0 = max(0, int(np.floor(box[1] - oy)))
        x1 = min(shape[1], int(np.ceil(box[2] - ox)))
        y1 = min(shape[0], int(np.ceil(box[3] - oy)))
        if x1 > x0 and y1 > y0:
            mask[y0:y1, x0:x1] = 1
    return mask


def _overlaps(boxes):
    count = 0
    for a, b in zip(boxes, boxes[1:]):
        if min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1]):
            count += 1
    return count


def _overlay(image, region, native, candidate, path):
    x0, y0, x1, y1 = [int(round(v)) for v in region['bbox']]
    pad = 20
    x0, y0 = max(0, x0-pad), max(0, y0-pad)
    x1, y1 = min(image.shape[1], x1+pad), min(image.shape[0], y1+pad)
    crop = image[y0:y1, x0:x1].copy()
    for box in native:
        a = (int(round(box[0]-x0)), int(round(box[1]-y0)))
        b = (int(round(box[2]-x0)), int(round(box[3]-y0)))
        cv2.rectangle(crop, a, b, (20, 20, 230), 1)
    for box in candidate:
        a = (int(round(box[0]-x0)), int(round(box[1]-y0)))
        b = (int(round(box[2]-x0)), int(round(box[3]-y0)))
        cv2.rectangle(crop, a, b, (20, 180, 20), 1)
    cv2.imwrite(str(path), crop, [cv2.IMWRITE_JPEG_QUALITY, 92])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # The parameter record is written before any result is calculated.
    (OUT / 'config.json').write_text(json.dumps(CONFIG, indent=2) + '\n')
    graph = D.load(SOURCE)
    candidate_graph = deepcopy(graph)
    gray = cv2.imread(str(IMAGE), cv2.IMREAD_GRAYSCALE)
    color = cv2.imread(str(IMAGE), cv2.IMREAD_COLOR)
    if gray is None or color is None:
        raise FileNotFoundError(IMAGE)
    source_ix = D.index(graph)
    candidate_ix = D.index(candidate_graph)
    per_word, per_line = [], []
    total_native_ink = total_candidate_ink = total_line_ink = 0
    total_added_pixels = total_added_ink = 0
    native_overlap = candidate_overlap = 0
    region_native, region_candidate = {}, {}

    for line in [n for n in graph['nodes'] if n['kind'] == 'line']:
        words = sorted(D.children(graph, line['id'], 'word'), key=lambda n: (n['bbox'][0], n['id']))
        native = [w['bbox'] for w in words]
        candidate, audit = extend_words_to_foreground(
            gray, native, line['polygon'], line['bbox'],
            min_area=CONFIG['min_component_area'],
            binarization=CONFIG['binarization'],
            max_gap_height_ratio=CONFIG['max_gap_height_ratio'],
            margin=CONFIG['margin_pixels'],
            external_centroids_only=CONFIG['external_centroids_only'])
        candidate, decisions = select_edge_punctuation_extensions(
            [w.get('text', '') for w in words], native, candidate)
        for record, decision, selected in zip(audit, decisions, candidate):
            record['raw_candidate_box'] = record['candidate_box']
            record['candidate_box'] = selected
            record.update(decision)
            record['changed'] = decision['selected']
        fg, ox, oy = prepare_line_foreground(gray, line['polygon'], line['bbox'], CONFIG['binarization'])
        nm = _rect_mask(fg.shape, native, ox, oy)
        cm = _rect_mask(fg.shape, candidate, ox, oy)
        added = (cm == 1) & (nm == 0)
        native_ink = int(np.count_nonzero((fg > 0) & (nm > 0)))
        candidate_ink = int(np.count_nonzero((fg > 0) & (cm > 0)))
        line_ink = int(np.count_nonzero(fg > 0))
        added_pixels = int(np.count_nonzero(added))
        added_ink = int(np.count_nonzero((fg > 0) & added))
        total_native_ink += native_ink
        total_candidate_ink += candidate_ink
        total_line_ink += line_ink
        total_added_pixels += added_pixels
        total_added_ink += added_ink
        native_overlap += _overlaps(native)
        candidate_overlap += _overlaps(candidate)
        for word, box, record in zip(words, candidate, audit):
            candidate_ix[word['id']]['bbox'] = box
            per_word.append(dict(record, id=word['id'], text=word.get('text', ''),
                                 line_id=line['id']))
        per_line.append({
            'id': line['id'], 'source_id': line.get('source_id'),
            'words': len(words), 'changed_words': sum(r['changed'] for r in audit),
            'native_ink_coverage': native_ink / line_ink if line_ink else None,
            'candidate_ink_coverage': candidate_ink / line_ink if line_ink else None,
            'added_pixels': added_pixels, 'added_ink_pixels': added_ink,
        })
        region_native.setdefault(line['parent'], []).extend(native)
        region_candidate.setdefault(line['parent'], []).extend(candidate)

    # The diplomatic layer and every stable node ID must be untouched.
    assert [n['id'] for n in graph['nodes']] == [n['id'] for n in candidate_graph['nodes']]
    assert [(n['id'], n.get('text')) for n in graph['nodes'] if n['kind'] in {'line', 'word'}] == [
        (n['id'], n.get('text')) for n in candidate_graph['nodes'] if n['kind'] in {'line', 'word'}]
    assert all(c[0] <= n[0] and c[1] <= n[1] and c[2] >= n[2] and c[3] >= n[3]
               for n, c in zip([w['native_box'] for w in per_word],
                               [w['candidate_box'] for w in per_word]))
    candidate_graph['events'].append({
        'type': 'additive_word_ink_extension_a16c',
        'source': 'A15 native PERO CTC word boxes plus source-image foreground',
        'parameters': CONFIG,
        'warning': 'diagnostic on consumed page; automatic geometry, not verified ground truth',
    })
    package = export_package(candidate_graph, OUT / 'package', ROOT / 'schemas')
    for rid, boxes in region_native.items():
        region = source_ix[rid]
        _overlay(color, region, boxes, region_candidate[rid], OUT / f'{rid}.overlay.jpg')

    changed = [w for w in per_word if w['changed']]
    punctuation = [w for w in per_word if w['text'] and not w['text'][-1].isalnum()]
    report = {
        'schema': 'bbvlm.ink-extension-report/1',
        'status': 'diagnostic_complete_not_ground_truth',
        'scope': CONFIG['scope'], 'reference_inputs': False,
        'parameters': CONFIG, 'lines': len(per_line), 'words': len(per_word),
        'changed_words': len(changed),
        'changed_terminal_punctuation_words': sum(w['changed'] for w in punctuation),
        'terminal_punctuation_words': len(punctuation),
        'native_line_foreground_coverage': total_native_ink / total_line_ink,
        'candidate_line_foreground_coverage': total_candidate_ink / total_line_ink,
        'coverage_gain_points': 100 * (total_candidate_ink - total_native_ink) / total_line_ink,
        'added_rectangle_pixels': total_added_pixels,
        'added_foreground_pixels': total_added_ink,
        'added_area_foreground_precision': total_added_ink / total_added_pixels if total_added_pixels else None,
        'native_adjacent_word_overlaps': native_overlap,
        'candidate_adjacent_word_overlaps': candidate_overlap,
        'containment_invariant': True, 'text_and_id_invariant': True,
        'new_layout_passes': 0, 'new_recognition_passes': 0, 'new_vlm_passes': 0,
        'package': package,
        'accepted_for_project_completion_gate': False,
        'limitations': [
            '0044 and A15 are consumed diagnostics, not an independent validation set',
            'foreground coverage measures thresholded ink, not semantic ownership or exact box truth',
            'rectangles necessarily include background and may absorb nearby rule/noise',
            'visual or independent geometry adjudication is required before promotion',
        ],
        'per_line': per_line, 'per_word': per_word,
    }
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in {'per_line', 'per_word'}}, indent=2))


if __name__ == '__main__':
    main()
