"""Resume deterministic experiments with a process lock and durable checkpoints.

The surrounding Codex agent supplies literature review, new candidates and visual
model calls. This driver never substitutes a simulated response for a VLM call.
Run --execute to advance all ready CPU phases; otherwise report next work.
"""
import argparse,fcntl,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/loop'
phases=[('recognition_cache','scripts/cache_newseye_pero.py','cache/752234-003/run.json'),
        ('geometry_g01','scripts/run_geometry_loop.py','geometry-g01/heldout.json'),
        ('native_end_to_end','scripts/run_pero_end_to_end.py','end-to-end/752234-003/run.json'),
        ('end_to_end_evaluation','scripts/evaluate_end_to_end.py','end-to-end/summary.json'),
        ('end_to_end_words','scripts/evaluate_end_to_end_words.py','end-to-end/word-summary.json'),
        ('reference_audit_sample','scripts/prepare_reference_audit.py','reference-audit-v1/input/request.json'),
        ('reference_structural_audit','scripts/audit_newseye_reference.py','reference-audit-v1/structural-audit.json'),
        ('reference_blind_audit','scripts/evaluate_reference_audit.py','reference-audit-v1/report.json'),
        ('cev_diagnostic','scripts/evaluate_cev.py','cev-v1/report.json'),
        ('spiritualist_reference_audit','scripts/audit_spiritualist_reference.py','spiritualist-v1/reference-audit.json'),
        ('spiritualist_normalized_import','scripts/evaluate_spiritualist_import.py','spiritualist-v1/import-0009/report.json'),
        ('spiritualist_olr_prepare','scripts/prepare_spiritualist_olr.py','spiritualist-v1/olr-0009/input/request.json'),
        ('spiritualist_olr_evaluate','scripts/evaluate_spiritualist_olr.py','spiritualist-v1/olr-0009/report.json'),
        ('spiritualist_olr_v2_prepare','scripts/prepare_spiritualist_olr_v2.py','spiritualist-v1/olr-v2-validation/input/request.json'),
        ('spiritualist_olr_v2_evaluate','scripts/evaluate_spiritualist_olr_v2.py','spiritualist-v1/olr-v2-validation/report.json'),
        ('spiritualist_olr_v3_calibrate','scripts/calibrate_spiritualist_column_order.py','spiritualist-v1/olr-v3-column/development-report.json'),
        ('spiritualist_olr_v3_evaluate','scripts/evaluate_spiritualist_column_order.py','spiritualist-v1/olr-v3-column/validation-0014-report.json'),
        ('spiritualist_semantic_v1_conventions','scripts/audit_spiritualist_semantic_conventions.py','spiritualist-v1/semantic-v1/development-conventions.json'),
        ('spiritualist_semantic_v1_prepare','scripts/prepare_spiritualist_semantic_v1.py','spiritualist-v1/semantic-v1-validation/input/request.json'),
        ('spiritualist_semantic_v1_evaluate','scripts/evaluate_spiritualist_semantic_v1.py','spiritualist-v1/semantic-v1-validation/report.json'),
        ('spiritualist_semantic_v2_calibrate','scripts/calibrate_spiritualist_header_units.py','spiritualist-v1/semantic-v2-header/development-report.json'),
        ('spiritualist_semantic_v2_prepare','scripts/prepare_spiritualist_role_filter_v2.py','spiritualist-v1/semantic-v2-header-validation/input/request.json'),
        ('spiritualist_semantic_v2_evaluate','scripts/evaluate_spiritualist_role_filter_v2.py','spiritualist-v1/semantic-v2-header-validation/report.json'),
        ('spiritualist_semantic_v3_prepare','scripts/prepare_spiritualist_faceted_v3.py','spiritualist-v1/semantic-v3-faceted-validation/input/request.json'),
        ('spiritualist_semantic_v3_evaluate','scripts/evaluate_spiritualist_faceted_v3.py','spiritualist-v1/semantic-v3-faceted-validation/report.json'),
        ('spiritualist_semantic_v4_calibrate','scripts/calibrate_spiritualist_header_geometry.py','spiritualist-v1/semantic-v4-coarse/development-report.json'),
        ('spiritualist_semantic_v4_prepare','scripts/prepare_spiritualist_coarse_v4.py','spiritualist-v1/semantic-v4-coarse-validation/input/request.json'),
        ('spiritualist_semantic_v4_evaluate','scripts/evaluate_spiritualist_coarse_v4.py','spiritualist-v1/semantic-v4-coarse-validation/report.json'),
        ('doclayout_yolo_pilot','scripts/evaluate_doclayout_yolo_pilot.py','spiritualist-v1/doclayout-yolo-pilot-0044/report.json'),
        ('spiritualist_olr_v4_calibrate','scripts/calibrate_spiritualist_column_anchors_v4.py','spiritualist-v1/olr-v4-column-anchors/development-report.json'),
        ('spiritualist_semantic_v5_prepare','scripts/prepare_spiritualist_coarse_v5.py','spiritualist-v1/semantic-v5-coarse-order-validation/input/request.json'),
        ('spiritualist_semantic_v5_evaluate','scripts/evaluate_spiritualist_coarse_v5.py','spiritualist-v1/semantic-v5-coarse-order-validation/report.json'),
        ('spiritualist_semantic_v6_split','scripts/freeze_spiritualist_semantic_v6_split.py','spiritualist-v1/semantic-v6-typography/split.json'),
        ('spiritualist_semantic_v6_calibrate','scripts/calibrate_spiritualist_typography_v6.py','spiritualist-v1/semantic-v6-typography/development-report.json'),
        ('spiritualist_semantic_v6_evaluate','scripts/evaluate_spiritualist_typography_v6.py','spiritualist-v1/semantic-v6-typography/validation-0004-report.json'),
        ('spiritualist_semantic_v6_prepare','scripts/prepare_spiritualist_coarse_v6.py','spiritualist-v1/semantic-v6-full-validation/input/request.json'),
        ('spiritualist_semantic_v6_full_evaluate','scripts/evaluate_spiritualist_coarse_v6.py','spiritualist-v1/semantic-v6-full-validation/report.json'),
        ('yolo_columns_a12','scripts/evaluate_yolo_columns.py','spiritualist-v1/yolo-columns-a12-0044/report.json'),
        ('yolo_ocr_a13_prepare','scripts/prepare_yolo_ocr.py','spiritualist-v1/yolo-ocr-a13-0044/input/request.json'),
        ('yolo_ocr_a13_evaluate','scripts/evaluate_yolo_ocr.py','spiritualist-v1/yolo-ocr-a13-0044/report.json'),
        ('column_lines_a14','scripts/run_column_line_ablation.py','spiritualist-v1/column-lines-a14-0044/report.json'),
        ('predicted_alignment_a15','scripts/run_predicted_vlm_alignment.py','spiritualist-v1/predicted-alignment-a15-0044/report.json'),
        ('ink_extension_a16c','scripts/evaluate_ink_extension_a16.py','spiritualist-v1/ink-extension-a16c-0044/report.json'),
        ('mets_profile_a17','scripts/evaluate_mets_profile_a17.py','spiritualist-v1/mets-profile-a17-0044/report.json'),
        ('sbb_reference_a18','scripts/audit_sbb_reference_a18.py','reference-a18/report.json'),
        ('sbb_blind_ocr_a18','scripts/evaluate_sbb_blind_a18.py','reference-a18/ocr-report.json'),
        ('no_recognizer_a19','scripts/evaluate_gap_ablation_a19.py','gap-ablation-a19/report.json'),
        ('ocr_conventions_a20','scripts/evaluate_ocr_conventions_a20.py','conventions-a20/report.json'),
        ('routing_a21_prepare','scripts/prepare_routing_a21.py','routing-a21/input/request.json'),
        ('routing_a21_evaluate','scripts/evaluate_routing_a21.py','routing-a21/report.json'),
        ('sbb_reserve_a22_prepare','scripts/prepare_sbb_reserve_a22.py','reserve-a22/opened.json'),
        ('sbb_reserve_a22_evaluate','scripts/evaluate_sbb_reserve_a22.py','reserve-a22/report.json'),
        ('ctc_fallback_a23','scripts/evaluate_ctc_fallback_a23.py','ctc-fallback-a23/report.json'),
        ('vlm_input_a24_prepare','scripts/prepare_vlm_input_a24.py','vlm-input-a24/input/request.json'),
        ('vlm_input_a24_evaluate','scripts/evaluate_vlm_input_a24.py','vlm-input-a24/report.json'),
        ('french_holdout_a25_freeze','scripts/freeze_french_holdout_a25.py','french-holdout-a25/split.json'),
        ('french_holdout_a25_open','scripts/open_french_holdout_a25.py','french-holdout-a25/opened.json'),
        ('french_holdout_a25_evaluate','scripts/evaluate_french_holdout_a25.py','french-holdout-a25/output/report.json'),
        ('bnf_impact_a26_download','scripts/download_bnf_corrected_archive_a26.py','bnf-impact-a26/source/archive-manifest.json'),
        ('bnf_impact_a26_freeze','scripts/freeze_bnf_impact_a26.py','bnf-impact-a26/split.json'),
        ('bnf_impact_a26_open','scripts/open_bnf_impact_a26.py','bnf-impact-a26/opened.json'),
        ('bnf_impact_a26_evaluate','scripts/evaluate_bnf_impact_a26.py','bnf-impact-a26/output/report.json'),
        ('bnf_olr_a27_freeze','scripts/freeze_bnf_olr_a27.py','bnf-impact-olr-a27/split.json'),
        ('bnf_olr_a27_prepare','scripts/prepare_bnf_olr_a27.py','bnf-impact-olr-a27/opened.json'),
        ('bnf_olr_a27_evaluate','scripts/evaluate_bnf_olr_a27.py','bnf-impact-olr-a27/output/report.json'),
        ('bnf_olr_a27_sol_escalation','scripts/evaluate_bnf_olr_a27_escalation.py','bnf-impact-olr-a27/output/sol-escalation-report.json'),
        ('french_word_a28_freeze','scripts/freeze_french_word_gt_a28.py','french-word-gt-a28/split.json'),
        ('french_word_a28_open','scripts/open_french_word_gt_a28.py','french-word-gt-a28/opened.json'),
        ('french_word_a28_evaluate','scripts/evaluate_french_word_gt_a28.py','french-word-gt-a28/output/report.json'),
        ('french_word_a28_post_audit','scripts/audit_french_word_gt_a28.py','french-word-gt-a28/post-score/report.json'),
        ('bnf_olr_a29_develop','scripts/develop_olr_continuation_a29.py','bnf-impact-olr-a29/development-report.json'),
        ('bnf_olr_a29_freeze','scripts/freeze_bnf_olr_a29.py','bnf-impact-olr-a29/split.json'),
        ('bnf_olr_a29_prepare','scripts/prepare_bnf_olr_a29.py','bnf-impact-olr-a29/opened.json'),
        ('bnf_olr_a29_evaluate','scripts/evaluate_bnf_olr_a29.py','bnf-impact-olr-a29/output/report.json'),
        ('bnf_olr_a29_post_audit','scripts/audit_bnf_olr_a29.py','bnf-impact-olr-a29/post-score/report.json'),
        ('bnf_region_ocr_a30_freeze','scripts/freeze_bnf_region_ocr_a30.py','bnf-region-ocr-a30/split.json'),
        ('bnf_region_ocr_a30_prepare','scripts/prepare_bnf_region_ocr_a30.py','bnf-region-ocr-a30/opened.json'),
        ('bnf_region_ocr_a30_evaluate','scripts/evaluate_bnf_region_ocr_a30.py','bnf-region-ocr-a30/output/report.json'),
        ('bnf_region_ocr_a30_sol','scripts/evaluate_bnf_region_ocr_a30_sol.py','bnf-region-ocr-a30/output/sol-report.json'),
        ('bnf_region_ocr_a30_post_audit','scripts/audit_bnf_region_ocr_a30.py','bnf-region-ocr-a30/post-score/report.json'),
        ('unmasked_a31_prepare','scripts/prepare_unmasked_a31.py','unmasked-a31/manifest.json'),
        ('unmasked_a31_evaluate','scripts/evaluate_unmasked_a31.py','unmasked-a31/report.json'),
        ('component_boxes_a32','scripts/evaluate_component_boxes_a32.py','component-boxes-a32/report.json'),
        ('component_audit_a32','scripts/audit_component_boxes_a32.py','component-boxes-a32/regressions-clean.png'),
        ('text_punctuation_a33','scripts/evaluate_text_punctuation_a33.py','text-punctuation-a33/report.json'),
        ('word_transfer_a34_freeze','scripts/freeze_word_transfer_a34.py','word-transfer-a34/split.json'),
        ('word_transfer_a34_open','scripts/open_word_transfer_a34.py','word-transfer-a34/opened.json'),
        ('word_transfer_a34_evaluate','scripts/evaluate_word_transfer_a34.py','word-transfer-a34/output/report.json'),
        ('native_refinement_a35','scripts/evaluate_native_refinement_a35.py','native-refinement-a35/report.json'),
        ('native_refinement_a35_audit','scripts/audit_native_refinement_a35.py','native-refinement-a35/regressions-clean.png')]

def checkpoint():
    p=json.loads((BASE/'protocol.json').read_text());gates=dict(p['completion_gates'])
    # A conditional two-page result is recorded separately from the broader gate.
    g=BASE/'geometry-g01/heldout.json'
    evidence={'conditional_word_geometry':json.loads(g.read_text())['gate_passed'] if g.exists() else None}
    audit=BASE/'reference-audit-v1/report.json';structural=BASE/'reference-audit-v1/structural-audit.json'
    if audit.exists():
        a=json.loads(audit.read_text());evidence['newseye_random_audit']={
          'sample_size':a['sample_size'],'triage_signal_rate':a['triage_signal_rate'],
          'wilson95':a['triage_signal_wilson95'],'status':'reference_rejected_for_superiority_claims_pending_adjudication'}
    if structural.exists():
        s=json.loads(structural.read_text());evidence['newseye_structural_audit']=s['totals']
    spiritualist=BASE/'spiritualist-v1/reference-audit.json'
    if spiritualist.exists():
        s=json.loads(spiritualist.read_text());evidence['spiritualist_reference_audit']={
          'files':s['files'],'words':s['totals']['words'],'xsd_valid_pages':s['totals']['xsd_valid_pages'],
          'word_overlap_ge_25pct_rate':s['rates']['adjacent_overlap_ge_25pct_per_word'],
          'words_outside_line_rate':s['rates']['words_outside_line_bbox'],
          'semantic_units':s['normalized_import']['semantic_units'],
          'decision':s['decision']}
    olr=BASE/'spiritualist-v1/olr-0009/report.json'
    if olr.exists():
        o=json.loads(olr.read_text());evidence['spiritualist_blind_olr_development']={
          'raw_structural_valid':o['raw_structural_valid'],
          'reading_order_pair_accuracy_diagnostic':o['reading_order_pair_accuracy_known_subset'],
          'semantic_group_pair_f1_diagnostic':o['semantic_group_pair_f1'],
          'role_accuracy_diagnostic':o['role_accuracy'],
          'accepted_for_gate':o['diagnostic_scores_accepted_for_gate']}
    olr2=BASE/'spiritualist-v1/olr-v2-validation/report.json'
    if olr2.exists():
        o=json.loads(olr2.read_text());evidence['spiritualist_blind_olr_validation_v2']={
          'pages':[p['page'] for p in o['pages']],
          'raw_structural_valid':o['raw_structural_valid'],
          'aggregate':o['aggregate'],'content_gate_passed':o['content_gate_passed'],
          'accepted_for_project_completion_gate':o['accepted_for_project_completion_gate']}
    olr3=BASE/'spiritualist-v1/olr-v3-column/validation-0014-report.json'
    if olr3.exists():
        o=json.loads(olr3.read_text());evidence['spiritualist_column_order_validation_v3']={
          'page':o['page'],'scope':o['scope'],'vlm_passes':o['passes']['vlm'],
          'reading_order_pair_accuracy':o['reading_order_pair_accuracy'],
          'gate_passed':o['gate']['passed'],
          'accepted_for_project_completion_gate':o['accepted_for_project_completion_gate']}
    semantic=BASE/'spiritualist-v1/semantic-v1-validation/report.json'
    if semantic.exists():
        o=json.loads(semantic.read_text());m=o.get('metrics') or {};evidence['spiritualist_semantic_validation_v1']={
          'page':o['page'],'raw_structural_valid':o['raw_structural_valid'],
          'eligibility_f1':m.get('eligibility_f1'),'role_accuracy':m.get('role_accuracy'),
          'semantic_group_pair_f1':m.get('semantic_group_pair_f1'),
          'semantic_group_bcubed_f1':m.get('semantic_group_bcubed_f1'),
          'combined_order_pair_recall':m.get('combined_order_pair_recall'),
          'content_gate_passed':o['content_gate_passed'],
          'accepted_for_project_completion_gate':o['accepted_for_project_completion_gate']}
    semantic2=BASE/'spiritualist-v1/semantic-v2-header-validation/report.json'
    if semantic2.exists():
        o=json.loads(semantic2.read_text());m=o.get('metrics') or {};evidence['spiritualist_semantic_validation_v2_header']={
          'page':o['page'],'raw_structural_valid':o['raw_structural_valid'],
          'eligibility_f1':m.get('eligibility_f1'),'role_accuracy':m.get('role_accuracy'),
          'semantic_group_pair_f1':m.get('semantic_group_pair_f1'),
          'semantic_group_bcubed_f1':m.get('semantic_group_bcubed_f1'),
          'combined_order_pair_recall':m.get('combined_order_pair_recall'),
          'content_gate_passed':o['content_gate_passed'],
          'accepted_for_project_completion_gate':o['accepted_for_project_completion_gate']}
    semantic3=BASE/'spiritualist-v1/semantic-v3-faceted-validation/report.json'
    if semantic3.exists():
        o=json.loads(semantic3.read_text());m=o.get('metrics') or {};evidence['spiritualist_semantic_validation_v3_faceted']={
          'page':o['page'],'raw_structural_valid':o['raw_structural_valid'],
          'eligibility_f1':m.get('eligibility_f1'),'physical_role_accuracy':m.get('physical_role_accuracy'),
          'semantic_group_pair_f1':m.get('semantic_group_pair_f1'),
          'semantic_group_bcubed_f1':m.get('semantic_group_bcubed_f1'),
          'combined_order_pair_recall':m.get('combined_order_pair_recall'),
          'editorial_genre_scored':o['editorial_genre_scored'],'content_gate_passed':o['content_gate_passed'],
          'accepted_for_project_completion_gate':o['accepted_for_project_completion_gate']}
    semantic4=BASE/'spiritualist-v1/semantic-v4-coarse-validation/report.json'
    if semantic4.exists():
        o=json.loads(semantic4.read_text());m=o.get('metrics') or {};evidence['spiritualist_semantic_validation_v4_coarse']={
          'page':o['page'],'raw_structural_valid':o['raw_structural_valid'],
          'eligibility_f1':m.get('eligibility_f1'),'coarse_role_accuracy':m.get('coarse_role_accuracy'),
          'fine_physical_role_accuracy':m.get('fine_physical_role_accuracy'),
          'semantic_group_pair_f1':m.get('semantic_group_pair_f1'),
          'semantic_group_bcubed_f1':m.get('semantic_group_bcubed_f1'),
          'combined_order_pair_recall':m.get('combined_order_pair_recall'),
          'editorial_genre_scored':o['editorial_genre_scored'],'content_gate_passed':o['content_gate_passed'],
          'accepted_for_project_completion_gate':o['accepted_for_project_completion_gate']}
    semantic5=BASE/'spiritualist-v1/semantic-v5-coarse-order-validation/report.json'
    if semantic5.exists():
        o=json.loads(semantic5.read_text());m=o.get('metrics') or {};evidence['spiritualist_semantic_validation_v5_coarse_order']={
          'page':o['page'],'raw_structural_valid':o['raw_structural_valid'],
          'eligibility_f1':m.get('eligibility_f1'),'coarse_role_accuracy':m.get('coarse_role_accuracy'),
          'fine_physical_role_accuracy':m.get('fine_physical_role_accuracy'),
          'semantic_group_pair_f1':m.get('semantic_group_pair_f1'),
          'semantic_group_bcubed_f1':m.get('semantic_group_bcubed_f1'),
          'combined_order_pair_recall':m.get('combined_order_pair_recall'),
          'editorial_genre_scored':o['editorial_genre_scored'],'content_gate_passed':o['content_gate_passed'],
          'accepted_for_project_completion_gate':o['accepted_for_project_completion_gate']}
    yolo=BASE/'spiritualist-v1/doclayout-yolo-pilot-0044/report.json'
    if yolo.exists():
        o=json.loads(yolo.read_text());evidence['doclayout_yolo_consumed_page_diagnostic']={
          'page':o['page'],'runtime_seconds':o['runtime_seconds'],'reference_regions':o['reference_regions'],
          'predictions':o['predictions'],'reference_union_coverage':o['reference_union_coverage'],
          'iou50_recall':o['greedy_one_to_one_iou']['0.5']['recall'],'accepted_for_project_completion_gate':False}
    semantic6=BASE/'spiritualist-v1/semantic-v6-typography/validation-0004-report.json'
    if semantic6.exists():
        o=json.loads(semantic6.read_text());m=o['metrics'];evidence['spiritualist_semantic_validation_v6_typography']={
          'page':o['page'],'scope':o['scope'],'vlm_passes':o['passes']['vlm'],
          'fine_role_accuracy':m['fine_role_accuracy'],
          'semantic_group_pair_f1':m['semantic_group_pair_f1'],
          'order_pair_accuracy':m['order_pair_accuracy'],
          'content_gate_passed':o['content_gate_passed'],
          'accepted_for_project_completion_gate':o['accepted_for_project_completion_gate']}
    semantic6full=BASE/'spiritualist-v1/semantic-v6-full-validation/report.json'
    if semantic6full.exists():
        o=json.loads(semantic6full.read_text());m=o['metrics'];evidence['spiritualist_semantic_validation_v6_full']={
          'page':o['page'],'reader':o['reader'],'raw_structural_valid':o['raw_structural_valid'],
          'eligibility_precision':m['eligibility_precision'],'eligibility_recall':m['eligibility_recall'],
          'coarse_role_accuracy':m['coarse_role_accuracy'],'fine_physical_role_accuracy':m['fine_physical_role_accuracy'],
          'semantic_group_pair_f1':m['semantic_group_pair_f1'],
          'combined_order_pair_recall':m['combined_order_pair_recall'],
          'content_gate_passed':o['content_gate_passed'],
          'accepted_for_project_completion_gate':o['accepted_for_project_completion_gate']}
    for key,relative in [('yolo_columns_a12','spiritualist-v1/yolo-columns-a12-0044/report.json'),
                         ('yolo_ocr_a13','spiritualist-v1/yolo-ocr-a13-0044/report.json')]:
        path=BASE/relative
        if path.exists():
            o=json.loads(path.read_text())
            evidence[key]={k:v for k,v in o.items() if k in ('scope','status','cost','metrics','new_passes','accepted_for_project_completion_gate')}
            if 'scores' in o:
                evidence[key]['scores']={k:{a:b for a,b in v.items() if a!='per_line'} for k,v in o['scores'].items()}
    for key,relative in [('column_lines_a14','spiritualist-v1/column-lines-a14-0044/report.json'),
                         ('predicted_alignment_a15','spiritualist-v1/predicted-alignment-a15-0044/report.json')]:
        path=BASE/relative
        if path.exists():
            o=json.loads(path.read_text())
            evidence[key]={k:v for k,v in o.items() if k not in ('binding','reference_xml_sha256','raw_detection_sha256')}
    for suffix in ('a16a','a16b','a16c'):
        path=BASE/f'spiritualist-v1/ink-extension-{suffix}-0044/report.json'
        if path.exists():
            o=json.loads(path.read_text());evidence[f'ink_extension_{suffix}']={
              k:v for k,v in o.items() if k not in ('per_line','per_word')}
    a17=BASE/'spiritualist-v1/mets-profile-a17-0044/report.json'
    if a17.exists():
        o=json.loads(a17.read_text());evidence['mets_profile_a17']={
          k:v for k,v in o.items() if k not in ('input_graph_sha256','source_image_sha256_verified_before_export')}
    for key,relative in [('sbb_reference_a18','reference-a18/report.json'),
                         ('sbb_blind_ocr_a18','reference-a18/ocr-report.json'),
                         ('no_recognizer_a19','gap-ablation-a19/report.json')]:
        path=BASE/relative
        if path.exists():
            o=json.loads(path.read_text())
            evidence[key]={k:v for k,v in o.items() if not k.startswith('per_line') and k!='files'}
            if 'scores' in o:
                evidence[key]['scores']={k:{a:b for a,b in v.items() if a!='per_line'} for k,v in o['scores'].items()}
    for key, relative in [('ocr_conventions_a20','conventions-a20/report.json'),
                          ('routing_a21','routing-a21/report.json')]:
        path=BASE/relative
        if path.exists():
            o=json.loads(path.read_text())
            evidence[key]={k:v for k,v in o.items() if k not in ('scores','protected_input_sha256','source_sha256')}
            evidence[key]['scores']={name:{profile:{k:v for k,v in score.items() if k!='per_line'}
              for profile,score in profiles.items()} for name,profiles in o['scores'].items()}
    a22=BASE/'reserve-a22/report.json'
    if a22.exists():
        o=json.loads(a22.read_text())
        evidence['sbb_reserve_a22']={
          'scope':o['scope'],'reader':o['reader'],
          'ocr_scores':{p:{k:v for k,v in s.items() if k!='per_line'} for p,s in o['ocr_scores'].items()},
          'geometry':{k:v for k,v in o['geometry'].items() if k!='per_line'},
          'development_reserve_geometry_comparison':o['development_reserve_geometry_comparison'],
          'cost':o['cost'],'invariants':o['invariants'],
          'accepted_for_project_completion_gate':o['accepted_for_project_completion_gate']}
    a23=BASE/'ctc-fallback-a23/report.json'
    if a23.exists():
        o=json.loads(a23.read_text());evidence['ctc_fallback_a23']={
          'scope':o['scope'],'model':o['model'],'cost':o['cost'],
          'native_ocr_profiles':o['native_ocr'].get('profiles'),
          'measurements':{name:{k:v for k,v in m.items() if k!='per_line'} for name,m in o['measurements'].items()},
          'invariants':o['invariants'],'accepted_for_project_completion_gate':o['accepted_for_project_completion_gate']}
    a24=BASE/'vlm-input-a24/report.json'
    if a24.exists():
        o=json.loads(a24.read_text());evidence['vlm_input_a24']={
          'scope':o['scope'],'reader':o['reader'],'new_vlm_tasks':o['new_vlm_tasks'],
          'scores':{p:{name:{k:v for k,v in s.items() if k!='per_line'} for name,s in methods.items()}
                    for p,methods in o['scores'].items()},
          'accepted_for_project_completion_gate':o['accepted_for_project_completion_gate']}
    a25=BASE/'french-holdout-a25/output/report.json'
    if a25.exists():
        o=json.loads(a25.read_text());evidence['ctc_otsu_a25']={
          'scope':o['scope'],'observed_language_warning':o['observed_language_warning'],
          'counts':o['counts'],'model':o['model'],'cost':o['cost'],
          'native_ocr':{p:{k:v for k,v in s.items() if k!='per_line'} for p,s in o['native_ocr'].items()},
          'measurements':{name:{k:v for k,v in m.items() if k!='per_line'} for name,m in o['measurements'].items()},
          'candidate_local_gate_passed':o['candidate_local_gate_passed'],
          'invariants':o['invariants'],'accepted_for_project_completion_gate':o['accepted_for_project_completion_gate']}
    a26=BASE/'bnf-impact-a26/output/report.json'
    if a26.exists():
        o=json.loads(a26.read_text());evidence['bnf_impact_a26_structural_failure']={
          'counts':o['counts'],'vacuous_gate_value_rejected':o.get('candidate_conditional_gate_passed'),
          'valid_score':False,'reason':'selected PAGE files have zero TextLine/Word/Glyph; retained only as negative evidence',
          'accepted_for_project_completion_gate':False}
    a27=BASE/'bnf-impact-olr-a27/output/report.json'
    if a27.exists():
        o=json.loads(a27.read_text());evidence['bnf_impact_blind_stream_olr_a27']={
          'scope':o['scope'],'counts':o['counts'],'candidate':o['candidate'],
          'geometry_oracle_role_baseline':o['geometry_oracle_role_baseline'],
          'conditional_gate_passed':o['conditional_gate_passed'],'accepted_for_project_completion_gate':False}
    a27sol=BASE/'bnf-impact-olr-a27/output/sol-escalation-report.json'
    if a27sol.exists():
        o=json.loads(a27sol.read_text());evidence['bnf_impact_stream_olr_a27_sol_escalation']={
          'status':o['status'],'scope':o['scope'],'counts':o['counts'],'candidate':o['candidate'],
          'comparison':o['comparison'],'cost':o['cost'],'accepted_for_project_completion_gate':False}
    a28=BASE/'french-word-gt-a28/output/report.json'
    if a28.exists():
        o=json.loads(a28.read_text());evidence['french_sbb_word_gt_a28']={
          'scope':o['scope'],'counts':o['counts'],'cost':o['cost'],
          'native_ocr':{p:{k:v for k,v in s.items() if k!='per_line'} for p,s in o['native_ocr'].items()},
          'measurements':{name:{k:v for k,v in m.items() if k!='per_line'} for name,m in o['measurements'].items()},
          'candidate_conditional_gate_passed':o['candidate_conditional_gate_passed'],
          'invariants':o['invariants'],'accepted_for_project_completion_gate':False}
    a29dev=BASE/'bnf-impact-olr-a29/development-report.json'
    if a29dev.exists():
        o=json.loads(a29dev.read_text());evidence['bnf_olr_continuation_a29_development']={
          'status':o['status'],'parameters':o['parameters'],'counts':o['counts'],
          'raw':o['raw'],'merged':o['merged'],'accepted_for_project_completion_gate':False}
    a29=BASE/'bnf-impact-olr-a29/output/report.json'
    if a29.exists():
        o=json.loads(a29.read_text());evidence['bnf_impact_blind_stream_olr_a29']={
          'scope':o['scope'],'counts':o['counts'],'eligibility':o['eligibility'],
          'raw_vlm':o['raw_vlm'],'merged':o['merged'],
          'geometry_oracle_role_baseline':o['geometry_oracle_role_baseline'],
          'conditional_gate_passed':o['conditional_gate_passed'],
          'accepted_for_project_completion_gate':False}
    a30=BASE/'bnf-region-ocr-a30/output/report.json'
    if a30.exists():
        o=json.loads(a30.read_text());evidence['bnf_region_ocr_a30_primary']={
          'page':o['page'],'scope':o['scope'],'candidate':o['candidate'],
          'strict_nfc_diplomatic':{k:v for k,v in o['scores']['strict_nfc_diplomatic'].items() if k!='per_region'},
          'conditional_gate_passed':o['conditional_gate_passed'],
          'reference_status':o['reference_status'],'accepted_for_project_completion_gate':False}
    a30sol=BASE/'bnf-region-ocr-a30/output/sol-report.json'
    if a30sol.exists():
        o=json.loads(a30sol.read_text());evidence['bnf_region_ocr_a30_sol_posthoc']={
          'status':o['status'],'candidate':o['candidate'],
          'strict_nfc_diplomatic':{k:v for k,v in o['scores']['strict_nfc_diplomatic'].items() if k!='per_region'},
          'diagnostic_zero_cer':o['diagnostic_zero_cer'],'accepted_for_project_completion_gate':False}
    a31=BASE/'unmasked-a31/report.json'
    if a31.exists():
        o=json.loads(a31.read_text());evidence['unmasked_context_a31']={
          'status':o['status'],'primary_metric':o['primary_metric'],
          'scores':{name:{p:{k:v for k,v in s.items() if k!='per_region'} for p,s in profiles.items()} for name,profiles in o['scores'].items()},
          'improved_ids':o['improved_ids'],'regressed_ids':o['regressed_ids'],
          'cost':o['cost'],'accepted_for_project_completion_gate':False}
    a32=BASE/'component-boxes-a32/report.json'
    if a32.exists():
        o=json.loads(a32.read_text());evidence['component_boxes_a32_development']={
          'status':o['status'],'scope':o['scope'],'counts':o['counts'],
          'measurements':o['measurements'],'paired_against_raw_otsu':o['paired_against_raw_otsu'],
          'cost':o['cost'],'invariants':o['invariants'],'accepted_for_project_completion_gate':False}
    a33=BASE/'text-punctuation-a33/report.json'
    if a33.exists():
        o=json.loads(a33.read_text());evidence['text_punctuation_a33_development']={
          'status':o['status'],'scope':o['scope'],'counts':o['counts'],
          'measurements':o['measurements'],'paired_against_a32_satellites':o['paired_against_a32_satellites'],
          'cost':o['cost'],'invariants':o['invariants'],'accepted_for_project_completion_gate':False}
    a34=BASE/'word-transfer-a34/output/report.json'
    if a34.exists():
        o=json.loads(a34.read_text());evidence['word_transfer_a34_independent_geometry']={
          'scope':o['scope'],'selection_intent':o['selection_intent'],'counts':o['counts'],
          'measurements':o['measurements'],
          'paired_conservative_vs_satellites':o['paired_conservative_vs_satellites'],
          'candidate_local_gate_passed':o['candidate_local_gate_passed'],
          'candidate_work_conditions':o['candidate_work_conditions'],
          'cost':o['cost'],'invariants':o['invariants'],'limitations':o['limitations'],
          'accepted_for_project_completion_gate':False}
    native_a35=BASE/'native-refinement-a35/report.json'
    if native_a35.exists():
        o=json.loads(native_a35.read_text())
        evidence['native_refinement_a35']={**{k:v for k,v in o.items() if k!='datasets'},
          'datasets':{k:{a:b for a,b in v.items() if a!='by_page'} for k,v in o['datasets'].items()}}
    state={'schema':'bbvlm.loop-checkpoint/1','updated_unix':time.time(),'status':'in_progress',
      'phases':[{'id':name,'complete':(BASE/result).exists(),'script':script,'result':result} for name,script,result in phases],
      'completion_gates':gates,'evidence':evidence,
      'model_policy':p['model_policy'],
      'next_research':['A35 consumed diagnostic: unchanged A32 with recognized text preserves most oracle-text gain (French IoU80 .806617 vs native .110667; German/Latin .559571 vs .190376). Joint exact-text+IoU80 remains .732459/.420887. No new inference; remaining oracle line geometry and visual punctuation/neighbor-ink failures prevent promotion. Next test predicted lines on a newly frozen diverse reference set. Do not retune consumed A28/A34. VLM value must be measured in lexical/OLR/semantic output rather than attributed to this cheap geometry stage.',
        'A34 independent geometry transfer on 12 unopened SBB pages (4759 words): A32 beats PERO native in every work and globally (mean IoU .812303 vs .654863; IoU80 .589410 vs .190376), but is not perfect and uses oracle lines/text/order. Frozen conservative A34 fails: 1/7 changed words improves, 6 regress, mean delta all -.000087. Keep A32, reject A34. Adapter was mechanically amended after open/before scores, so no pristine implementation-freeze claim. Next geometry hypothesis must use CTC character spans or attachment confidence and a new independent set, not retune consumed A34.',
        'Schema audit: inspected DAHN, TAPUS and Reichsanzeiger-GT examples contain lines/text tokens but no geometric Word nodes. Never synthesize word-box GT from token counts; seek genuine French Word polygons or independent human adjudication.',
        'A33 consumed A28 development rejects naive text-guided punctuation rescue: 4/11 changed words improve, 7 regress; mean IoU .893795->.893394 and IoU80 .817456->.816885, 1.467 s CPU. Keep A32, not A33. Post-score only: gains have area 27-69 px; six losses 5-15 and the seventh is star-triggered. Freeze area-minimum/no-star rule before any independent validation; never present a tuned A28 score.',
        'A32 consumed A28 development: component+satellite filter increases mean IoU .83882->.89379 and IoU80 recall .68454->.81746 in .726 s extra CPU, but regresses 15 words including three visually confirmed punctuation losses. Keep as development candidate only; investigate text-aware punctuation/component attachment without deleting faint detached marks, then freeze new independent data. See component-boxes-a32/RESULTS.md. No new VLM/OCR inference in A32.',
        'User clarified that normalized operational CER, not diplomatic Unicode identity, is the primary OCR target. Preserve strict diagnostic and original historical gates; specify verified Gallica/Exalead-compatible normalization before new independent evaluation. A31 tests unmasked/overlay-free target plus visible context with a blind fresh Sol reader on consumed A30; consult its report, never mistake the old white margin for real context.',
        'A30 primary blind Luna OCR on 16 deterministic polygon crops from unopened BnF page 00123532 is not zero: strict NFC CER 1.7310%, 2/16 exact. Separate Unicode hyphen convention from lexical errors, independently adjudicate flagged manual-reference anomalies, and do not promote the post-hoc Sol escalation.',
        'A28 sealed French word GT: on 1753 words from 8 pages/2 catalogue-French works, CTC+raw-Otsu improves PERO-native recall IoU50 68.91%->93.44% and IoU80 11.07%->68.45%, but the preregistered per-page gate fails (not perfect). Worst cases mix neighboring ink/bleed-through and reference-box convention; develop a component/baseline-band variant only on consumed pages, then seek a new unopened French word-box source before validation.',
        'A27 consumed OLR: Luna abstained as 234 singletons. Targeted blind Sol produced 34 pure substreams for 13 OrderedGroups, pair F1 0.5906 versus geometry+oracle-role 0.5052, with no cross-group merges but recall 0.419. Develop a CPU continuation merger on consumed A27, then freeze a new BnF page; preserve article truth as a separate human-adjudication gate.',
        'A26 failure: reject its vacuous empty-reference gate. BnF IMPACT has 0 TextLine/Word/Glyph and cannot validate word boxes or OCR.',
        'A25 external diagnostic: CTC separators plus raw line Otsu cover 1097/1097 words, recall IoU50 99.45% and IoU80 84.41% versus PERO-native 84.32%/16.77%. Do not promote: implementation was sealed after opening, the supposed French work is German, and line/text/token order are oracle.',
        'A24 consumed-data input ablation: one Sol pass over full-page locator + 2x context + 4x line worsened strict CER 11.62% to 12.22% and decomposed CER 4.86% to 5.01%. Resolution/context alone does not explain the reported Claude/Gemini zero; obtain their exact images, prompts, outputs and scoring convention or reproduce on a newly frozen common set.',
        'A23 consumed-data CTC diagnostic: PERO native decomposed CER 4.58%, Sol A22 4.86%; neither is zero. One CPU recognition batch took 1.81 s for 16 oracle lines, forced alignment 0.13 s. Hybrid boxes cover 121/121 but only 19.83% IoU80; post-hoc Otsu reaches 91.74% IoU50 but cannot be promoted. Freeze an Otsu/line-clipped candidate on development, then evaluate a new independent word-box holdout.',
        'A22 reserve consumed: frozen no-recognizer boxes are precise on 7 emissions (IoU80 precision 1.0) but recall 5.79%; keep only as a fast path. Never retune or relabel A22 as independent.',
        'A19: no-recognizer projection proposes 50/94 oracle lines (294/623 words), IoU 0.945 on emitted words but misses/false routing remain; 18/20 cached predicted VLM lines proposed. Not yet safe or cheaper end-to-end. Compare CTC baseline and hybrid on frozen reserve after development-only router work.',
        'User priority: minimal PERO stages, joint OCR/semantic/evidence VLM pass, selective CTC only. See ARCHITECTURE_A19.md; do not justify VLM by wrapping full PERO or by counting cached inference as free.',
        'French references: BnF manually corrected non-NewsEye press sets (Europeana/internal/IMPACT), primary catalogue read; bytes not downloaded yet. Do not confuse Gallica machine ALTO with GT.',
        'A10/A11 use source regions AND source line geometry/text for typography; 0004/0010 consumed, NOT image-only end-to-end tests',
        'Candidate OCR-only: OCR-D-GT-VD-SBB (348 pages, level 3, manual inspection, claimed 99.95% capture; mainly books/German-Latin)',
        'Evaluate VLM on predicted French crops, not only oracle German lines',
        'Measure geometry with predicted text and lines; protect ascenders/descenders in G02 before freezing a new split',
        'Freeze a new diverse independent holdout before testing detector/refinement changes',
        'A14: retain whole predicted lines, reject imposed overlapping column regions (635 fragments from 416 raw lines); validate on diverse untouched pages after freezing',
        'A16: additive ink recovers visible terminal punctuation on consumed 0044, but A16a changes 179/184 and A16b 72/184 words; keep A16c four-token edge-punctuation proposal in review and validate on a newly frozen independent set before promotion',
        'Audit readable footnote convention on 0010, freeze abstention/review policy on development only, then test untouched page without retuning',
        'Evaluate the column-order fast path on predicted regions and add an ambiguity router before any general claim',
        'Freeze any revised semantic OLR protocol before using 0044/0050; never retune on consumed 0003/0008/0014/0015/0029/0039',
        'A17: METS links image+ALTO and verifies local fixity; obtain/cache official MODS 3.8 XSD (upstream currently 403), then validate sourced bibliographic fields on a non-consumed document',
        'Evaluate retrieval with independently authored queries and relevance/evidence judgments',
        'Measure routing quality, passes, latency and token cost; preserve abstention'],
      'stop_rule':'Only mark success when independent evidence supports every gate; no claim of perfect ground truth from model agreement.'}
    if all(gates.values()):state['status']='requires_final_evidence_audit'
    target=BASE/'CHECKPOINT.json';temp=target.with_suffix('.tmp');temp.write_text(json.dumps(state,indent=2));temp.replace(target)
    return state

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');args=ap.parse_args()
    with (BASE/'runner.lock').open('w') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SystemExit('another iteration is active')
        if args.execute:
            env=dict(os.environ,OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',PYTHONPATH=str(ROOT/'src'))
            for name,script,result in phases:
                if (BASE/result).exists():continue
                log=BASE/(name+'.log');start=time.time()
                with log.open('a') as out:r=subprocess.run([str(ROOT/'.venv/bin/python'),script],cwd=ROOT,env=env,stdout=out,stderr=subprocess.STDOUT)
                with (BASE/'events.jsonl').open('a') as out:out.write(json.dumps({'phase':name,'start':start,'end':time.time(),'returncode':r.returncode,'script_sha256':hashlib.sha256((ROOT/script).read_bytes()).hexdigest()})+'\n')
                checkpoint()
                if r.returncode:raise SystemExit('phase failed; see '+str(log))
        print(json.dumps(checkpoint(),indent=2))
if __name__=='__main__':main()
