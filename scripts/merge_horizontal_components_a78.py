"""Single frozen image-only horizontal linker; A76 consumed data only."""
import json,time,hashlib
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
from evaluate_textline_instances_a75 import box_iou,parse_reference,summarize
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'experiments/loop/next-a76';OUT=ROOT/'experiments/loop/next-a78'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def merge(items):
 b=np.asarray([v['bbox_native'] for v in items],float);n=len(b);h=b[:,3]-b[:,1];cy=(b[:,1]+b[:,3])/2
 right={};left={}
 for i in range(n):
  for j in range(n):
   if i==j:continue
   gap=b[j,0]-b[i,2];small=min(h[i],h[j]);over=min(b[i,3],b[j,3])-max(b[i,1],b[j,1])
   if not (0<=gap<=1.5*small and over>=.7*small and max(h[i],h[j])<=1.5*small and abs(cy[i]-cy[j])<=.25*small):continue
   key=(float(gap),items[j]['component']);keyleft=(float(gap),items[i]['component'])
   if i not in right or key<right[i][0]:right[i]=(key,j)
   if j not in left or keyleft<left[j][0]:left[j]=(keyleft,i)
 parent=list(range(n))
 def root(i):
  while parent[i]!=i:i=parent[i]
  return i
 links=[]
 for i,(_,j) in right.items():
  if left[j][1]==i:parent[root(j)]=root(i);links.append([items[i]['component'],items[j]['component']])
 groups={}
 for i in range(n):groups.setdefault(root(i),[]).append(i)
 result=[]
 for inds in groups.values():
  a=b[inds];result.append({'components':[items[i]['component'] for i in inds],'bbox_native':[float(a[:,0].min()),float(a[:,1].min()),float(a[:,2].max()),float(a[:,3].max())]})
 assert sorted(i for r in result for i in r['components'])==sorted(x['component'] for x in items)
 return result,links

def main():
 start=time.perf_counter();source=json.loads((SRC/'candidates.json').read_text());out={'schema':'bbvlm.a78.horizontal-links/1','source_sha256':sha(SRC/'candidates.json'),'protocol_sha256':sha(OUT/'PROTOCOL.md'),'pages':{}}
 for n,p in source['pages'].items():
  groups,links=merge(p['instances']);out['pages'][n]={'instances':groups,'links':links}
 (OUT/'candidates.json').write_text(json.dumps(out,indent=2)+'\n');seal=sha(OUT/'candidates.json')
 expected={r['file']:r['sha256'] for r in json.loads((ROOT/'experiments/loop/chronicling-a58/audit.json').read_text())['files_detail']}
 pages={};tests={};gains=0
 for n,p in out['pages'].items():
  refs,_=parse_reference(n,expected);rb=np.array([x['bbox'] for x in refs]);new=np.array([x['bbox_native'] for x in p['instances']]);old=np.array([x['bbox_native'] for x in source['pages'][n]['instances']]);scores=[];matches=[]
  for boxes in [old,new]:
   iou=box_iou(boxes,rb);rr,cc=linear_sum_assignment(-iou);scores.append(summarize(iou,rr,cc,len(boxes),len(rb)));matches.append(set(cc[iou[rr,cc]>=.5].tolist()))
  before,after=scores;gained=sorted(matches[1]-matches[0]);lost=sorted(matches[0]-matches[1]);gains+=len(gained)-len(lost)
  pages[n]={'before':before,'after':after,'merged_groups':sum(len(i['components'])>1 for i in p['instances']),'links':len(p['links']),'gained_ref_ids':[refs[i]['line_id'] for i in gained],'lost_ref_ids':[refs[i]['line_id'] for i in lost]}
  tests[n]=after['iou50']['precision']>=before['iou50']['precision'] and after['iou50']['recall']>=before['iou50']['recall']
 assert sha(SRC/'candidates.json')==out['source_sha256'];assert sha(OUT/'candidates.json')==seal
 report={'schema':'bbvlm.a78.report/1','status':'consumed_single_configuration','candidate_sha256_before_xml':seal,'pages':pages,'per_page_noninferiority':tests,'net_true50_gain':gains,'local_gate_passed':all(tests.values()) and gains>0,'seconds':time.perf_counter()-start,'new_model_forwards':0,'test_pages_opened':0,'all_scientific_gates_passed':False}
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='pages'}))
if __name__=='__main__':main()
