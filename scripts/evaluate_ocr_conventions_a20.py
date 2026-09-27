"""Re-evaluate consumed A18 outputs with source-defined, symmetric views.

No inference, reference correction, score-based routing or reserve access.
The compatibility dictionaries are AST data, never executed downloaded code.
"""
import ast
import hashlib
import json
import time
import unicodedata
from pathlib import Path
from bbvlm.metrics import edit_distance
from bbvlm.ocr_conventions import transform, private_use_inventory

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'experiments/loop'
OUT = BASE/'conventions-a20'
REF = BASE/'reference-a18'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compatibility_tables():
    tree = ast.parse((OUT/'source/extracted_text.py').read_text())
    tables = []
    for name in ('unjoin_ligatures', 'substitute_equivalences'):
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
        assignment = next(n for n in fn.body if isinstance(n, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == 'equivalences' for t in n.targets))
        tables.append(ast.literal_eval(assignment.value))
    return tables


def evaluate(reference, hypothesis, normalizer):
    ref = {r['id']: r['text'] for r in reference}
    hyp = {r['id']: r['text'] for r in hypothesis}
    if len(ref) != len(reference) or len(hyp) != len(hypothesis) or set(ref) != set(hyp):
        raise ValueError('Exact unique ID coverage required')
    rows = []
    for lid, value in ref.items():
        a, b = normalizer(value), normalizer(hyp[lid])
        rows.append({'id': lid, 'reference_view': a, 'hypothesis_view': b,
                     'characters': len(a), 'edits': edit_distance(a, b),
                     'exact': a == b, 'reference_retained_pua': private_use_inventory(a)})
    chars = sum(r['characters'] for r in rows)
    edits = sum(r['edits'] for r in rows)
    return {'lines': len(rows), 'characters': chars, 'edits': edits,
            'cer': edits/chars if chars else None,
            'exact_lines': sum(r['exact'] for r in rows), 'per_line': rows}


def main():
    start = time.perf_counter()
    protected = [REF/p for p in ('private-reference.json', 'luna-response.json',
                                 'sol-response.json', 'split.json', 'ocr-report.json')]
    protected += list((REF/'source').rglob('*.xml'))
    before = {str(p.relative_to(ROOT)): sha(p) for p in protected}
    reference = json.loads(protected[0].read_text())
    luna = json.loads(protected[1].read_text())
    luna = luna['lines'] if isinstance(luna, dict) else luna
    sol = json.loads(protected[2].read_text())['lines']
    requested = json.loads((REF/'sol-input/request.json').read_text())['items']
    assert {r['id'] for r in sol} == {r['id'] for r in requested}
    assert len(sol) == len(requested)
    combined = {r['id']: r for r in luna}
    combined.update({r['id']: r for r in sol})
    tables = compatibility_tables()

    def compatibility(s):
        s = unicodedata.normalize('NFC', s)
        for table in tables:
            for old, new in table.items():
                s = s.replace(old, new)
        return s

    normalizers = {'strict': lambda s: s,
                   'glyph_decomposition_v1': lambda s: transform(s, 'glyph_decomposition_v1'),
                   'dinglehopper_sbb_compatibility_codepoints': compatibility}
    scores = {name: {profile: evaluate(reference, lines, fn)
                    for profile, fn in normalizers.items()}
              for name, lines in [('luna', luna), ('luna_sol', list(combined.values()))]}
    split = json.loads((REF/'split.json').read_text())
    reserve_absent = all(not (REF/'source'/p[k]).exists() for p in split['pages']
                         if p['role'] == 'reserve' for k in ('xml', 'image'))
    assert reserve_absent
    assert before == {str(p.relative_to(ROOT)): sha(p) for p in protected}
    old = json.loads((REF/'ocr-report.json').read_text())['scores']
    for reader in scores:
        for key in ('characters', 'edits', 'cer', 'exact_lines'):
            assert scores[reader]['strict'][key] == old[reader][key]
    report = {
        'schema': 'bbvlm.ocr-conventions-a20/1', 'scores': scores,
        'scope': 'Consumed 16 A18 oracle line crops, four audit works; diagnostic only',
        'unit': 'Unicode code points, including spaces and punctuation; not grapheme CER',
        'reference_status': 'External original SBB GT unchanged; not independently adjudicated',
        'profile_limits': {
            'strict': 'Original code points, no normalization',
            'glyph_decomposition_v1': 'NFC + documented ligatures and e-above decomposition. Loses ligature identity; retains long s, punctuation, abbreviations and e-above distinction. Not level-3 exactness.',
            'dinglehopper_sbb_compatibility_codepoints': 'Pinned dictionary compatibility view; folds e-above to umlaut, hyphen variants and apostrophe, includes upstream uncertain q& mapping. Not diplomatic and not the dinglehopper grapheme metric.',
        },
        'protected_input_sha256': before,
        'source_sha256': {str(p.relative_to(OUT)): sha(p) for p in (OUT/'source').iterdir() if p.is_file()},
        'transform_sha256': sha(ROOT/'src/bbvlm/ocr_conventions.py'),
        'retained_pua_policy': 'Never delete or guess a mapping; F1E8 retained in all profiles',
        'cost': {'new_vlm_tasks': 0, 'new_neural_forwards': 0,
                 'cpu_wall_seconds': time.perf_counter()-start, 'historical_inference_cost': 'See A18; not zero'},
        'invariants': {'reference_predictions_unchanged': True, 'reserve_bytes_absent': reserve_absent,
                       'strict_scores_reproduced': True},
        'accepted_for_project_completion_gate': False,
    }
    (OUT/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: {p: {a:b for a,b in v.items() if a != 'per_line'}
                          for p,v in s.items()} for k,s in scores.items()}, indent=2))


if __name__ == '__main__':
    main()
