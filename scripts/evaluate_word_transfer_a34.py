#!/usr/bin/env python3
"""Sealed independent transfer evaluation on three unopened SBB works."""
import hashlib,json,time
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from lxml import etree as E
import evaluate_french_holdout_a25 as core
from bbvlm.component_boxes import refine_cells,refine_cells_text,TRAILING_PUNCTUATION
from bbvlm.metrics import iou
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/loop';EXP=BASE/'word-transfer-a34'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compact(x):return {k:v for k,v in x.items() if k!='per_line'}
def bind_with_explicit_ocr_omissions(xml,regions):
    """A34 adapter: represent a PERO-empty oracle line as zero native words."""
    import re
    root=E.fromstring(xml,E.XMLParser(resolve_entities=False,no_network=True));ns=E.QName(root).namespace;q=lambda n:f'{{{ns}}}{n}'
    blocks={b.get('ID'):b for b in root.findall('.//'+q('TextBlock'))};used={e.get('ID') for e in root.iter() if e.get('ID')}
    if set(blocks)!={'block_'+r.id for r in regions}:raise ValueError('native ALTO region binding mismatch')
    for region in regions:
        block=blocks['block_'+region.id];exported=iter(block.findall(q('TextLine')))
        for line in region.lines:
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.-]*',line.id) or line.id in used:raise ValueError('bad line id')
            if (line.transcription or '').strip():
                element=next(exported,None)
                if element is None:raise ValueError('unexpected nonempty native omission')
                words=element.findall(q('String'))
                if ' '.join(w.get('CONTENT','') for w in words)!=line.transcription:raise ValueError('native diplomatic mismatch')
                for i,w in enumerate(words,1):w.set('ID',f'{line.id}_W{i:04d}')
            else:
                element=E.SubElement(block,q('TextLine'))
                pts=np.asarray(line.polygon);lo=pts.min(0);hi=pts.max(0)
                for key,value in zip(('HPOS','VPOS','WIDTH','HEIGHT'),(lo[0],lo[1],hi[0]-lo[0],hi[1]-lo[1])):element.set(key,str(int(value)))
                element.set('BBVLM_OCR_OMISSION','true')
            element.set('ID',line.id);used.add(line.id)
        if next(exported,None) is not None:raise ValueError('unbound exported native line')
    return E.tostring(root,pretty_print=True,xml_declaration=True,encoding='utf-8')
def main():
    started=time.perf_counter();s=json.loads((EXP/'split.json').read_text());opened=json.loads((EXP/'opened.json').read_text())
    checks={'protocol':EXP/'PROTOCOL.md','freeze':ROOT/'scripts/freeze_word_transfer_a34.py',
            'opener':ROOT/'scripts/open_word_transfer_a34.py','evaluator':Path(__file__),
            'core':ROOT/'scripts/evaluate_french_holdout_a25.py','components':ROOT/'src/bbvlm/component_boxes.py',
            'tree':BASE/'reference-a18/source/tree.json'}
    for k,p in checks.items():assert sha(p)==s['sealed_sha256'][k],f'sealed changed {k}'
    for x in opened['files']:assert sha(EXP/'source'/x['path'])==x['sha256']
    core.EXP=EXP;core.SOURCE=EXP/'source';core.OUT=EXP/'output';core.bind_native_alto_ids=bind_with_explicit_ocr_omissions;core.main()
    base=json.loads((EXP/'output/report.json').read_text());pred=json.loads((EXP/'output/boxes.json').read_text())
    rows,paths=core.load_rows(s);images={p:cv2.imread(str(x),cv2.IMREAD_GRAYSCALE) for p,x in paths.items()};assert all(x is not None for x in images.values())
    tick=time.perf_counter();pred['satellites']={};pred['conservative']={};diagnostics={};changes=[]
    punctuation=set(TRAILING_PUNCTUATION)-{'*'}
    for row in rows:
        forced=pred['forced'][row['id']]
        boxes,d1=refine_cells(images[row['page']],row['line_bbox'],[x['bbox'] for x in forced],'satellites')
        pred['satellites'][row['id']]=[{'text':w['text'],'bbox':b} for w,b in zip(forced,boxes)]
        boxes2,d2=refine_cells_text(images[row['page']],row['line_bbox'],forced,minimum_rescue_area=20,trailing_punctuation=punctuation)
        pred['conservative'][row['id']]=[{'text':w['text'],'bbox':b} for w,b in zip(forced,boxes2)]
        diagnostics[row['id']]={'satellites':d1,'conservative':d2}
        for i,(gt,a,b) in enumerate(zip(row['words'],pred['satellites'][row['id']],pred['conservative'][row['id']])):
            if a['bbox']!=b['bbox']:
                changes.append({'line':row['id'],'page':row['page'],'work':next(p['work'] for p in s['pages'] if p['page']==row['page']),
                    'word_index':i,'text':gt['text'],'reference':gt['bbox'],'satellites':a['bbox'],'conservative':b['bbox'],
                    'old_iou':iou(gt['bbox'],a['bbox']),'new_iou':iou(gt['bbox'],b['bbox']),
                    'delta':float(iou(gt['bbox'],b['bbox'])-iou(gt['bbox'],a['bbox']))})
    refine_seconds=time.perf_counter()-tick
    metrics={n:core.box_metrics(rows,p,n,n!='native') for n,p in pred.items()}
    page_work={x['page']:x['work'] for x in s['pages']};grouped={'page':{},'work':{}}
    for kind,values in (('page',paths),('work',s['works'])):
        for value in values:
            rr=[r for r in rows if (r['page'] if kind=='page' else page_work[r['page']])==value]
            grouped[kind][value]={n:compact(core.box_metrics(rr,p,n,n!='native')) for n,p in pred.items()}
    deltas=[x['delta'] for x in changes];paired={'changed_words':len(changes),'improved_words':sum(x>1e-9 for x in deltas),
        'regressed_words':sum(x < -1e-9 for x in deltas),'mean_delta_changed':float(np.mean(deltas)) if deltas else 0.0,
        'mean_delta_all_words':float(sum(deltas)/sum(len(r['words']) for r in rows))}
    conditions={w:{'zero_omission':grouped['work'][w]['conservative']['predicted_words']==grouped['work'][w]['conservative']['reference_words'],
        'mean_iou_noninferior_a32':grouped['work'][w]['conservative']['mean_iou_matched']>=grouped['work'][w]['satellites']['mean_iou_matched'],
        'iou80_noninferior_a32':grouped['work'][w]['conservative']['recall_iou80']>=grouped['work'][w]['satellites']['recall_iou80']} for w in s['works']}
    local_gate=bool(changes) and paired['improved_words']>0 and paired['regressed_words']==0 and all(all(v.values()) for v in conditions.values())
    canvas=Image.new('RGB',(1100,max(1,len(changes))*110),'white');draw=ImageDraw.Draw(canvas)
    for j,x in enumerate(changes):
        q=np.asarray([x[k] for k in ('reference','satellites','conservative')]);lo=np.maximum(0,q[:,:2].min(0)-8).astype(int);hi=(q[:,2:].max(0)+8).astype(int)
        im=Image.fromarray(images[x['page']][lo[1]:hi[1],lo[0]:hi[0]]).convert('RGB');scale=min(3,500/max(1,im.width),70/max(1,im.height));im=im.resize((round(im.width*scale),round(im.height*scale)))
        canvas.paste(im,(5,j*110+28));draw.text((5,j*110+4),f"{x['line']} #{x['word_index']} {x['text']} {x['old_iou']:.3f}->{x['new_iou']:.3f} old={x['satellites']} new={x['conservative']} GT={x['reference']}",fill='black')
    canvas.save(EXP/'all-changes-clean.png')
    base.update({'schema':'bbvlm.word-transfer-a34/1','scope':'three deterministically selected unopened SBB works; oracle line polygons/text/token order',
      'selection_intent':'independent cross-work geometry transfer, not French newspaper validation','works':s['works'],
      'measurements':{n:compact(m) for n,m in metrics.items()},'by_group':grouped,'paired_conservative_vs_satellites':paired,
      'candidate_work_conditions':conditions,'candidate_local_gate_passed':local_gate,
      'cost':{**base['cost'],'component_refinement_seconds_both_variants':refine_seconds,'new_vlm_tasks':0},
      'invariants':{**base['invariants'],'candidate_rule_frozen_before_source_open':True,'evaluation_adapter_amended_after_open_before_scores':True,'three_unconsumed_works':True,
                    'reference_boxes_hidden_from_refiners':True,'no_gt_replacement':True},
      'limitations':['German/Latin historical books, not French newspapers.','Oracle line polygons, reference text and token order.',
        'Synthetic baselines may disadvantage PERO native boxes.','External corrected GT is not independently adjudicated perfect truth.'],
      'accepted_for_project_completion_gate':False,'total_evaluator_seconds':time.perf_counter()-started})
    (EXP/'output/boxes.json').write_text(json.dumps(pred,ensure_ascii=False,indent=2)+'\n');(EXP/'diagnostics.json').write_text(json.dumps(diagnostics,ensure_ascii=False,indent=2)+'\n')
    (EXP/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n');(EXP/'output/report.json').write_text(json.dumps(base,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'works':s['works'],'counts':base['counts'],'measurements':base['measurements'],'paired':paired,'gate':local_gate,'cost':base['cost']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
