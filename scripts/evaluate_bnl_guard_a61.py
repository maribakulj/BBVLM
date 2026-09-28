"""Fixed A54 guard applied to localized native-band Sol correction."""
import json,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from evaluate_bnl_vlm_a54 import measures,reference_text,validate_and_apply
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'experiments/loop/bnl-guard-a61'
q=json.loads((P/'blind/request.json').read_text());a=json.loads((P/'sol-response.json').read_text());item=q['items'][0]
assert len(a['items'])==1 and a['items'][0]['id']=='V417'
assert set(a['inspected_images'])==set(item['images'])
assert hashlib.sha256(item['candidate'].encode()).hexdigest()==item['candidate_sha256']
old_request=json.loads((ROOT/'experiments/loop/bnl-bands-a60/blind/request.json').read_text())
old_hashes={x['id']:x['sha256'] for x in old_request['items']}
for image_path,old_id in zip(item['images'],['K843','K206','K591']):
 assert hashlib.sha256(Path(image_path).read_bytes()).hexdigest()==old_hashes[old_id]
text,guard=validate_and_apply(item['candidate'],a['items'][0]);ref=reference_text('0455')
per_edit=[];current=item['candidate']
for edit in a['items'][0]['edits']:
 changed=current.replace(edit['before'],edit['after'],1)
 per_edit.append({'before':edit['before'],'after':edit['after'],'lexical_edit_delta':measures(ref,changed)['lexical_alnum']['edits']-measures(ref,current)['lexical_alnum']['edits']})
 current=changed
r={'status':'complete_consumed_development_diagnostic','guard':guard,'candidate':measures(ref,item['candidate']),'sol_raw':measures(ref,a['items'][0]['text']),'sol_guarded':measures(ref,text),'declared_edits':a['items'][0]['edits'],'cost':{'reader_sessions':1,'image_items':3,'model':'gpt-6-sol','tokens':'not exposed','new_ocr_or_detector_forwards':0},'global_completion':False,'reference_unchanged':True,'per_edit_agreement_delta':per_edit,'image_bytes_match_frozen_a60':True}
(P/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False,indent=2))
