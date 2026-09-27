"""A35 consumed-data ablation: A32 on recognized rather than oracle words."""
import hashlib
import json
import time
from pathlib import Path

import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment

import evaluate_french_holdout_a25 as core
from bbvlm.component_boxes import PARAMETERS, refine_cells
from bbvlm.metrics import iou
from bbvlm.ocr_conventions import transform

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'experiments/loop'
OUT = BASE / 'native-refinement-a35'
DATASETS = ('french-word-gt-a28', 'word-transfer-a34')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact(metric):
    return {k: v for k, v in metric.items() if k != 'per_line'}


def pairs(reference, prediction):
    if not reference or not prediction:
        return []
    matrix = np.array([[iou(a['bbox'], b['bbox']) for b in prediction] for a in reference])
    a, b = linear_sum_assignment(-matrix)
    return list(zip(a.tolist(), b.tolist()))


def joint_metrics(rows, prediction):
    """Same geometry assignment for joint text+box score; never reorder text."""
    exact = at50 = at80 = total = 0
    for row in rows:
        gt, pr = row['words'], prediction[row['id']]
        total += len(gt)
        for gi, pi in pairs(gt, pr):
            same = transform(gt[gi]['text'], 'glyph_decomposition_v1') == transform(pr[pi]['text'], 'glyph_decomposition_v1')
            overlap = iou(gt[gi]['bbox'], pr[pi]['bbox'])
            exact += same
            at50 += same and overlap >= .5
            at80 += same and overlap >= .8
    if not total:
        raise ValueError('empty reference')
    return {'reference_words': total, 'exact_text_assigned': exact,
            'exact_text_and_iou50': at50, 'exact_text_and_iou80': at80,
            'recall_exact_text_and_iou50': at50 / total,
            'recall_exact_text_and_iou80': at80 / total,
            'text_convention': 'glyph_decomposition_v1; diagnostic, not Gallica normalization'}


def main():
    start = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    protected = [ROOT / 'src/bbvlm/component_boxes.py', Path(__file__)]
    for name in DATASETS:
        source = BASE / name
        split = json.loads((source / 'split.json').read_text())
        protected += [source / 'split.json', source / 'output/boxes.json', source / 'output/report.json']
        protected += [source / 'source' / p[k] for p in split['pages'] for k in ('xml', 'image')]
    before = {str(p.relative_to(ROOT)): digest(p) for p in protected}
    (OUT / 'seal.json').write_text(json.dumps({'status': 'consumed_diagnostic_not_independent',
        'parameters_unchanged': PARAMETERS, 'input_sha256': before}, indent=2))
    reports, all_predictions, all_cases = {}, {}, []
    for name in DATASETS:
        source = BASE / name
        split = json.loads((source / 'split.json').read_text())
        core.SOURCE = source / 'source'
        rows, paths = core.load_rows(split)
        previous = json.loads((source / 'output/boxes.json').read_text())
        native = previous['native']
        assert set(native) == {r['id'] for r in rows}
        images = {p: cv2.imread(str(path), cv2.IMREAD_GRAYSCALE) for p, path in paths.items()}
        assert all(im is not None for im in images.values())
        predictions = {'native': native, 'native_otsu': {}, 'native_a32': {}}
        timing = {}
        for method in ('native_otsu', 'native_a32'):
            tick = time.perf_counter()
            for row in rows:
                words = native[row['id']]
                boxes = [w['bbox'] for w in words]
                if method == 'native_otsu':
                    revised = core.raw_otsu_boxes(images[row['page']], row['line_bbox'], boxes)
                else:
                    revised, _ = refine_cells(images[row['page']], row['line_bbox'], boxes, 'satellites')
                assert len(revised) == len(words)
                predictions[method][row['id']] = [{'text': w['text'], 'bbox': b} for w, b in zip(words, revised)]
            timing[method] = time.perf_counter() - tick
        # Oracle-text comparator is labelled, never fed to the native variants.
        if name == 'french-word-gt-a28':
            oracle = json.loads((BASE / 'component-boxes-a32/boxes.json').read_text())['satellites']
        else:
            oracle = previous['satellites']
        scored = {**predictions, 'oracle_text_a32': oracle}
        metrics = {m: compact(core.box_metrics(rows, p, m, False)) for m, p in scored.items()}
        joint = {m: joint_metrics(rows, p) for m, p in predictions.items()}
        fixed = []
        for row in rows:
            lid = row['id']
            assert all([w['text'] for w in predictions[m][lid]] == [w['text'] for w in native[lid]] for m in predictions)
            for gi, pi in pairs(row['words'], native[lid]):
                gt, old, new = row['words'][gi], native[lid][pi], predictions['native_a32'][lid][pi]
                a, b = iou(gt['bbox'], old['bbox']), iou(gt['bbox'], new['bbox'])
                item = {'dataset': name, 'line': lid, 'page': row['page'], 'reference_index': gi,
                        'prediction_index': pi, 'reference_text': gt['text'], 'predicted_text': old['text'],
                        'reference': gt['bbox'], 'native': old['bbox'], 'refined': new['bbox'],
                        'old_iou': a, 'new_iou': b, 'delta': b-a}
                fixed.append(item)
        all_cases.extend(fixed)
        by_page = {}
        for page in paths:
            subset = [r for r in rows if r['page'] == page]
            by_page[page] = {m: compact(core.box_metrics(subset, p, m, False)) for m, p in predictions.items()}
        oldcost = json.loads((source / 'output/report.json').read_text())['cost']
        reports[name] = {'counts': {'pages': len(paths), 'lines': len(rows),
            'reference_words': sum(len(r['words']) for r in rows),
            'recognized_words': sum(len(w) for w in native.values()),
            'lines_token_count_differs': sum(len(r['words']) != len(native[r['id']]) for r in rows),
            'empty_recognized_lines': sum(not native[r['id']] for r in rows)},
            'geometry': metrics, 'joint_text_geometry': joint, 'by_page': by_page,
            'fixed_native_assignment': {'pairs': len(fixed),
                'improved': sum(x['delta'] > 1e-9 for x in fixed),
                'regressed': sum(x['delta'] < -1e-9 for x in fixed),
                'regressions_over_0_1': sum(x['delta'] < -.1 for x in fixed),
                'mean_delta_iou': float(np.mean([x['delta'] for x in fixed]))},
            'cost': {'incremental_cpu_seconds': timing, 'new_vlm_passes': 0,
                'new_recognizer_forwards': 0,
                'historical_recognizer_seconds': oldcost['recognition_seconds'],
                'historical_recognizer_forwards': oldcost['recognizer_forwards'],
                'warning': 'Recognition cache remains a paid computational prerequisite; native ALTO export cost not separately metered.'}}
        all_predictions[name] = predictions
    after = {str(p.relative_to(ROOT)): digest(p) for p in protected}
    assert before == after
    report = {'schema': 'bbvlm.native-refinement-a35/1', 'status': 'consumed_diagnostic_completed',
        'hypothesis': 'A32 gain persists without oracle transcription or oracle token count',
        'scope': 'Native recognized text and boxes; still oracle lines and synthetic baselines',
        'datasets': reports, 'invariants': {'protected_inputs_unchanged': True,
            'native_text_order_cardinality_preserved': True, 'no_gt_word_boxes_or_text_in_refiner': True,
            'no_new_inference': True, 'no_reference_replacement': True},
        'total_seconds': time.perf_counter()-start, 'accepted_for_project_completion_gate': False}
    for filename, data in [('report.json', report), ('boxes.json', all_predictions),
                           ('fixed-assignment-cases.json', all_cases)]:
        (OUT / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({name: {'counts': r['counts'], 'geometry': r['geometry'],
        'joint': r['joint_text_geometry'], 'paired': r['fixed_native_assignment'], 'cost': r['cost']}
        for name, r in reports.items()}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
