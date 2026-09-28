"""Consumed diagnostic of pixel ownership; oracle unions are never candidates."""
import json, time, hashlib, xml.etree.ElementTree as ET
from pathlib import Path
import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment
from evaluate_crop_geometry_a65 import polygon
from evaluate_textline_instances_a75 import box_iou, summarize
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'experiments/loop/next-a76'; OUT=ROOT/'experiments/loop/next-a77'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 start=time.perf_counter(); sealed=json.loads((SRC/'candidates.json').read_text())
 expected={x['file']:x['sha256'] for x in json.loads((ROOT/'experiments/loop/chronicling-a58/audit.json').read_text())['files_detail']}
 official=json.loads((ROOT/'experiments/loop/chronicling-a58/official_split.json').read_text())
 assert not set(sealed['pages']) & set(official['Test'])
 inputs={str(p.relative_to(ROOT)):sha(p) for p in [SRC/'candidates.json',SRC/'predictions.json',OUT/'PROTOCOL.md']}
 pages={};details={}
 for name, data in sealed['pages'].items():
  mp=SRC/f'{name}-textline-mask.png'; assert sha(mp)==data['mask_sha256'];inputs[str(mp.relative_to(ROOT))]=sha(mp)
  mask=(cv2.imread(str(mp),0)>0).astype(np.uint8)
  _,labels,stats,_=cv2.connectedComponentsWithStats(mask,connectivity=8)
  instances=data['instances']; ids=np.array([x['component'] for x in instances]);areas=stats[ids,cv2.CC_STAT_AREA]
  h,w=mask.shape;sh,sw=data['source_shape'];sx,sy=w/sw,h/sh
  xp=ROOT/'corpora/chronicling-germany/annotations'/f'{name}.xml';assert sha(xp)==expected[xp.name];inputs[str(xp.relative_to(ROOT))]=sha(xp)
  tree=ET.fromstring(xp.read_bytes());ns={'p':tree.tag.split('}')[0][1:]}
  refs=[];refareas=[];hits=[];overlap=np.zeros_like(mask,dtype=np.uint16)
  for el in tree.findall('.//p:TextLine',ns):
   shape=polygon(el,ns)
   if shape is None:continue
   pts=np.round(np.asarray(shape.exterior.coords)*[sx,sy]).astype(np.int32)
   x,y,bw,bh=cv2.boundingRect(pts);x0=max(0,x);y0=max(0,y);x1=min(w,x+bw);y1=min(h,y+bh)
   local=np.zeros((max(0,y1-y0),max(0,x1-x0)),np.uint8)
   if local.size:cv2.fillPoly(local,[pts-[x0,y0]],1)
   counts=np.bincount(labels[y0:y1,x0:x1][local>0],minlength=len(stats)) if local.size else np.zeros(len(stats),int)
   hits.append(counts[ids]);refareas.append(int(local.sum()));overlap[y0:y1,x0:x1]+=local
   refs.append({'id':el.get('id'),'bbox':list(shape.bounds)})
  inter=np.asarray(hits).T;ca=inter/np.maximum(1,areas[:,None]);ra=inter/np.maximum(1,np.asarray(refareas)[None,:])
  edges=(ca>=.2)&(ra>=.01);sub=ra>=.05
  owner=inter.argmax(axis=1);contained=ca[np.arange(len(ids)),owner]>=.8
  groups=[];rows=[];cb=np.asarray([x['bbox_native'] for x in instances]);rb=np.asarray([x['bbox'] for x in refs])
  for j,ref in enumerate(refs):
   ci=np.flatnonzero((owner==j)&contained)
   if len(ci):
    b=cb[ci];groups.append([float(b[:,0].min()),float(b[:,1].min()),float(b[:,2].max()),float(b[:,3].max())])
   rows.append({**ref,'substantial_components':ids[np.flatnonzero(sub[:,j])].tolist(),'edge_components':ids[np.flatnonzero(edges[:,j])].tolist(),'contained_owner_components':ids[ci].tolist(),'covered_fraction':float(inter[:,j].sum()/max(1,refareas[j]))})
  iou=box_iou(cb,rb);rr,cc=linear_sum_assignment(-iou)
  ob=np.asarray(groups).reshape(-1,4);oi=box_iou(ob,rb);orr,occ=linear_sum_assignment(-oi)
  pages[name]={'candidates':len(ids),'references':len(refs),'old_bbox_iou10_multiple_refs':int(((iou>.1).sum(1)>1).sum()),'pixel_substantial_multiple_refs':int((edges.sum(1)>1).sum()),'pixel_no_substantial_ref':int((edges.sum(1)==0).sum()),'contained80_candidates':int(contained.sum()),'refs_multiple_components_ge5pct':int((sub.sum(0)>1).sum()),'refs_no_predicted_pixels':int((inter.sum(0)==0).sum()),'predicted_pixels_in_multiple_refs_fraction':float(((overlap>1)&(mask>0)).sum()/max(1,mask.sum())),'baseline':summarize(iou,rr,cc,len(cb),len(rb)),'oracle_grouped':summarize(oi,orr,occ,len(ob),len(rb))}
  details[name]=rows
  if '1924' in name:
   assets=json.loads((SRC/'assets.json').read_text());a=next(a for a in assets['images'] if a['page']==name);ip=ROOT/a['path'];assert sha(ip)==a['sha256'];inputs[str(ip.relative_to(ROOT))]=sha(ip)
   image=cv2.imread(str(ip)); examples=sorted(rows,key=lambda r:(-len(r['substantial_components']),r['id']))[:6]
   for k,row in enumerate(examples):
    x0,y0,x1,y1=map(int,row['bbox']);pad=35;x0=max(0,x0-pad);y0=max(0,y0-pad);x1=min(sw,x1+pad);y1=min(sh,y1+pad)
    raw=image[y0:y1,x0:x1].copy(); overlay=raw.copy()
    for i in row['substantial_components']:
     b=next(v['bbox_native'] for v in instances if v['component']==i);p0=(int(b[0])-x0,int(b[1])-y0);p1=(int(b[2])-x0,int(b[3])-y0);cv2.rectangle(overlay,p0,p1,(0,0,255),2)
    cv2.imwrite(str(OUT/f'witness-{k}-raw.png'),raw);cv2.imwrite(str(OUT/f'witness-{k}-overlay.png'),overlay)
   (OUT/'witnesses.json').write_text(json.dumps(examples,indent=2)+'\n')
 assert all(sha(ROOT/p)==v for p,v in inputs.items())
 (OUT/'details.json').write_text(json.dumps(details,indent=2)+'\n')
 report={'schema':'bbvlm.a77.diagnostic/1','status':'consumed_oracle_attribution','pages':pages,'input_sha256':inputs,'seconds':time.perf_counter()-start,'new_model_forwards':0,'ocr_calls':0,'vlm_calls':0,'test_pages_opened':0,'all_scientific_gates_passed':False}
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(pages,indent=2))
if __name__=='__main__':main()
