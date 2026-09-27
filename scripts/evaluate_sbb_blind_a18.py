"""Score raw blind reader outputs without rewriting the external reference."""
from pathlib import Path
import json
import hashlib
import unicodedata
from bbvlm.metrics import text_scores

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'experiments/loop/reference-a18'


def main():
    reference = json.loads((BASE/'private-reference.json').read_text())
    raw = json.loads((BASE/'luna-response.json').read_text())
    lines = raw['lines'] if isinstance(raw, dict) else raw
    assert {r['id'] for r in lines} == {r['id'] for r in reference}
    assert len(lines) == len(reference)
    report = {'schema': 'bbvlm.sbb-blind-ocr-audit/1',
              'reference': 'external SBB original, no correction from our models',
              'scope': '16 random oracle line crops from four audit works, not end-to-end',
              'scores': {'luna': text_scores(reference, lines)},
              'luna_uncertain': [r['id'] for r in lines if r.get('uncertain')],
              'input_response_sha256': hashlib.sha256((BASE/'luna-response.json').read_bytes()).hexdigest(),
              'passes': {'luna': 1, 'sol': 0},
              'cost_observability': {'luna_input_crops': len(reference), 'token_counts': None,
                                     'billed_cost': None, 'note': 'A pass is an agent reading task, not a measured backend forward or free inference'},
              'reference_encoding': {
                  'private_use_characters': sum(unicodedata.category(c)=='Co' for r in reference for c in r['text']),
                  'lines_with_private_use': sum(any(unicodedata.category(c)=='Co' for c in r['text']) for r in reference),
                  'policy': 'Keep strict score; do not infer a favorable PUA mapping from model predictions. Obtain the authoritative OCR-D/MUFI mapping before a separate comparable convention score.'},
              'accepted_for_project_completion_gate': False}
    sol_path = BASE/'sol-response.json'
    if sol_path.exists():
        sol = json.loads(sol_path.read_text())['lines']
        request = json.loads((BASE/'sol-input/request.json').read_text())
        ids = {r['id'] for r in request['items']}
        assert {r['id'] for r in sol} == ids and len(sol) == len(ids)
        combined = {r['id']:r for r in lines}
        combined.update({r['id']:r for r in sol})
        report['scores']['luna_sol'] = text_scores(reference, list(combined.values()))
        report['passes']['sol'] = 1
        report['cost_observability'].update(sol_target_crops=len(sol), sol_original_context_crops=len(sol))
        report['sol_target_ids'] = sorted(ids)
        report['sol_selection'] = 'Luna uncertainty only, not reference CER'
        report['comparison_confound'] = 'Sol received polygon-isolated targets plus original context; model and presentation both changed'
        report['sol_response_sha256'] = hashlib.sha256(sol_path.read_bytes()).hexdigest()
    (BASE/'ocr-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({**report, 'scores': {k: {a:b for a,b in v.items() if a!='per_line'} for k,v in report['scores'].items()}}, indent=2))


if __name__ == '__main__':
    main()
