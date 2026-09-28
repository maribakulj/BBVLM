"""Compare same source content as a tall image versus three native bands."""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from evaluate_bnl_vlm_a54 import reference_text,measures
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'experiments/loop/bnl-bands-a60'
m=json.loads((P/'private-map.json').read_text());q=json.loads((P/'blind/request.json').read_text());a=json.loads((P/'sol-response.json').read_text());rows=a['items'];byid={x['id']:x for x in rows}
assert len(rows)==len(m['order']) and set(byid)==set(m['order'])
assert set(a['inspected_images'])=={x['image'] for x in q['items']}
for x in q['items']:assert hashlib.sha256(Path(x['image']).read_bytes()).hexdigest()==x['sha256']
text='\n'.join(byid[x]['text'].strip() for x in m['order']);score=measures(reference_text(m['source_id']),text)
a59=next(x for x in json.loads((ROOT/'experiments/loop/bnl-sol-a59/report.json').read_text())['rows'] if x['source_id']==m['source_id'])
r={'status':'completed_consumed_development_ablation','source_id':m['source_id'],'source_size':m['source_size'],'cuts':m['cuts'],'luna_guarded_a54':a59['luna_guarded'],'sol_tall_a59':a59['sol'],'sol_bands_a60':score,'improved_lexical':score['lexical_alnum']['edits']<a59['sol']['lexical_alnum']['edits'],'cost':{'reader_sessions':1,'image_items':3,'model':'gpt-6-sol','new_pixels':0,'new_detector_or_ocr_forwards':0,'tokens':'not exposed'},'limitations':['single changed presentation and new stochastic session','consumed development block','source reference has not been independently adjudicated','no independent claim of zero CER'], 'global_completion':False}
(P/'joined-text.txt').write_text(text+'\n');(P/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,indent=2))
