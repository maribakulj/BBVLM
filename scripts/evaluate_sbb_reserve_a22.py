"""Evaluate the one-pass Sol reserve OCR and frozen A19 box proposal."""
from pathlib import Path
import hashlib, json, time
import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.stats import fisher_exact
from bbvlm.gap_alignment import locate_words_without_recognizer
from bbvlm.metrics import edit_distance, iou
from bbvlm.ocr_conventions import transform, private_use_inventory

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/loop'
OUT=BASE/'reserve-a22'
SOURCE=BASE/'reference-a18'
CONFIG={'min_gap_height_ratio':.10,'gap_separation_ratio':1.5}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def wilson(success,total,z=1.959963984540054):
    p=success/total;d=1+z*z/total
    c=(p+z*z/(2*total))/d
    h=z*np.sqrt(p*(1-p)/total+z*z/(4*total*total))/d
    return [float(c-h),float(c+h)]

def text_score(reference,hypothesis,profile):
    fn=lambda s: transform(s,profile)
    rows=[]
    for ref in reference:
        a,b=fn(ref['text']),fn(hypothesis[ref['id']]['text'])
        rows.append({'id':ref['id'],'work':ref['work'],'characters':len(a),
                     'edits':edit_distance(a,b),'exact':a==b,
                     'reference_view':a,'hypothesis_view':b})
    chars=sum(r['characters'] for r in rows);edits=sum(r['edits'] for r in rows)
    return {'lines':len(rows),'characters':chars,'edits':edits,'cer':edits/chars if chars else None,
            'exact_lines':sum(r['exact'] for r in rows),'per_line':rows}

def main():
    started=time.perf_counter()
    opened=json.loads((OUT/'opened.json').read_text())
    assert sha(OUT/'PROTOCOL.md')==opened['protocol_sha256']
    reference=json.loads((OUT/'private-reference.json').read_text())
    response=json.loads((OUT/'sol-response.json').read_text())
    lines=response['lines'];hyp={r['id']:r for r in lines}
    ids={r['id'] for r in reference}
    assert len(hyp)==len(lines)==len(reference)==16 and set(hyp)==ids
    request=json.loads((OUT/'input/request.json').read_text())
    required={r[k] for r in request['items'] for k in ('image','original_image')}
    inspected={str(Path(p).relative_to(ROOT)) if Path(p).is_absolute() else p for p in response['inspected_images']}
    assert required <= inspected
    protected=[OUT/'PROTOCOL.md',OUT/'opened.json',OUT/'private-reference.json',OUT/'input/request.json',OUT/'AGENT_PROMPT.txt']
    protected += [ROOT/p for p in required]
    for f in opened['files']: protected.append(SOURCE/'source'/f['path'])
    before={str(p.relative_to(ROOT)):sha(p) for p in protected}
    scores={p:text_score(reference,hyp,p) for p in ('strict','glyph_decomposition_v1')}
    # WER is whitespace-token edit distance, punctuation retained.
    for profile,score in scores.items():
        word_edits=word_count=0
        for ref in reference:
            a=transform(ref['text'],profile).split();b=transform(hyp[ref['id']]['text'],profile).split()
            word_edits+=edit_distance(a,b);word_count+=len(a)
        score.update(reference_words=word_count,word_edits=word_edits,
                     wer_whitespace_tokens=word_edits/word_count if word_count else None)
    images={}
    geometry=[]
    for ref in reference:
        image_path=SOURCE/'source'/ref['source_image']
        if str(image_path) not in images: images[str(image_path)]=cv2.imread(str(image_path),cv2.IMREAD_GRAYSCALE)
        tokens=hyp[ref['id']]['text'].split()
        tic=time.perf_counter()
        pred=locate_words_without_recognizer(images[str(image_path)],ref['polygon'],ref['line_bbox'],tokens,**CONFIG)
        cpu=time.perf_counter()-tic
        gt=[w['bbox'] for w in ref['words']];boxes=pred['boxes']
        matched=[]
        if gt and boxes:
            matrix=np.array([[iou(a,b) for b in gt] for a in boxes])
            aa,bb=linear_sum_assignment(-matrix)
            matched=[float(matrix[a,b]) for a,b in zip(aa,bb)]
        geometry.append({'id':ref['id'],'work':ref['work'],'reference_words':len(gt),
          'predicted_words':len(boxes),'hypothesis_tokens':len(tokens),'reference_tokens':len(ref['text'].split()),
          'token_count_equal':len(tokens)==len(gt),'prediction':pred,'matched_ious':matched,'cpu_seconds':cpu})
    pred_total=sum(r['predicted_words'] for r in geometry);gt_total=sum(r['reference_words'] for r in geometry)
    matches={t:sum(v>=t for r in geometry for v in r['matched_ious']) for t in (.5,.8)}
    matched_all=[v for r in geometry for v in r['matched_ious']]
    proposed=[r for r in geometry if r['predicted_words']]
    geom={'lines':len(geometry),'proposed_lines':len(proposed),'abstained_lines':len(geometry)-len(proposed),
      'token_count_equal_lines':sum(r['token_count_equal'] for r in geometry),
      'reference_words':gt_total,'predicted_words':pred_total,
      'mean_iou_one_to_one_emitted':float(np.mean(matched_all)) if matched_all else None,
      'matches_iou50':matches[.5],'precision_iou50':matches[.5]/pred_total if pred_total else None,
      'recall_iou50':matches[.5]/gt_total if gt_total else None,
      'matches_iou80':matches[.8],'precision_iou80':matches[.8]/pred_total if pred_total else None,
      'recall_iou80':matches[.8]/gt_total if gt_total else None,
      'emitted_matched_words_iou_lt50':sum(v<.5 for v in matched_all),
      'proposed_lines_all_reference_words_iou_ge80':sum(r['predicted_words']==r['reference_words'] and len(r['matched_ious'])==r['reference_words'] and all(v>=.8 for v in r['matched_ious']) for r in proposed),
      'cpu_seconds':sum(r['cpu_seconds'] for r in geometry),'per_line':geometry}
    development=json.loads((BASE/'gap-ablation-a19/report.json').read_text())['sbb_conditional_geometry']
    table=[[development['proposed_lines'],development['lines']-development['proposed_lines']],
           [geom['proposed_lines'],geom['lines']-geom['proposed_lines']]]
    comparison={'a19_audit_proposed_lines':development['proposed_lines'],'a19_audit_lines':development['lines'],
      'a19_audit_rate':development['proposed_lines']/development['lines'],
      'a19_audit_wilson95':wilson(development['proposed_lines'],development['lines']),
      'a22_reserve_proposed_lines':geom['proposed_lines'],'a22_reserve_lines':geom['lines'],
      'a22_reserve_rate':geom['proposed_lines']/geom['lines'],
      'a22_reserve_wilson95':wilson(geom['proposed_lines'],geom['lines']),
      'fisher_exact_two_sided_p':float(fisher_exact(table).pvalue),
      'interpretation':'Exploratory domain-shift warning: frozen fast-path coverage fell sharply; small reserve n and sampled-line scope prevent a universal rate claim.'}
    assert before=={str(p.relative_to(ROOT)):sha(p) for p in protected}
    report={'schema':'bbvlm.sbb-reserve-a22/1','scope':'16 lines from four work-disjoint pre-frozen reserve pages; now consumed',
      'reader':'gpt-6-sol','ocr_scores':scores,'geometry':geom,'geometry_config':CONFIG,
      'development_reserve_geometry_comparison':comparison,
      'reference_status':'External SBB GT, provider plus SBB post-correction/manual page inspection; not independently adjudicated perfect truth',
      'reference_pua':private_use_inventory(''.join(r['text'] for r in reference)),
      'uncertain_ids':sorted(r['id'] for r in lines if r.get('uncertain')),
      'cost':{'new_vlm_tasks':1,'target_images':16,'context_images':16,'total_images_inspected':len(inspected),
              'tokens':None,'billed_cost':None,'new_recognizer_forwards':0,'new_layout_forwards':0,
              'cpu_wall_seconds':time.perf_counter()-started},
      'invariants':{'protocol_frozen_before_open':True,'exact_id_coverage':True,'all_required_images_inspected':True,
                    'protected_inputs_unchanged':True,'no_oracle_reader_mixture':True,'source_git_blobs_verified':True},
      'limitations':['Oracle line polygons: word geometry is conditional, not end-to-end layout',
        'One-to-one IoU matching is geometry-only; it does not certify token identity',
        'Source polygon vertex extents and half-open pixel boxes retain a one-pixel convention difference',
        'Reserve is consumed after this report and cannot be reused as independent validation',
        'No PERO baseline was run on these exact reserve lines in this task'],
      'accepted_for_project_completion_gate':False,
      'source_sha256':{'gap_alignment':sha(ROOT/'src/bbvlm/gap_alignment.py'),'ocr_conventions':sha(ROOT/'src/bbvlm/ocr_conventions.py'),
                       'agent_prompt':sha(OUT/'AGENT_PROMPT.txt'),'response':sha(OUT/'sol-response.json')},
      'protected_input_sha256':before}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'ocr':{k:{a:b for a,b in v.items() if a!='per_line'} for k,v in scores.items()},
                      'geometry':{k:v for k,v in geom.items() if k!='per_line'},'uncertain':len(report['uncertain_ids'])},indent=2))

if __name__=='__main__': main()
