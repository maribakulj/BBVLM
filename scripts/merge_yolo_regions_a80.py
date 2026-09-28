"""Image-only region ownership followed by unchanged A78 linker."""
import json,time,hashlib
from pathlib import Path
import numpy as np
import torch
from doclayout_yolo import YOLOv10
from scipy.optimize import linear_sum_assignment
from merge_horizontal_components_a78 import merge
from evaluate_textline_instances_a75 import box_iou,parse_reference,summarize
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'experiments/loop/next-a80/dense';OUT=ROOT/'experiments/loop/next-a80/routed'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 start=time.perf_counter();weights=ROOT/'models/doclayout-yolo/doclayout_yolo_docstructbench_imgsz1024.pt';assert sha(weights)=='9a2ee0220fe3d9ad31b47e1d9f1282f46959a54e4618fce9cffcc9715b8286e2'
 source=json.loads((SRC/'candidates.json').read_text());assets=json.loads((SRC/'assets.json').read_text());torch.set_num_threads(4);torch.set_num_interop_threads(1)
 pp=OUT/'predictions.json';new_forwards=0
 if pp.exists():
  pred=json.loads(pp.read_text());assert pred['protocol_sha256']==sha(OUT/'PROTOCOL.md')
 else:
  model=YOLOv10(str(weights));pred={'protocol_sha256':sha(OUT/'PROTOCOL.md'),'weight_sha256':sha(weights),'pages':{}}
  for row in assets['images']:
   path=ROOT/row['path'];assert sha(path)==row['sha256'];tick=time.perf_counter();r=model.predict(str(path),imgsz=1024,conf=.2,max_det=300,device='cpu',verbose=False,save=False)[0];new_forwards+=1
   pred['pages'][row['page']]={'seconds':time.perf_counter()-tick,'image_sha256':sha(path),'boxes':[{'bbox':list(map(float,b)),'class_id':int(c),'class_name':r.names[int(c)],'confidence':float(s)} for b,c,s in zip(r.boxes.xyxy.tolist(),r.boxes.cls.tolist(),r.boxes.conf.tolist())]}
  pp.write_text(json.dumps(pred,indent=2)+'\n')
 out={'source_sha256':sha(SRC/'candidates.json'),'predictions_sha256':sha(pp),'pages':{}}
 for name,page in source['pages'].items():
  regions=[r['bbox'] for r in pred['pages'][name]['boxes'] if r['class_id'] not in [3,5]];groups={};unknown=[];ambiguous=0
  for item in page['instances']:
   x0,y0,x1,y1=item['bbox_native'];area=(x1-x0)*(y1-y0);owners=[]
   for k,(a,b,c,d) in enumerate(regions):
    inter=max(0,min(x1,c)-max(x0,a))*max(0,min(y1,d)-max(y0,b))
    if inter/area>=.9:owners.append(k)
   if len(owners)==1:groups.setdefault(owners[0],[]).append(item)
   else:unknown.append({'components':[item['component']],'bbox_native':item['bbox_native'],'owner':None});ambiguous+=len(owners)>1
  result=list(unknown);links=[]
  for owner,items in groups.items():
   joined,ls=merge(items);links+=ls
   result += [dict(x,owner=owner) for x in joined]
  assert sorted(c for g in result for c in g['components'])==sorted(i['component'] for i in page['instances'])
  out['pages'][name]={'instances':result,'links':links,'unknown_or_ambiguous':len(unknown),'ambiguous':ambiguous,'region_count':len(regions)}
 cp=OUT/'candidates.json';cp.write_text(json.dumps(out,indent=2)+'\n');seal=sha(cp)
 expected={r['file']:r['sha256'] for r in json.loads((ROOT/'experiments/loop/chronicling-a58/audit.json').read_text())['files_detail']};pages={};checks={};gain=0
 for name,page in out['pages'].items():
  refs,_=parse_reference(name,expected);rb=np.array([r['bbox'] for r in refs]);scores=[];match=[]
  for items in [source['pages'][name]['instances'],page['instances']]:
   b=np.array([x['bbox_native'] for x in items]);i=box_iou(b,rb);rr,cc=linear_sum_assignment(-i);scores.append(summarize(i,rr,cc,len(b),len(rb)));match.append(set(cc[i[rr,cc]>=.5].tolist()))
  old,new=scores;wins=match[1]-match[0];loss=match[0]-match[1];gain+=len(wins)-len(loss);checks[name]=new['iou50']['precision']>=old['iou50']['precision'] and new['iou50']['recall']>=old['iou50']['recall']
  pages[name]={'before':old,'after':new,'links':len(page['links']),'regions':page['region_count'],'unknown_or_ambiguous':page['unknown_or_ambiguous'],'ambiguous':page['ambiguous'],'gained_ref_ids':[refs[i]['line_id'] for i in sorted(wins)],'lost_ref_ids':[refs[i]['line_id'] for i in sorted(loss)]}
 assert sha(cp)==seal and sha(SRC/'candidates.json')==out['source_sha256']
 report={'status':'consumed_region_constrained_merger','pages':pages,'checks':checks,'net_true50_gain':gain,'local_gate_passed':all(checks.values()) and gain>0,'new_model_forwards':new_forwards,'total_model_forwards':4,'inference_seconds':sum(x['seconds'] for x in pred['pages'].values()),'seconds':time.perf_counter()-start,'candidate_sha256_before_xml':seal,'ocr_calls':0,'vlm_calls':0,'test_pages_opened':0,'all_scientific_gates_passed':False}
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='pages'}))
if __name__=='__main__':main()
