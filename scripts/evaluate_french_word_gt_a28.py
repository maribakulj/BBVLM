#!/usr/bin/env python3
"""Run the sealed A25 candidate on A28 and add fail-closed per-page gates."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import evaluate_french_holdout_a25 as core

ROOT=Path(__file__).resolve().parents[1];EXP=ROOT/'experiments/loop/french-word-gt-a28'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def compact(value):return {k:v for k,v in value.items() if k!='per_line'}

def main():
    split=json.loads((EXP/'split.json').read_text());opened=json.loads((EXP/'opened.json').read_text())
    checks={'protocol':EXP/'PROTOCOL.md','opener':ROOT/'scripts/open_french_word_gt_a28.py',
      'evaluator':ROOT/'scripts/evaluate_french_word_gt_a28.py','candidate_core_a25':ROOT/'scripts/evaluate_french_holdout_a25.py',
      'tree':ROOT/'experiments/loop/reference-a18/source/tree.json'}
    for key,path in checks.items():
        if sha(path)!=split['sealed_sha256'][key]:raise ValueError(f'sealed file changed: {key}')
    for item in opened['files']:
        if sha(EXP/'source'/item['path'])!=item['sha256']:raise ValueError(f"source changed: {item['path']}")
    core.EXP=EXP;core.SOURCE=EXP/'source';core.OUT=EXP/'output';core.main()
    report_path=EXP/'output/report.json';report=json.loads(report_path.read_text());rows,_=core.load_rows(split)
    if not rows or not all(row['words'] and row['text'].strip() for row in rows):raise ValueError('fail closed: empty line/word reference')
    boxes=json.loads((EXP/'output/boxes.json').read_text());per_page={};conditions={}
    for page in sorted({r['page'] for r in rows}):
        group=[r for r in rows if r['page']==page]
        metrics={name:core.box_metrics(group,boxes[key],name,key!='native') for name,key in
          [('pero_native','native'),('reference_forced_ctc','forced'),('ctc_raw_otsu_v1','otsu')]}
        per_page[page]={k:compact(v) for k,v in metrics.items()};o=metrics['ctc_raw_otsu_v1'];f=metrics['reference_forced_ctc'];n=metrics['pero_native']
        conditions[page]={'zero_omission':o['predicted_words']==o['reference_words'],
          'recall_iou50_eq_1':o['recall_iou50']==1.,'recall_iou80_ge_090':o['recall_iou80']>=.90,
          'mean_iou_ge_090':o['mean_iou_matched']>=.90,
          'iou80_strictly_better_both':o['recall_iou80']>f['recall_iou80'] and o['recall_iou80']>n['recall_iou80'],
          'iou50_mean_noninferior_both':o['recall_iou50']>=max(f['recall_iou50'],n['recall_iou50']) and o['mean_iou_matched']>=max(f['mean_iou_matched'],n['mean_iou_matched'])}
    report.update({'schema':'bbvlm.french-word-gt-a28/1','scope':'all eight pages of two SBB works catalogued fre; oracle line polygons/text/token order',
      'selection_intent':'catalogue-French word-box validation','observed_language_warning':'not yet independently language-adjudicated; report preserves exact source transcriptions',
      'per_page_measurements':per_page,'candidate_page_conditions':conditions,
      'candidate_conditional_gate_passed':all(all(x.values()) for x in conditions.values()),
      'accepted_for_project_completion_gate':False})
    report['invariants'].update({'implementation_frozen_before_source_open':True,'two_catalogue_french_works':True,'nonempty_reference_fail_closed':True})
    report['limitations']=['Oracle line polygons, reference text and token order: conditional geometry, not end-to-end layout.',
      'Catalogue language and PAGE granularity were used for selection; actual language mix is reported after opening.',
      'Two works and eight pages remain too small for a universal claim.',
      'Source word polygons and transcriptions are corrected external GT, not independently adjudicated perfect truth.',
      'Synthetic horizontal baselines may disadvantage PERO.']
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'counts':report['counts'],'native_ocr':{k:compact(v) for k,v in report['native_ocr'].items()},
      'measurements':{k:compact(v) for k,v in report['measurements'].items()},'per_page':per_page,
      'candidate_conditional_gate_passed':report['candidate_conditional_gate_passed']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()

