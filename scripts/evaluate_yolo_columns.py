"""A12: re-use real YOLO predictions as columns, NOT as reference block copies.

Prediction precedes loading evaluation XML; consumed 0044 is diagnostic only.
Line rectangles are provisional crop-risk probes, not certified ink/word GT.
"""
from collections import defaultdict
from pathlib import Path
import hashlib,itertools,json,time
from lxml import etree as E
from bbvlm.columns import propose_column_windows

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/loop/spiritualist-v1'
OUT=BASE/'yolo-columns-a12-0044'
NS={'a':'http://www.loc.gov/standards/alto/ns-v4#'}


def intersection(a,b):
    return max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))


def area(b):
    return max(0,b[2]-b[0])*max(0,b[3]-b[1])


def bbox(node):
    x,y,w,h=[float(node.get(k)) for k in ('HPOS','VPOS','WIDTH','HEIGHT')]
    return [x,y,x+w,y+h]


def main():
    source=BASE/'doclayout-yolo-pilot-0044/report.json'
    cached=json.loads(source.read_text())
    # Image dimensions were established by the prior detector run/corpus.
    page_bbox=[0,0,2479,3508]
    config=json.loads((BASE/'olr-v4-column-anchors/config.json').read_text())
    params={k:config[k] for k in ('gap_ratio','top_exclusion_ratio','max_anchor_width_ratio',
                                'min_anchor_width_ratio','assign_by_overlap')}
    predictions=[dict(p,id=f'D{i:03d}') for i,p in enumerate(cached['predicted'])]
    start=time.perf_counter()
    proposal=propose_column_windows(predictions,page_bbox,order_parameters=params)
    elapsed=time.perf_counter()-start
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'proposal.json').write_text(json.dumps(proposal,indent=2)+'\n')
    # Ground truth may ONLY enter after the proposal is saved.
    path=next((ROOT/'corpora/spiritualist/alto_xml/ocr_gt_labelled').glob('0044_*.xml'))
    tree=E.parse(str(path)); pn=tree.find('.//a:Page',NS)
    assert page_bbox[2:]==[float(pn.get('WIDTH')),float(pn.get('HEIGHT'))]
    groups=defaultdict(list); refs=[]; line_rows=[]
    for b in tree.findall('.//a:TextBlock',NS):
        if int(b.get('READING_ORDER'))<0: continue
        box=bbox(b); col=b.get('COLUMN_ID'); groups[col].append(box)
        chosen=max(range(len(proposal['windows'])),key=lambda i:intersection(box,proposal['windows'][i]['core_bbox']))
        refs.append({'id':b.get('ID'),'reference_column':col,'predicted_column':chosen,
                     'bbox':box,'reading_order':int(b.get('READING_ORDER'))})
        for line in b.findall('./a:TextLine',NS):
            lb=bbox(line)
            if not area(lb): continue
            core=proposal['windows'][chosen]['core_bbox']; ctx=proposal['windows'][chosen]['context_bbox']
            line_rows.append({'id':line.get('ID'),'column':chosen,
                'core_contains':intersection(lb,core)>=area(lb)-1e-6,
                'context_contains':intersection(lb,ctx)>=area(lb)-1e-6,
                'tight_contains':any(intersection(lb,[span[0],0,span[1],3508])>=area(lb)-1e-6
                                     for span in proposal['anchor_spans_x'])})
    pairs=list(itertools.combinations(refs,2))
    pair_ok=sum((a['reference_column']==b['reference_column'])==
                (a['predicted_column']==b['predicted_column']) for a,b in pairs)
    spans=sorted(([min(b[0] for b in boxes),max(b[2] for b in boxes)] for boxes in groups.values()))
    span_scores=[]
    if len(spans)==len(proposal['anchor_spans_x']):
        for ref,pred in zip(spans,proposal['anchor_spans_x']):
            inter=max(0,min(ref[1],pred[1])-max(ref[0],pred[0]))
            span_scores.append(inter/(ref[1]-ref[0]+pred[1]-pred[0]-inter))
    mapped_order=sorted(refs,key=lambda r:(r['predicted_column'],r['bbox'][1],r['id']))
    rank={r['id']:i for i,r in enumerate(mapped_order)}
    order_pairs=list(itertools.combinations(sorted(refs,key=lambda r:r['reading_order']),2))
    order_correct=sum(rank[a['id']]<rank[b['id']] for a,b in order_pairs)
    report={'schema':'bbvlm.yolo-column-diagnostic/1','page':'0044',
        'status':'posthoc_consumed_page_not_independent_validation',
        'input':'25 cached real DocLayout-YOLO detections; no reference boxes/text in proposal',
        'detector_report_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'cost':{'new_vlm_passes':0,'new_detector_passes':0,'cached_detector_seconds':cached['runtime_seconds'],
                'column_postprocessing_seconds':elapsed},
        'metrics':{'predicted_columns':len(proposal['windows']),'reference_columns':len(groups),
            'column_pair_correct':pair_ok,'column_pair_total':len(pairs),
            'column_pair_accuracy':pair_ok/len(pairs) if pairs else None,
            'column_span_iou':span_scores,
            'reference_region_order_correct':order_correct,'reference_region_order_pairs':len(order_pairs),
            'reference_region_order_accuracy':order_correct/len(order_pairs) if order_pairs else None,
            'line_rectangles_probed':len(line_rows),
            'tight_span_lines_not_contained':sum(not x['tight_contains'] for x in line_rows),
            'core_tile_lines_not_contained':sum(not x['core_contains'] for x in line_rows),
            'context_tile_lines_not_contained':sum(not x['context_contains'] for x in line_rows),
            'retained_detections':len(proposal['retained_detection_ids']),
            'spanning_detection_count':len(proposal['spanning_region_ids'])},
        'reference_regions':refs,'line_crop_probes':line_rows,
        'limitations':['column count alone does not validate reading order',
            'order uses reference region y coordinates only in evaluator: conditional, not detector order',
            'line-box containment is not ink completeness or OCR accuracy',
            'full-height windows include masthead and overlapping context: deduplicate by geometry/IDs, never text alone',
            'same consumed page, no new independent success claim'],
        'accepted_for_project_completion_gate':False}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'metrics':report['metrics'],'cost':report['cost']},indent=2))


if __name__=='__main__': main()
