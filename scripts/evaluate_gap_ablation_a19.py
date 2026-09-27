"""A19: fixed no-CTC ablation on SBB audit pages and cached predicted VLM lines.

SBB uses reference line polygons/text (conditional geometry only). Spiritualist
uses predicted line geometry and cached VLM text, but has no valid word GT.
Neither branch is an independent superiority test. No setting is tuned here.
"""
from pathlib import Path
import json
import time
import hashlib
import numpy as np
import cv2
from lxml import etree as E
from bbvlm.gap_alignment import locate_words_without_recognizer
from bbvlm.metrics import iou
from audit_sbb_reference_a18 import box, txt

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'experiments/loop/reference-a18'
OUT = ROOT / 'experiments/loop/gap-ablation-a19'
CONFIG = {'min_gap_height_ratio': .10, 'gap_separation_ratio': 1.5}


def polygon(line):
    return [list(map(float, p.split(','))) for p in line.find('{*}Coords').get('points').split()]


def main():
    OUT.mkdir(exist_ok=True)
    (OUT/'config.json').write_text(json.dumps({'parameters': CONFIG,
      'frozen_before_measurement': True, 'selection': 'mechanistic single setting, no tuning',
      'reference_scope': 'audit/development; four reserve books remain unopened'}, indent=2))
    split = json.loads((BASE/'split.json').read_text())
    rows = []
    for page in split['pages']:
        if page['role'] != 'audit':
            continue
        gray = cv2.imread(str(BASE/'source'/page['image']), cv2.IMREAD_GRAYSCALE)
        root = E.parse(str(BASE/'source'/page['xml']))
        for line in root.findall('.//{*}TextLine'):
            tokens = txt(line).split()
            if not tokens:
                continue
            start = time.perf_counter()
            prediction = locate_words_without_recognizer(gray, polygon(line), box(line), tokens, **CONFIG)
            duration = time.perf_counter()-start
            # Only now inspect reference words. Word XML is not an inference input.
            words = line.findall('{*}Word')
            compatible = [txt(w) for w in words] == tokens
            scores = [iou(b, box(w)) for b, w in zip(prediction['boxes'], words)] if compatible else []
            rows.append({'work': page['work'], 'line': line.get('id'), 'tokens': len(tokens),
                         'word_reference_count': len(words), 'tokenization_compatible': compatible,
                         'prediction': prediction, 'ious': scores, 'cpu_seconds': duration})
    compatible = [r for r in rows if r['tokenization_compatible']]
    emitted = [r for r in compatible if r['prediction']['boxes']]
    scores = [v for r in emitted for v in r['ious']]
    denominator = sum(r['word_reference_count'] for r in compatible)
    cached = ROOT/'experiments/loop/spiritualist-v1/predicted-alignment-a15-0044/package/document.json'
    graph = json.loads(cached.read_text())
    gray = cv2.imread(str(ROOT/'corpora/spiritualist/companion/Spiritualist_Images/0044.png'), cv2.IMREAD_GRAYSCALE)
    diagnostic = []
    for line in [n for n in graph['nodes'] if n['kind'] == 'line']:
        start = time.perf_counter()
        pred = locate_words_without_recognizer(gray, line['polygon'], line['bbox'], line['text'].split(), **CONFIG)
        diagnostic.append({'line': line['id'], 'prediction': pred,
                           'cpu_seconds': time.perf_counter()-start})
    report = {'schema': 'bbvlm.no-recognizer-ablation/1', 'config': CONFIG,
      'sbb_conditional_geometry': {'lines': len(rows), 'compatible_lines': len(compatible),
        'tokenization_incompatible_lines': len(rows)-len(compatible),
        'proposed_lines': len(emitted), 'reference_words_compatible': denominator,
        'emitted_words_compatible': len(scores),
        'emitted_words_iou_lt50': sum(v<.5 for v in scores),
        'proposed_lines_with_any_iou_lt50': sum(any(v<.5 for v in r['ious']) for r in emitted),
        'proposed_lines_all_words_iou_ge80': sum(all(v>=.8 for v in r['ious']) for r in emitted),
        'mean_iou_emitted': float(np.mean(scores)) if scores else None,
        'word_recall_iou50_including_abstentions': sum(v>=.5 for v in scores)/denominator if denominator else None,
        'word_recall_iou80_including_abstentions': sum(v>=.8 for v in scores)/denominator if denominator else None,
        'cpu_seconds': sum(r['cpu_seconds'] for r in rows)},
      'predicted_vlm_lines_diagnostic': {'lines': len(diagnostic),
        'proposed_lines': sum(bool(r['prediction']['boxes']) for r in diagnostic),
        'cpu_seconds': sum(r['cpu_seconds'] for r in diagnostic),
        'word_geometry_ground_truth_available': False},
      'new_passes': {'vlm': 0, 'layout': 0, 'recognizer': 0},
      'accepted_for_project_completion_gate': False,
      'cost_warning': 'No recognizer was invoked. Actual end-to-end cost saving is not measured: fallback batch costs and VLM latency/tokens require a controlled run.',
      'limitations': ['SBB line geometry and text are oracle inputs, not end-to-end',
        'source polygon vertex extents are compared as continuous rectangles; pixel-tight proposals use half-open pixel bounds; one-pixel convention differences are not adjudicated',
        'SBB word conventions require visual audit; no PERO baseline rerun on this corpus',
        'word count/gap separation does not validate transcription or word ownership',
        'unmatched tokenization reported separately; cannot hide it in a global recall',
        'all inspected pages are development/audit; reserve remains unseen'],
      'source_code_sha256': hashlib.sha256((ROOT/'src/bbvlm/gap_alignment.py').read_bytes()).hexdigest(),
      'per_line_sbb': rows, 'per_line_predicted': diagnostic}
    (OUT/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if not k.startswith('per_line')}, indent=2))


if __name__ == '__main__':
    main()
