"""Frozen G01 on predicted native PERO words, evaluated against independent words.

Same recognizer and detector for both methods. Exact diplomatic token text AND
IoU determine a correct detection. No GT coordinates/text enter refinement.
"""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import cv2,numpy as np
from lxml import etree as E
from scipy.optimize import linear_sum_assignment
from bbvlm.refine import refine_words
ROOT=Path(__file__).resolve().parents[1]

def boxes_iou(a,b):
    a=np.array(a);b=np.array(b)
    inter=np.maximum(0,np.minimum(a[:,None,2:],b[None,:,2:])-np.maximum(a[:,None,:2],b[None,:,:2])).prod(2)
    return inter/np.maximum(1e-8,np.maximum(0,a[:,2:]-a[:,:2]).prod(1)[:,None]+np.maximum(0,b[:,2:]-b[:,:2]).prod(1)[None,:]-inter)

def score(ref,pred,threshold):
    rg={};pg={}
    for w in ref:rg.setdefault(w['text'],[]).append(w['box'])
    for w in pred:pg.setdefault(w['text'],[]).append(w['box'])
    tp=0
    for text in rg.keys()&pg.keys():
        iou=boxes_iou(rg[text],pg[text]);valid=iou>=threshold;r,c=linear_sum_assignment(-(valid*(min(iou.shape)+1)+iou*valid));tp+=int(valid[r,c].sum())
    return {'correct':tp,'reference':len(ref),'predicted':len(pred),'precision':tp/max(1,len(pred)),'recall':tp/max(1,len(ref)),'f1':2*tp/max(1,len(ref)+len(pred))}

def main():
    frozen=json.loads((ROOT/'experiments/loop/geometry-g01/frozen_candidate.json').read_text());results=[]
    for pid in ['0253902-001','0401692-003','752234-003']:
        base=ROOT/'experiments/loop/end-to-end'/pid;run=json.loads((base/'run.json').read_text());image=cv2.imread(str(ROOT/run['image']),0)
        r=E.parse(str(base/'layout.xml'));native_lines=[]
        for line in r.findall('.//{*}TextLine'):
            pts=np.array([list(map(float,p.split(','))) for p in line.find('{*}Coords').get('points').split()]);native_lines.append({'poly':pts.tolist(),'box':[*pts.min(0),*pts.max(0)]})
        alto=E.parse(str(base/'native.alto.xml'));pred=[];refined=[];unmatched=0
        for line in alto.findall('.//{*}TextLine'):
            ws=[]
            for w in line.findall('{*}String'):
                x,y=float(w.get('HPOS')),float(w.get('VPOS'));ws.append({'text':w.get('CONTENT'),'box':[x,y,x+float(w.get('WIDTH')),y+float(w.get('HEIGHT'))]})
            if not ws:continue
            x,y=float(line.get('HPOS')),float(line.get('VPOS'));lb=[x,y,x+float(line.get('WIDTH')),y+float(line.get('HEIGHT'))]
            matrix=boxes_iou([lb],[n['box'] for n in native_lines])[0];idx=int(matrix.argmax());n=native_lines[idx]
            if matrix[idx]>=.3:
                boxes=refine_words(image,[w['box'] for w in ws],n['poly'],n['box'],**frozen['config'])
            else:boxes=[w['box'] for w in ws];unmatched+=1
            pred.extend(ws);refined.extend([{'text':w['text'],'box':b} for w,b in zip(ws,boxes)])
        # Reference is loaded only after both system predictions are complete.
        source=json.loads((ROOT/'experiments/loop/cache'/pid/'run.json').read_text());r=E.parse(str(ROOT/source['source_xml']));ref=[]
        for w in r.findall('.//{*}Word'):
            pts=np.array([list(map(float,p.split(','))) for p in w.find('{*}Coords').get('points').split()]);ref.append({'text':w.findtext('{*}TextEquiv/{*}Unicode',default=''),'box':[*pts.min(0),*pts.max(0)]})
        result={'page':pid,'oracle_inputs':False,'unmatched_alto_to_predicted_page_lines':unmatched,'frozen_config':frozen,'scores':{str(t):{'native':score(ref,pred,t),'refined':score(ref,refined,t)} for t in [.5,.75,.9]}}
        (base/'word-evaluation.json').write_text(json.dumps(result,indent=2));results.append(result);print(pid,result['scores'],flush=True)
    (ROOT/'experiments/loop/end-to-end/word-summary.json').write_text(json.dumps(results,indent=2))
if __name__=='__main__':main()
