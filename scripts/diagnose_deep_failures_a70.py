"""Classify A69 <50% line-coverage residuals without new inference."""
import hashlib, json, time
from collections import Counter
from pathlib import Path

from shapely.geometry import box
from shapely.ops import unary_union

from evaluate_transfer_a69 import ROOT, parse_xml

OUT = ROOT / 'experiments/loop/next-a70'
A69 = ROOT / 'experiments/loop/next-a69'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    started = time.perf_counter()
    candidates = json.loads((A69/'candidates.json').read_text())['pages']
    split = json.loads((A69/'split.json').read_text())['pages']
    expected = {r['file']: r['sha256'] for r in json.loads(
        (ROOT/'experiments/loop/chronicling-a58/audit.json').read_text())['files_detail']}
    rows = []
    for page in split:
        _, lines, xml_hash = parse_xml(page, expected)
        boxes = [(box(*r['bbox']), r['class_name']) for r in candidates[page]['native']]
        all_union = unary_union([b for b, _ in boxes])
        for line_id, line in lines:
            coverages = [line.intersection(b).area/line.area for b, _ in boxes]
            best = max(coverages, default=0.0)
            if best >= .5:
                continue
            union_coverage = line.intersection(all_union).area/line.area
            contributors = [(i, c, boxes[i][1]) for i, c in enumerate(coverages) if c >= .01]
            if union_coverage >= .95:
                category = 'fragmented_recoverable'
            elif union_coverage >= .5:
                category = 'fragmented_partial'
            else:
                category = 'miss_or_convention'
            rows.append({
                'page': page, 'line_id': line_id, 'xml_sha256': xml_hash,
                'best_single_coverage': best, 'union_coverage': union_coverage,
                'contributors': [{'box_index': i, 'coverage': c, 'class_name': name}
                                 for i, c, name in contributors],
                'category': category,
            })
    counts = Counter(r['category'] for r in rows)
    pages = Counter(r['page'] for r in rows)
    contributor_counts = Counter(min(len(r['contributors']), 4) for r in rows)
    report = {
        'status': 'consumed_failure_attribution_not_validation',
        'source_candidate_sha256': sha(A69/'candidates.json'),
        'source_predictions_sha256': sha(A69/'predictions.json'),
        'deep_failures': len(rows), 'categories': dict(counts),
        'pages': dict(pages), 'contributors_capped_at4': dict(contributor_counts),
        'rows': rows, 'new_model_forwards': 0, 'ocr_calls': 0, 'vlm_calls': 0,
        'test_pages_opened': 0, 'seconds': time.perf_counter()-started,
        'all_scientific_gates_passed': False,
        'limitations': [
            'A69 Training pages are consumed and A58 already audited their XML.',
            'Union coverage can identify fragmentation but not semantic ownership.',
            'PAGE line polygons and detector rectangles are not perfect ALTO truth.'
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'report-v2.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('deep_failures','categories','pages','contributors_capped_at4')}, indent=2))


if __name__ == '__main__':
    main()
