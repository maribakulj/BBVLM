#!/usr/bin/env python3
"""Score blind A30 region OCR under diplomatic and search views."""
from __future__ import annotations
import hashlib,json,re,time,unicodedata
from pathlib import Path
from bbvlm.metrics import edit_distance
ROOT=Path(__file__).resolve().parents[1];EXP=ROOT/'experiments/loop/bnf-region-ocr-a30';A26=ROOT/'experiments/loop/bnf-impact-a26'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def strict(s):return '\n'.join(x.rstrip() for x in unicodedata.normalize('NFC',s.replace('\r\n','\n').replace('\r','\n')).strip().split('\n'))
def search(s):
 s=unicodedata.normalize('NFKC',strict(s)).lower().replace('’',"'").replace('‘',"'");s=re.sub(r'-\n(?=\w)','',s);return re.sub(r'\s+',' ',s).strip()
def score(ref,hyp,view):
 rows=[]
 for token in sorted(ref):
  a=view(ref[token]['reference']);b=view(hyp[token]);e=edit_distance(a,b);rows.append({'id':token,'characters':len(a),'edits':e,'exact':a==b,'reference':a,'hypothesis':b})
 chars=sum(x['characters'] for x in rows);edits=sum(x['edits'] for x in rows);return {'characters':chars,'edits':edits,'cer':edits/chars if chars else None,'exact_regions':sum(x['exact'] for x in rows),'per_region':rows}
def main():
 started=time.perf_counter();s=json.loads((EXP/'split.json').read_text());checks={'protocol':EXP/'PROTOCOL.md','prompt':EXP/'VLM_PROMPT.md','preparer':ROOT/'scripts/prepare_bnf_region_ocr_a30.py','evaluator':ROOT/'scripts/evaluate_bnf_region_ocr_a30.py','metrics':ROOT/'src/bbvlm/metrics.py','archive_manifest':A26/'source/archive-manifest.json'}
 for k,p in checks.items():
  if sha(p)!=s['sealed_sha256'][k]:raise ValueError(f'sealed file changed: {k}')
 task=json.loads((EXP/'public-task.json').read_text());ref=json.loads((EXP/'private-reference.json').read_text())['items'];pred=json.loads((EXP/'candidate/luna.json').read_text());hyp=pred.get('transcriptions',{});ids=set(task['expected_ids']);inspected=set(pred.get('inspected_paths',[]));expected_paths={x['image'] for x in task['items']};unknown=sorted(set(hyp)-ids);missing=sorted(ids-set(hyp));scores={'strict_nfc_diplomatic':score(ref,hyp,strict) if not unknown and not missing else None,'search_normalized':score(ref,hyp,search) if not unknown and not missing else None};strict_score=scores['strict_nfc_diplomatic'];conditions={'exact_id_coverage':not unknown and not missing,'all_images_declared_inspected':inspected==expected_paths,'strict_cer_zero':strict_score is not None and strict_score['cer']==0,'all_regions_exact':strict_score is not None and strict_score['exact_regions']==16}
 report={'schema':'bbvlm.bnf-region-ocr-a30-report/1','page':s['page']['page'],'scope':'16 deterministic oracle TextRegion polygon crops from unopened manually transcribed French BnF PAGE; one blind Luna pass','candidate':{'reader':pred.get('reader'),'uncertain_ids':pred.get('uncertain_ids',[]),'unknown_ids':unknown,'missing_ids':missing},'scores':scores,'gate_conditions':conditions,'conditional_gate_passed':all(conditions.values()),'cost':{'new_vlm_tasks':1,'evaluator_seconds':time.perf_counter()-started},'accepted_for_project_completion_gate':False,'reference_status':'BnF-described manual transcription; not independently adjudicated perfect truth','limitations':['Oracle region polygons and selected crops; no full-page coverage.','Region-level reference has no word boxes.','One page and one reader.'],'invariants':{'sealed_before_open':True,'reader_denied_reference_xml_and_mapping':True,'originals_unchanged':True}}
 (EXP/'output').mkdir(parents=True,exist_ok=True);(EXP/'output/report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
