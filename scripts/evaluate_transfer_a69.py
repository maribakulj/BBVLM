"""Run frozen detector+edge transfer, sealing image candidates before XML score."""
import hashlib, importlib.metadata, json, math, time, xml.etree.ElementTree as ET
from pathlib import Path
import cv2, torch
from doclayout_yolo import YOLOv10
from shapely.geometry import box
from shapely.ops import unary_union
from bbvlm.refine import extend_crop_edges_to_connected_ink
from evaluate_crop_geometry_a65 import polygon

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'experiments/loop/next-a69'
WEIGHTS=ROOT/'models/doclayout-yolo/doclayout_yolo_docstructbench_imgsz1024.pt'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fixed(b,p,w,h):return [max(0,b[0]-p),max(0,b[1]-p),min(w,b[2]+p),min(h,b[3]+p)]
def parse_xml(name,expected):
 p=ROOT/'corpora/chronicling-germany/annotations'/f'{name}.xml';assert sha(p)==expected[p.name]
 root=ET.fromstring(p.read_bytes());ns={'p':root.tag.split('}')[0][1:]};pe=root.find('p:Page',ns)
 regions=[];lines=[]
 for re in pe.findall('p:TextRegion',ns):
  rp=polygon(re,ns)
  if rp is not None:regions.append(rp)
  for le in re.findall('p:TextLine',ns):
   lp=polygon(le,ns)
   if lp is not None:lines.append((le.get('id'),lp))
 return regions,lines,sha(p)
def metrics(rows,regions,lines):
 out={}
 native_shapes=[box(*r['bbox']) for r in rows['native']]
 for policy in ('native','fixed','ink_crossing'):
  shapes=[box(*r['bbox']) for r in rows[policy]]
  vals=[max((line.intersection(c).area/line.area for c in shapes),default=0.) for _,line in lines]
  rec={'lines':len(vals),'mean_best_coverage':sum(vals)/len(vals),'lt50':sum(v<.5 for v in vals),
       'lt95':sum(v<.95 for v in vals),'added_area':0.,'foreign_added_area':0.,
       'foreign_added_boxes_gt1pct':0}
  if policy!='native':
   for native,candidate in zip(native_shapes,shapes):
    added=candidate.difference(native);rec['added_area']+=added.area
    ints=[native.intersection(r).area for r in regions]
    if ints:
     dominant=max(range(len(regions)),key=lambda i:ints[i])
     other=unary_union([r for i,r in enumerate(regions) if i!=dominant])
     foreign=added.intersection(other).area;rec['foreign_added_area']+=foreign
     if added.area and foreign/added.area>.01:rec['foreign_added_boxes_gt1pct']+=1
   rec['foreign_fraction_of_added']=rec['foreign_added_area']/rec['added_area'] if rec['added_area'] else 0.
  out[policy]=rec
 return out
def add(records):
 keys=('lines','lt50','lt95','added_area','foreign_added_area','foreign_added_boxes_gt1pct')
 out={k:sum(r[k] for r in records) for k in keys}
 out['mean_best_coverage']=sum(r['mean_best_coverage']*r['lines'] for r in records)/out['lines']
 out['foreign_fraction_of_added']=out['foreign_added_area']/out['added_area'] if out['added_area'] else 0.
 return out
def main():
 started=time.perf_counter();split=json.loads((OUT/'split.json').read_text());names=split['pages']
 assets=json.loads((OUT/'assets.json').read_text());asset={r['page']:r for r in assets['images']}
 assert hashlib.sha256(WEIGHTS.read_bytes()).hexdigest()=='9a2ee0220fe3d9ad31b47e1d9f1282f46959a54e4618fce9cffcc9715b8286e2'
 torch.set_num_threads(4);torch.set_num_interop_threads(1);model=YOLOv10(str(WEIGHTS))
 predictions=[]
 for name in names:
  path=ROOT/asset[name]['path'];assert sha(path)==asset[name]['sha256']
  t=time.perf_counter();result=model.predict(str(path),imgsz=1024,conf=.2,max_det=300,device='cpu',verbose=False,save=False)[0]
  predictions.append({'page':name,'shape':list(result.orig_shape),'seconds':time.perf_counter()-t,
   'boxes':[{'bbox':list(map(float,b)),'confidence':float(s),'class_id':int(c),'class_name':result.names[int(c)]}
            for b,s,c in zip(result.boxes.xyxy.tolist(),result.boxes.conf.tolist(),result.boxes.cls.tolist())]})
 (OUT/'predictions.json').write_text(json.dumps(predictions,indent=2)+'\n')
 candidates={}
 for pred in predictions:
  name=pred['page'];path=ROOT/asset[name]['path'];gray=cv2.imread(str(path),cv2.IMREAD_GRAYSCALE);h,w=gray.shape
  assert pred['shape']==[h,w];pad=max(4,round(.003*min(h,w)))
  rows=[r for r in pred['boxes'] if r['class_id'] not in (3,5)];out={'native':[],'fixed':[],'ink_crossing':[]}
  for r in rows:
   b=r['bbox'];nb=[max(0,math.floor(b[0])),max(0,math.floor(b[1])),min(w,math.ceil(b[2])),min(h,math.ceil(b[3]))]
   cb,audit=extend_crop_edges_to_connected_ink(gray,nb,max_pad=pad,min_area=3,min_side_pixels=2)
   common={'class_id':r['class_id'],'class_name':r['class_name'],'confidence':r['confidence']}
   out['native'].append({'bbox':nb,**common});out['fixed'].append({'bbox':fixed(nb,pad,w,h),**common})
   out['ink_crossing'].append({'bbox':cb,'edge_audit':audit,**common})
  out['shape']=[h,w];out['max_pad']=pad;candidates[name]=out
 payload={'schema':'bbvlm.a69.candidates/1','rule':'A68 unchanged','pages':candidates,
          'source_sha256':{n:asset[n]['sha256'] for n in names}}
 cp=OUT/'candidates.json';cp.write_text(json.dumps(payload,indent=2)+'\n');candidate_hash=sha(cp)
 # Only now may the transfer XML geometry be opened.
 expected={r['file']:r['sha256'] for r in json.loads((ROOT/'experiments/loop/chronicling-a58/audit.json').read_text())['files_detail']}
 per_page={};xml_hashes={}
 for name in names:
  regions,lines,xh=parse_xml(name,expected);xml_hashes[name]=xh;per_page[name]=metrics(candidates[name],regions,lines)
 aggregate={p:add([per_page[n][p] for n in names]) for p in ('native','fixed','ink_crossing')}
 n,f,i=aggregate['native'],aggregate['fixed'],aggregate['ink_crossing']
 checks={'lt50_noninferior':i['lt50']<=n['lt50'],
  'lt95_relative_reduction_ge20pct':i['lt95']<=.8*n['lt95'],
  'added_area_le60pct_fixed':i['added_area']<=.6*f['added_area'],
  'foreign_boxes_le_fixed':i['foreign_added_boxes_gt1pct']<=f['foreign_added_boxes_gt1pct'],
  'foreign_fraction_le_fixed_plus2pp':i['foreign_fraction_of_added']<=f['foreign_fraction_of_added']+.02,
  'no_page_mean_regression':all(per_page[x]['ink_crossing']['mean_best_coverage']+1e-12>=per_page[x]['native']['mean_best_coverage'] for x in names)}
 report={'status':'frozen_transfer_not_global_validation','candidate_sha256_before_xml':candidate_hash,
  'pages':names,'aggregate':aggregate,'per_page':per_page,'gate_checks':checks,'local_gate_passed':all(checks.values()),
  'xml_sha256':xml_hashes,'model_forwards':len(names),'test_pages_opened':0,'vlm_calls':0,'ocr_calls':0,
  'seconds':time.perf_counter()-started,'versions':{k:importlib.metadata.version(k) for k in ('torch','doclayout_yolo','opencv-python','shapely')},
  'all_scientific_gates_passed':False,
  'limitations':['Official Training pages used as BBVLM transfer because Validation geometry was consumed by A65.',
                 'A58 structurally audited all XML; this is not a pristine corpus claim.',
                 'Annotation coverage and foreign overlap are not perfect ALTO or semantic ownership truth.']}
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'aggregate':aggregate,'gate_checks':checks,'local_gate_passed':all(checks.values())},indent=2))
if __name__=='__main__':main()
