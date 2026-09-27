"""Evaluate saved VLM reads on geometrically matched, predicted French crops.

Selection and escalation are already saved and are never chosen using this file.
Unmatched predictions remain separately reported, not assumed correct.
"""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from evaluate_end_to_end import lines,match
from bbvlm.document import load,apply_proposal
from bbvlm.metrics import text_scores
from bbvlm.__main__ import export_package
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/loop/french-vlm';p=ROOT/'experiments/loop/end-to-end/0253902-001'
source=json.loads((ROOT/'experiments/loop/cache/0253902-001/run.json').read_text());ref=lines(ROOT/source['source_xml']);pred=lines(p/'layout.xml');pairs,*_=match(ref,pred);mapping={pred[h]['id']:ref[r] for r,h,v in pairs}
graph=load(base/'native.graph.json');ix={n['id']:n for n in graph['nodes']};request=json.loads((base/'input/request.json').read_text());response=json.loads((base/'luna.response.json').read_text())
g=apply_proposal(graph,response,'gpt-6-luna French predicted crops',request['requested_line_ids']);export_package(g,base/'luna.package',ROOT/'schemas')
references=[];unmatched=[];baseline=[]
for lid in request['requested_line_ids']:
    rid=ix[lid]['source_id']
    if rid in mapping:references.append({'id':lid,'text':mapping[rid]['text']});baseline.append({'id':lid,'text':ix[lid].get('text','')})
    else:unmatched.append(lid)
known={r['id'] for r in references}
summary={'selected_lines':len(request['requested_line_ids']),'matched_reference_lines':len(references),'unmatched_predicted_ids':unmatched,'reference_characters':sum(len(r['text']) for r in references),'geometry':'native predicted PERO lines; matching IoU>=.5; no oracle crops','native':text_scores(references,baseline),'luna':text_scores(references,[l for l in response['lines'] if l['id'] in known]),'scope':'exploratory development-page sample; not a frontier benchmark; distributed reference contains suspected transcription errors and requires independent audit','routing':'uncertain=true chosen before reference scoring; 5 expanded context crops'}
sol=base/'sol.escalation.json'
if sol.exists():
    retry=json.loads(sol.read_text());route=json.loads((base/'escalation-input/request.json').read_text());g=apply_proposal(g,retry,'gpt-6-sol targeted French escalation',route['requested_line_ids']);export_package(g,base/'luna-sol.package',ROOT/'schemas');summary['luna_sol']=text_scores(references,[n for n in g['nodes'] if n['kind']=='line' and n['id'] in known])
(base/'scores.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps({k:{a:b for a,b in v.items() if a!='per_line'} if isinstance(v,dict) else v for k,v in summary.items()},indent=2))
