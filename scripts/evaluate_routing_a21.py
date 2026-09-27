"""Compare all six Luna non-escalated lines before/after actual blind Sol."""
import json
from pathlib import Path
from evaluate_ocr_conventions_a20 import evaluate, sha
from bbvlm.ocr_conventions import transform

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'experiments/loop'
OUT = BASE/'routing-a21'
REF = BASE/'reference-a18'


def main():
    previous = json.loads((BASE/'conventions-a20/report.json').read_text())
    for path, digest in previous['protected_input_sha256'].items():
        assert sha(ROOT/path) == digest
    reference = json.loads((REF/'private-reference.json').read_text())
    luna = json.loads((REF/'luna-response.json').read_text())
    luna = luna['lines'] if isinstance(luna, dict) else luna
    old_sol = json.loads((REF/'sol-response.json').read_text())['lines']
    raw = json.loads((OUT/'sol-response.json').read_text())
    new_sol = raw['lines']
    request = json.loads((OUT/'input/request.json').read_text())
    ids = {r['id'] for r in request['items']}
    assert ids == {r['id'] for r in luna if not r.get('uncertain')}
    assert ids == {r['id'] for r in new_sol} and len(new_sol) == len(ids)
    required = {r['image'] for r in request['items']}
    inspected = {str(Path(p).relative_to(ROOT)) if Path(p).is_absolute() else p
                 for p in raw['inspected_images']}
    assert required <= inspected
    old = {r['id']: r for r in luna}
    old.update({r['id']:r for r in old_sol})
    new = dict(old)
    new.update({r['id']:r for r in new_sol})
    scores = {}
    comparisons = {}
    for profile in ('strict', 'glyph_decomposition_v1'):
        fn = lambda s: transform(s, profile)
        scores[profile] = {name: evaluate(reference, list(lines.values()), fn)
                           for name, lines in [('before', old), ('after', new)]}
        subset = [r for r in reference if r['id'] in ids]
        scores[profile]['six_luna'] = evaluate(subset, [r for r in luna if r['id'] in ids], fn)
        scores[profile]['six_sol'] = evaluate(subset, new_sol, fn)
        a = {r['id']: r['edits'] for r in scores[profile]['six_luna']['per_line']}
        b = {r['id']: r['edits'] for r in scores[profile]['six_sol']['per_line']}
        comparisons[profile] = {
            'improved_ids': sorted(i for i in ids if b[i] < a[i]),
            'regressed_ids': sorted(i for i in ids if b[i] > a[i]),
            'unchanged_ids': sorted(i for i in ids if b[i] == a[i]),
            'non_escalated_disagreement_lines_before': sum(v > 0 for v in a.values()),
            'non_escalated_lines': len(ids),
            'warning': 'Reference agreement; not human-adjudicated correctness'}
    split = json.loads((REF/'split.json').read_text())
    assert all(not (REF/'source'/p[k]).exists() for p in split['pages']
               if p['role'] == 'reserve' for k in ('xml','image'))
    report = {'schema': 'bbvlm.routing-ablation-a21/1', 'scores': scores,
        'comparisons': comparisons,
        'scope': 'All six not-uncertain Luna outputs on consumed A18 audit; selection based on uncertainty flag, global motivation post-hoc',
        'confounds': ['reader model', 'polygon-isolated presentation', 'more explicit historical-convention prompt'],
        'cost': {'new_vlm_tasks': 1, 'new_reader': 'gpt-6-sol',
                 'interrupted_and_resumed_agent_turns': 1,
                 'target_images_inspected': len(required), 'total_images_inspected': len(inspected),
                 'new_tokens': None, 'new_billed_cost': None,
                 'cumulative_reading_tasks_a18_a21': 3,
                 'note': 'Task count is not backend-forward count; 16 Luna + 16 Sol target reads cumulatively'},
        'sol_uncertain_ids': [r['id'] for r in new_sol if r.get('uncertain')],
        'response_sha256': sha(OUT/'sol-response.json'),
        'request_sha256': sha(OUT/'input/request.json'),
        'agent_prompt_sha256': sha(OUT/'AGENT_PROMPT.txt'),
        'input_image_sha256': {r[k]: sha(ROOT/r[k]) for r in request['items']
                               for k in ('image', 'original_image')},
        'invariants': {'original_predictions_reference_unchanged': True, 'reserve_bytes_absent': True,
                       'exact_id_coverage': True, 'all_targets_visually_inspected': True},
        'decision': 'Do not certify using reader self-confidence alone; preserve disagreements and review queue. No automatic production escalation policy inferred from six consumed lines.',
        'accepted_for_project_completion_gate': False}
    (OUT/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({p: {n: {k:v for k,v in s.items() if k != 'per_line'}
                           for n,s in d.items()} for p,d in scores.items()}, indent=2))


if __name__ == '__main__':
    main()
