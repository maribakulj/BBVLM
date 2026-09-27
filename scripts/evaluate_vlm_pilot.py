"""Re-score recorded Terra/Luna outputs; no model call or oracle routing."""
from pathlib import Path
import sys
import json
import hashlib
from copy import deepcopy
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from bbvlm.document import load, save, apply_proposal
from bbvlm.metrics import text_scores, normalise
from bbvlm.__main__ import export_package

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'experiments/terra_luna'
refs = json.loads((BASE/'reference/selected.json').read_text())
graph = load(BASE/'input.graph.json')
requests = json.loads((BASE/'input/disagreements.json').read_text())
responses = {m: json.loads((BASE/f'{m}.response.json').read_text()) for m in ['terra','luna']}
ai={r['id']:r for r in responses['terra']['lines']}
bi={r['id']:r for r in responses['luna']['lines']}
expected_retry = [r['id'] for r in responses['terra']['lines'] if normalise(ai[r['id']]['text']) != normalise(bi[r['id']]['text'])]
assert requests['requested_line_ids'] == expected_retry, 'routing changed'
summary = {'type':'exploratory_pilot','reference_lines':len(refs),'reference_characters':sum(len(r['text']) for r in refs),
           'selection':'first three lines per region; 25 of 354 page lines',
           'geometry':'reference line/region crops, no word-box evaluation',
           'reading_order_caveat':'sequential region IDs reveal source order; do not interpret as a blind order benchmark',
           'retry_selection':'4 disagreements after NFC + ſ→s; no reference used',
           'models':{}}
for model, response in responses.items():
    first = text_scores(refs,response['lines'])
    (BASE/f'{model}.scores.json').write_text(json.dumps(first,ensure_ascii=False,indent=2))
    g = apply_proposal(graph,response,model)
    export_package(g,BASE/f'{model}.package',ROOT/'schemas')
    retry=json.loads((BASE/f'{model}.retry.json').read_text())
    corrected=apply_proposal(g,retry,model+' targeted retry',requests['requested_line_ids'])
    final_lines=[dict(id=n['id'],text=n.get('text','')) for n in corrected['nodes'] if n['kind']=='line']
    second=text_scores(refs,final_lines)
    (BASE/f'{model}.retry.scores.json').write_text(json.dumps(second,ensure_ascii=False,indent=2))
    export_package(corrected,BASE/f'{model}.retry.package',ROOT/'schemas')
    region_ids={n['id'] for n in graph['nodes'] if n['kind']=='region'}
    grouped={rid for a in response['articles'] for rid in a['regions']}
    expected_content=region_ids-{'R01','R02','R03','R04','R05'}
    summary['models'][model]={
        'model':'gpt-5.6-terra' if model=='terra' else 'gpt-6-luna',
        'reasoning_effort':'high','first':{k:v for k,v in first.items() if k!='per_line'},
        'after_targeted_retry':{k:v for k,v in second.items() if k!='per_line'},
        'content_regions_with_article_assignment':len(grouped & expected_content),
        'content_regions_total':len(expected_content),
        'article_accuracy':'not scored; no independently adjudicated article reference',
        'uncertain_lines_first':[r['id'] for r in response['lines'] if r.get('uncertain')],
        'uncertain_lines_retry':[r['id'] for r in retry['lines'] if r.get('uncertain')],
        'metadata_fields':len(response['metadata']),
        'runtime_and_token_cost':'not available from sub-agent interface',
        'response_sha256':hashlib.sha256((BASE/f'{model}.response.json').read_bytes()).hexdigest()}
(BASE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
