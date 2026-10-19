#!/usr/bin/env python
"""Compare deux modèles sur les MÊMES planches de lignes (évaluation seulement).

Chaque ligne détectée est rapprochée de la ligne de référence qu'elle recouvre
(IoU >= 0,5, une seule) ; erreurs cer_vt de chaque modèle contre cette ligne.
Rapporte aussi durées et tokens tracés par ``line_reader.ask``.
"""
import argparse
import json
from pathlib import Path
import statistics
import sys

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from evaluation import cer_vt, lev, iou, _points
from page_reference_text import load_page_reference

parser = argparse.ArgumentParser()
parser.add_argument('manifest')
parser.add_argument('page_id_or_sha')
parser.add_argument('annotations')
parser.add_argument('passes', nargs='+')
parser.add_argument('--a', default='lecture.jsonl:gemini-4-argon-medium')
parser.add_argument('--b', default='lecture-flash.jsonl:gemini-3.8-flash-medium')
parser.add_argument('--output')
args = parser.parse_args()

page = [p for p in json.loads(Path(args.manifest).read_text())['pages']
        if args.page_id_or_sha in (p['id'], p['image_sha256'])][0]
rows, _ = load_page_reference(page['reference'])
coords = {el.get('id'): _points(el) for el in etree.parse(page['reference']).findall('.//{*}TextLine')}
reference = [(coords[r['id']], r['text']) for r in rows if r['id'] in coords]
lines = {l['id']: l for l in json.loads(Path(args.annotations).read_text())}


def load(directory, spec):
    name, model = spec.split(':')
    sheets = {s['sheet']: s for s in json.loads((directory / 'planches.json').read_text())}
    reads, stats = {}, []
    path = directory / name
    if not path.exists():
        return reads, stats
    for row in map(json.loads, path.read_text().splitlines()):
        if row.get('model') != model:
            continue
        stats.append(row)
        if row['answer'] is None:
            continue
        for k, meta in sheets[row['sheet']]['lines'].items():
            if isinstance(row['answer'].get(k), str):
                reads[(row['sheet'], meta['line_id'])] = row['answer'][k]
    return reads, stats


result = dict(a=args.a, b=args.b, passes=[])
totals = dict(lines=0, ref_chars=0, a_errors=0, b_errors=0, both_exact=0, a_only_exact=0, b_only_exact=0,
              neither_exact=0, unmatched_lines=0)
examples = []
timing = {'a': [], 'b': []}
tokens = {'a': [], 'b': []}
failures = {'a': 0, 'b': 0}
for directory in map(Path, args.passes):
    ra, sa = load(directory, args.a)
    rb, sb = load(directory, args.b)
    common_sheets = {k[0] for k in ra} & {k[0] for k in rb}
    for key, stats in (('a', sa), ('b', sb)):
        for row in stats:
            if row['sheet'] not in common_sheets and row['answer'] is not None:
                continue
            failures[key] += row['answer'] is None
            for entry in row.get('log', []):
                timing[key].append(entry['seconds'])
                if entry.get('usage'):
                    tokens[key].append(entry['usage'])
    for (sheet, line_id), text_a in ra.items():
        if sheet not in common_sheets or (sheet, line_id) not in rb:
            continue
        line = lines.get(line_id)
        if line is None:
            continue
        candidates = [(iou(line['bbox'], box), text) for box, text in reference]
        good = [c for c in candidates if c[0] >= .5]
        if len(good) != 1:
            totals['unmatched_lines'] += 1
            continue
        ref = cer_vt(good[0][1])
        a, b = cer_vt(text_a), cer_vt(rb[(sheet, line_id)])
        ea, eb = lev(ref, a), lev(ref, b)
        totals['lines'] += 1; totals['ref_chars'] += len(ref)
        totals['a_errors'] += ea; totals['b_errors'] += eb
        if ea == 0 and eb == 0:
            totals['both_exact'] += 1
        elif ea == 0:
            totals['a_only_exact'] += 1
        elif eb == 0:
            totals['b_only_exact'] += 1
        else:
            totals['neither_exact'] += 1
        if ea != eb:
            examples.append(dict(line=line_id, ref=good[0][1], a=text_a, b=rb[(sheet, line_id)], a_errors=ea, b_errors=eb))
totals['a_cer'] = totals['a_errors'] / totals['ref_chars']
totals['b_cer'] = totals['b_errors'] / totals['ref_chars']
for key in 'ab':
    t = timing[key]
    result[f'{key}_seconds'] = dict(calls=len(t), median=statistics.median(t) if t else None,
                                    mean=statistics.mean(t) if t else None, total=sum(t))
    u = tokens[key]
    result[f'{key}_tokens'] = dict(calls_with_usage=len(u),
                                   mean_total=statistics.mean(x['total_tokens'] for x in u) if u else None,
                                   mean_input=statistics.mean(x['input_tokens'] for x in u) if u else None,
                                   mean_thinking=statistics.mean(x.get('thinking_tokens', 0) for x in u) if u else None)
    result[f'{key}_failed_sheets'] = failures[key]
result['totals'] = totals
result['examples'] = examples
if args.output:
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=1))
print(json.dumps({k: v for k, v in result.items() if k != 'examples'}, ensure_ascii=False, indent=1))
for e in examples[:40]:
    print(f"{e['line']}: REF {e['ref']!r}\n   A({e['a_errors']}) {e['a']!r}\n   B({e['b_errors']}) {e['b']!r}")
