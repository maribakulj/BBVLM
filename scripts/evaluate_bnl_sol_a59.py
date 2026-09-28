#!/usr/bin/env python3
"""Score blinded Sol native-image diagnostic without modifying source references."""
import sys,json,hashlib,difflib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from evaluate_bnl_vlm_a54 import reference_text, measures
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'experiments/loop/bnl-sol-a59';A=ROOT/'experiments/loop/bnl-independent-a54'
mapping=json.loads((P/'private-map.json').read_text());request=json.loads((P/'blind/request.json').read_text());response=json.loads((P/'sol-response.json').read_text());answers=response['items']
assert len(answers)==len(mapping) and {x['id'] for x in answers}==set(mapping)
paths={x['image'] for x in request['items']};assert set(response['inspected_images'])==paths
for x in request['items']:assert hashlib.sha256(Path(x['image']).read_bytes()).hexdigest()==x['sha256']
prior={x['source_id']:x for x in json.loads((A/'vlm-report.json').read_text())['rows']};rows=[]
for ans in answers:
 sid=mapping[ans['id']];ref=reference_text(sid);score=measures(ref,ans['text'])
 from bbvlm.text_views import lexical_alnum
 left,right=lexical_alnum(ref),lexical_alnum(ans['text'])
 changes=[{'operation':op,'reference':left[i:j],'hypothesis':right[k:l],'ref_context':left[max(0,i-25):min(len(left),j+25)],'hyp_context':right[max(0,k-25):min(len(right),l+25)]} for op,i,j,k,l in difflib.SequenceMatcher(None,left,right,autojunk=False).get_opcodes() if op!='equal']
 rows.append({'id':ans['id'],'source_id':sid,'control':sid in ['0439','0456'],'luna_guarded':prior[sid]['luna_guarded'],'sol':score,'uncertain_spans':ans.get('uncertain_spans',[]),'lexical_differences':changes})
agg={}
for system in ['luna_guarded','sol']:
 agg[system]={}
 for view in rows[0][system]:
  n=sum(x[system][view]['characters'] for x in rows);e=sum(x[system][view]['edits'] for x in rows)
  agg[system][view]={'characters':n,'edits':e,'cer':e/n,'exact_blocks':sum(x[system][view]['exact'] for x in rows)}
report={'status':'completed_consumed_development_diagnostic','selection':'four largest A54 lexical residuals plus two exact controls; oracle diagnostic only','rows':rows,'aggregate':agg,'control_regressions':{v:[x['id'] for x in rows if x['control'] and not x['sol'][v]['exact']] for v in rows[0]['sol']},'cost':{'agent':'gpt-6-sol','reader_sessions':1,'image_items':6,'extra_detector_or_ocr_forwards':0,'tokens':'not exposed'},'reference_status':'unchanged provider XML; disagreements require visual adjudication','global_completion':False}
(P/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
