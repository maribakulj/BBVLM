"""Evaluate native predicted lines against PAGE references, geometry-only matching.

One-to-one maximum-cardinality matching at line bbox IoU>=.5, then maximize IoU.
Report coverage, splits/merges and recognized CER separately. This is a diagnostic
baseline, not a leaderboard-compatible reading-order metric.
"""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from lxml import etree as E
from scipy.optimize import linear_sum_assignment
from bbvlm.metrics import text_scores
ROOT=Path(__file__).resolve().parents[1]

def lines(path):
    root=E.parse(str(path));ns={'p':root.getroot().nsmap[None]};rows=[]
    for n in root.findall('.//p:TextLine',ns):
        pts=np.array([list(map(float,p.split(','))) for p in n.find('p:Coords',ns).get('points').split()]);a=[*pts.min(0),*pts.max(0)]
        rows.append({'id':n.get('id'),'text':n.findtext('p:TextEquiv/p:Unicode',default='',namespaces=ns),'box':a})
    return rows

def match(ref,pred):
    a=np.array([r['box'] for r in ref]);b=np.array([r['box'] for r in pred]);inter=np.maximum(0,np.minimum(a[:,None,2:],b[None,:,2:])-np.maximum(a[:,None,:2],b[None,:,:2])).prod(2)
    aa=np.maximum(0,a[:,2:]-a[:,:2]).prod(1);bb=np.maximum(0,b[:,2:]-b[:,:2]).prod(1)
    iou=inter/np.maximum(1,aa[:,None]+bb[None,:]-inter);valid=iou>=.5
    ri,pi=linear_sum_assignment(-(valid*(min(len(ref),len(pred))+1)+iou*valid))
    pairs=[(int(r),int(p),float(iou[r,p])) for r,p in zip(ri,pi) if valid[r,p]]
    return pairs,inter,aa,bb

if __name__=='__main__':
    results=[]
    for page_id in ['0253902-001','0401692-003','752234-003']:
        p=ROOT/'experiments/loop/end-to-end'/page_id
        if not (p/'run.json').exists():raise RuntimeError('inference not complete: '+page_id)
        source=json.loads((ROOT/'experiments/loop/cache'/page_id/'run.json').read_text())
        ref=lines(ROOT/source['source_xml']);pred=lines(p/'layout.xml');pairs,inter,aa,bb=match(ref,pred)
        mapped=[{'id':ref[r]['id'],'text':pred[h]['text']} for r,h,_ in pairs]
        matched_h={h for r,h,_ in pairs};matched_r={r for r,h,_ in pairs}
        score=text_scores(ref,mapped);extras=[pred[i] for i in range(len(pred)) if i not in matched_h]
        extra_chars=sum(len(x['text']) for x in extras)
        result={'page':page_id,'reference_lines':len(ref),'predicted_lines':len(pred),'matched_at_iou_05':len(pairs),
            'line_recall':len(pairs)/len(ref),'line_precision':len(pairs)/len(pred),
            'potential_merges':int(((inter/np.maximum(1,aa[:,None])>.5).sum(0)>1).sum()),
            'potential_splits':int(((inter/np.maximum(1,bb[None,:])>.5).sum(1)>1).sum()),
            'matched_and_missing_reference_cer':score['cer'],'unmatched_prediction_characters':extra_chars,
            'coverage_penalized_cer':(score['edits']+extra_chars)/score['characters'],
            'missing_reference_lines':[ref[i]['id'] for i in range(len(ref)) if i not in matched_r],
            'matches':[{'reference':ref[r]['id'],'prediction':pred[h]['id'],'iou':v} for r,h,v in pairs],
            'warning':'CER sums geometrically matched line errors plus missing and extra text; it is not reading-order-sensitive page CER'}
        (p/'evaluation.json').write_text(json.dumps(result,indent=2));results.append({k:v for k,v in result.items() if k not in ['matches','missing_reference_lines']})
    (ROOT/'experiments/loop/end-to-end/summary.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
