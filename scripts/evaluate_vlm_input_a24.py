"""Score the single A24 input-ablation response against fixed consumed A22 data."""
from pathlib import Path
import hashlib,json
from bbvlm.metrics import edit_distance
from bbvlm.ocr_conventions import transform

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/loop';A22=BASE/'reserve-a22';OUT=BASE/'vlm-input-a24'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def score(ref,hyp,profile):
    rows=[]
    for r in ref:
        a=transform(r['text'],profile);b=transform(hyp[r['id']]['text'],profile);e=edit_distance(a,b)
        rows.append({'id':r['id'],'characters':len(a),'edits':e,'exact':a==b,'reference_view':a,'hypothesis_view':b})
    n=sum(r['characters'] for r in rows);e=sum(r['edits'] for r in rows)
    return {'characters':n,'edits':e,'cer':e/n,'exact_lines':sum(r['exact'] for r in rows),'per_line':rows}
def main():
    ref=json.loads((A22/'private-reference.json').read_text());old=json.loads((A22/'sol-response.json').read_text())
    new=json.loads((OUT/'sol-response.json').read_text());request=json.loads((OUT/'input/request.json').read_text())
    ids={r['id'] for r in ref};oh={r['id']:r for r in old['lines']};nh={r['id']:r for r in new['lines']}
    assert set(oh)==set(nh)==ids and len(nh)==len(new['lines'])==16
    expected={r['image'] for r in request['items']};inspected={str(Path(p).relative_to(ROOT)) if Path(p).is_absolute() else p for p in new['inspected_images']}
    assert expected<=inspected
    scores={}
    for profile in ('strict','glyph_decomposition_v1'):
        scores[profile]={'a22_native_crop':score(ref,oh,profile),'a24_multiscale_composite':score(ref,nh,profile)}
    protected=[A22/'private-reference.json',A22/'sol-response.json',OUT/'PROTOCOL.md',OUT/'input/request.json']+[ROOT/p for p in expected]
    hashes={str(p.relative_to(ROOT)):sha(p) for p in protected}
    report={'schema':'bbvlm.vlm-input-ablation-a24/1','scope':'post-hoc diagnostic on consumed A22 reserve',
      'reader':'gpt-6-sol','new_vlm_tasks':1,'images':16,'scores':scores,
      'uncertain_ids':sorted(r['id'] for r in new['lines'] if r.get('uncertain')),
      'invariants':{'exact_id_coverage':True,'all_composites_inspected':True,'protected_inputs_hashed':True},
      'limitations':['same model is stochastic and conditions were not randomized in parallel','A22 is consumed; result cannot select a final configuration','composites use oracle target line boxes','no raw Claude/Gemini outputs or exact prompts/settings were available for direct comparison'],
      'accepted_for_project_completion_gate':False,'protected_input_sha256':hashes}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({p:{k:{a:b for a,b in v.items() if a!='per_line'} for k,v in x.items()} for p,x in scores.items()},indent=2))
if __name__=='__main__':main()
