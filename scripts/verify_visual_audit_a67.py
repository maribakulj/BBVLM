"""Verify a real reader receipt and image fixity; never certify visual truth."""
import collections,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'experiments/loop/next-a67'
def main():
    request=json.loads((OUT/'blind/request.json').read_text())
    response=json.loads((OUT/'luna-response.json').read_text())
    views=[v for c in request['cases'] for v in c['views']]
    assert len(views)==12 and len({v['path'] for v in views})==12
    for v in views:assert hashlib.sha256(Path(v['path']).read_bytes()).hexdigest()==v['sha256'],v['path']
    assert response['model']=='gpt-6-luna'
    assert set(response['inspected_paths'])=={v['path'] for v in views}
    expected={c['id'] for c in request['cases']};ids=[c['id'] for c in response['cases']]
    assert len(ids)==len(set(ids))==4 and set(ids)==expected
    for c in response['cases']:
        assert c['visible_clipping'] in ('yes','no','uncertain')
        assert c['additional_text_separate'] in ('yes','no','uncertain')
        assert all(k in c for k in ('affected_edge','evidence','confidence','uncertainties'))
        assert isinstance(c['evidence'],str) and c['evidence'].strip()
    secondary=json.loads((OUT/'sol-response.json').read_text())
    assert secondary['model']=='gpt-6-sol'
    assert len(secondary['cases'])==2 and {c['id'] for c in secondary['cases']}=={'K482','K951'}
    selected=[v for c in request['cases'] if c['id'] in ('K482','K951') for v in c['views']]
    assert set(secondary['inspected_paths'])=={v['path'] for v in selected}
    for c in secondary['cases']:
        assert c['visible_clipping'] in ('yes','no','uncertain')
        assert c['additional_text_separate'] in ('yes','no','uncertain')
        assert all(k in c for k in ('affected_edge','evidence','confidence','uncertainties'))
    report={'status':'consumed_oracle_selected_visual_diagnostic_not_gold',
        'reader_agent':'/root/a67_luna','reader_model':'gpt-6-luna','reader_calls':1,
        'cases':4,'views':12,'view_pixels':sum(v['size'][0]*v['size'][1] for v in views),
        'clipping_observations':dict(collections.Counter(c['visible_clipping'] for c in response['cases'])),
        'image_hashes_verified':12,'strict_ids_valid':True,'ocr_cer_measured':False,
        'billing_tokens':None,'monetary_cost':None,'all_scientific_gates_passed':False,
        'targeted_reader_agent':'/root/a67_sol','targeted_reader_model':'gpt-6-sol',
        'targeted_reader_calls':1,'targeted_views':6,
        'targeted_clipping_observations':{c['id']:c['visible_clipping'] for c in secondary['cases']},
        'targeted_response_sha256':hashlib.sha256((OUT/'sol-response.json').read_bytes()).hexdigest(),
        'response_sha256':hashlib.sha256((OUT/'luna-response.json').read_bytes()).hexdigest(),
        'limitations':['Metric-selected examples are consumed, not independent validation.','Reader observation is not human adjudication.','Native crops/context do not certify every glyph or original annotation.']}
    (OUT/'report-v2.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
