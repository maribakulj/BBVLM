import json,hashlib
from pathlib import Path
from evaluate_bnl_vlm_a54 import measures,VIEWS
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'experiments/loop/next-a81'
r=json.loads((P/'blind/sol-request.json').read_text());a=json.loads((P/'sol-response.json').read_text());old=json.loads((P/'report.json').read_text());expected={x['id'] for x in r['items']};assert len(a['items'])==len(expected)==3 and {x['id'] for x in a['items']}==expected
imgs=[p for x in r['items'] for p in x['images']];assert len(a['inspected_images'])==6 and set(a['inspected_images'])==set(imgs)
for x in r['items']:
 for p,s in zip(x['images'],x['sha256']):assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==s
by={x['id']:x for x in old['rows']};rows=[]
for x in a['items']:
 ref=by[x['id']]['reference'];assert ref is not None;rows.append({'id':x['id'],'reference':ref,'luna_text':by[x['id']]['text'],'sol_text':x['text'],'luna':by[x['id']]['agreement'],'sol':measures(ref,x['text']),'neighboring_line_contamination':x['neighboring_line_contamination']})
summary={}
for system in ['luna','sol']:
 summary[system]={}
 for v in VIEWS:
  n=sum(x[system][v]['characters'] for x in rows);e=sum(x[system][v]['edits'] for x in rows);summary[system][v]={'characters':n,'edits':e,'cer':e/n if n else None,'exact_crops':sum(x[system][v]['exact'] for x in rows)}
report={'status':'targeted_consumed_prompt_and_model_change','summary':summary,'rows':rows,'cost':{'new_reader_sessions':1,'model':'gpt-6-sol','images':6,'tokens_and_money':'not exposed'},'limitations':['Post-score oracle selection, two failures plus exact control','Changed principal-line instruction and reader together; no causal ablation','Reference not independently human-adjudicated','Do not report repaired six-crop zero as independent system CER'],'global_completion':False}
(P/'targeted-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,indent=2))
