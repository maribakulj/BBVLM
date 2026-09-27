"""Compare blind unmasked Sol with original Sol, never changing the reference."""
import hashlib,json,time
from pathlib import Path
from evaluate_bnf_region_ocr_a30 import score,strict
from audit_bnf_region_ocr_a30 import retrieval

ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/'experiments/loop/unmasked-a31'
A30=ROOT/'experiments/loop/bnf-region-ocr-a30'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    started=time.perf_counter()
    task=json.loads((EXP/'task.json').read_text())
    ref=json.loads((A30/'private-reference.json').read_text())['items']
    old=json.loads((A30/'candidate/sol.json').read_text())
    new=json.loads((EXP/'sol.json').read_text())
    ids={i['id'] for i in task['items']}
    paths={i[k]['path'] for i in task['items'] for k in ('target','context')}
    assert set(new['transcriptions'])==ids==set(ref), 'ID mismatch'
    assert set(new['inspected_paths'])==paths, 'inspection paths mismatch'
    for item in task['items']:
        for kind in ('target','context'):
            assert sha(ROOT/item[kind]['path'])==item[kind]['sha256'], 'image changed'
    scores={}
    for name,pred in [('masked_a30_sol',old),('unmasked_context_a31_sol',new)]:
        scores[name]={'normalized':score(ref,pred['transcriptions'],retrieval),
                      'strict_secondary':score(ref,pred['transcriptions'],strict)}
    before={r['id']:r for r in scores['masked_a30_sol']['normalized']['per_region']}
    after={r['id']:r for r in scores['unmasked_context_a31_sol']['normalized']['per_region']}
    changes=[{'id':i,'edits_before':before[i]['edits'],'edits_after':after[i]['edits'],
              'reference':ref[i]['reference'],'before':old['transcriptions'][i],
              'after':new['transcriptions'][i]} for i in sorted(ids)
             if old['transcriptions'][i]!=new['transcriptions'][i]]
    report={'schema':'bbvlm.unmasked-a31-report/1',
      'status':'posthoc consumed-data input ablation, blind new reader; not independent validation',
      'primary_metric':'normalized CER using unchanged A30 post-score retrieval function, not verified Gallica/Exalead rules',
      'scores':scores,'changes':changes,
      'improved_ids':[i for i in sorted(ids) if after[i]['edits']<before[i]['edits']],
      'regressed_ids':[i for i in sorted(ids) if after[i]['edits']>before[i]['edits']],
      'uncertain_ids':new.get('uncertain_ids',[]),
      'cost':{'new_vlm_tasks':1,'input_images':32,'baseline_input_images':16,'evaluator_seconds':time.perf_counter()-started,'tokens_and_billing':'not exposed by subagent interface'},
      'invariants':{'exact_ids':True,'all_images_declared_inspected':True,'input_image_hashes_verified':True,
                    'old_reference_sha256':sha(A30/'private-reference.json'),'old_sol_sha256':sha(A30/'candidate/sol.json'),
                    'new_sol_sha256':sha(EXP/'sol.json'),'reader_denied_prior_outputs_and_reference':True},
      'limitations':['Joint intervention: no mask, no overlay, added context, adapted target instruction.',
                     'One stochastic pass per condition: cannot isolate causality from run-to-run variation.',
                     'Reference anomalies remain unchanged; agreements/disagreements are not adjudicated truth.',
                     'Reference-based crop geometry remains oracle; not end-to-end.'],
      'accepted_for_project_completion_gate':False}
    (EXP/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('scores','changes')},ensure_ascii=False,indent=2))
    for name,profiles in scores.items():
        print(name,{p:{k:v for k,v in s.items() if k!='per_region'} for p,s in profiles.items()})

if __name__=='__main__':main()
