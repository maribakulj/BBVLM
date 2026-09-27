"""Paired diagnostics for the frozen candidate. No additional selection/tuning."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import cv2,numpy as np
from bbvlm.refine import refine_words
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'experiments/loop/geometry-g01';conf=json.loads((p/'frozen_candidate.json').read_text())['config'];result=[]
def iou(a,b):
    inter=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]));u=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter;return inter/u if u else 0
for pid in ['0401692-003','752234-003']:
    d=json.loads((p/(pid+'.native.json')).read_text());im=cv2.imread(str(ROOT/d['image']),0);perline=[];details=[]
    for row in d['rows']:
        if row['error']:perline.append((0,len(row['reference'])));continue
        native=[w['box'] for w in row['native']];refined=refine_words(im,native,row['polygon'],row['line_box'],**conf)
        deltas=[]
        for gt,a,b in zip(row['reference'],native,refined):
            delta=iou(gt['box'],b)-iou(gt['box'],a);deltas.append(delta);details.append({'line':row['id'],'text':gt['text'],'delta':delta,'reference':gt['box'],'native':a,'refined':b})
        perline.append((sum(deltas),len(deltas)))
    arr=np.array(perline);rng=np.random.default_rng(73201);sample=rng.integers(0,len(arr),(2000,len(arr)));boot=arr[sample,0].sum(1)/arr[sample,1].sum(1)
    delta=[v['delta'] for v in details];r={'page':pid,'improved_words':sum(x>1e-9 for x in delta),'worsened_words':sum(x<-1e-9 for x in delta),'unchanged_words':sum(abs(x)<=1e-9 for x in delta),'mean_delta_ci95_line_bootstrap':np.percentile(boot,[2.5,97.5]).tolist(),'ci_warning':'line bootstrap within this page, NOT independent publication/page generalization','largest_regressions':sorted(details,key=lambda v:v['delta'])[:20]};result.append(r)
(p/'diagnostics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps([{k:v for k,v in r.items() if k!='largest_regressions'} for r in result],indent=2))
