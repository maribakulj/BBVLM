"""Score a consumed oracle-selected audit; never patch source references."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from evaluate_bnl_vlm_a54 import measures,reference_text
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'experiments/loop/next-a63'
request=json.loads((P/'blind/request.json').read_text());response=json.loads((P/'sol-response.json').read_text());private=json.loads((P/'private-map.json').read_text())
items=response['items'];ids=[x['id'] for x in items];expected=[x['id'] for x in request['items']]
assert len(ids)==len(set(ids)) and set(ids)==set(expected),'IDs must match exactly'
images=[p for x in request['items'] for p in x['images']]
assert len(response['inspected_images'])==len(images) and set(response['inspected_images'])==set(images),'inspected image inventory mismatch'
for item in request['items']:
 for path,sha in zip(item['images'],item['sha256']):
  assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,'changed image'
for suffix,label in [('png','source_sha256'),('xml','xml_sha256')]:
 assert hashlib.sha256((ROOT/f'experiments/loop/bnl-independent-a54/source/0455.{suffix}').read_bytes()).hexdigest()==private[label]
ref=reference_text('0455').splitlines();old=json.loads((ROOT/'experiments/loop/bnl-guard-a61/sol-response.json').read_text())['items'][0]['text'].splitlines()
assert len(ref)==len(old)==68
by_id={x['id']:x for x in items};rows=[]
for entry in private['mapping']:
 answer=by_id[entry['id']];idx=entry['line_index'];assert isinstance(answer['text'],str) and answer['text'].strip()
 rows.append({'id':entry['id'],'source_line_index':idx,'reference':ref[idx],'a61':old[idx],'a63':answer['text'],
 'a61_agreement':measures(ref[idx],old[idx]),'a63_agreement':measures(ref[idx],answer['text']),
 'uncertain_spans':answer.get('uncertain_spans',[])})
summary={}
for system in ['a61','a63']:
 summary[system]={}
 for view in ['strict_nfc_diplomatic','search_v1','lexical_alnum']:
  chars=sum(x[system+'_agreement'][view]['characters'] for x in rows);edits=sum(x[system+'_agreement'][view]['edits'] for x in rows)
  summary[system][view]={'characters':chars,'edits':edits,'cer':edits/chars,'exact_lines':sum(x[system+'_agreement'][view]['exact'] for x in rows)}
report={'status':'completed_consumed_reference_audit','selection':'four oracle-selected residual lines and two exact controls',
 'summary_agreement_only':summary,'rows':rows,'cost':{'new_reader_sessions':1,'model':'gpt-6-sol','unique_line_crops':6,'image_views':12,'tokens_and_money':'not exposed'},
 'originals_unchanged':True,'global_completion':False,'independent_gt_adjudication':False,
 'limitations':['Selected after A61 scores; no holdout claim','Reference disagreements may reflect transcription annotation errors','New session and zoom are confounded','No whole-block CER after oracle repair','Model agreement is not human adjudication']}
(P/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
