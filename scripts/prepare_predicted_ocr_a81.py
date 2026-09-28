"""Prepare consumed stratified blind predicted-box OCR audit; no reference text exposed."""
import json,hashlib,math
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
from PIL import Image
from evaluate_textline_instances_a75 import box_iou,parse_reference
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'experiments/loop/next-a81';S=ROOT/'experiments/loop/next-a80'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def key(x):return hashlib.sha256(('A81:'+str(x['components'])).encode()).hexdigest()
def main():
 src=json.loads((S/'routed/candidates.json').read_text());assets={x['page']:x for x in json.loads((S/'dense/assets.json').read_text())['images']};expected={x['file']:x['sha256'] for x in json.loads((ROOT/'experiments/loop/chronicling-a58/audit.json').read_text())['files_detail']}
 selected=[]
 for name,page in src['pages'].items():
  refs,xmlsha=parse_reference(name,expected);items=page['instances'];iou=box_iou(np.array([x['bbox_native'] for x in items]),np.array([x['bbox'] for x in refs]));rr,cc=linear_sum_assignment(-iou);matches={int(i):(int(j),float(iou[i,j])) for i,j in zip(rr,cc)}
  if '1785' in name:
   chosen=[(i,'merged') for i,x in enumerate(items) if len(x['components'])>1]
   unmatched=[i for i,x in enumerate(items) if len(x['components'])==1 and matches.get(i,(0,0))[1]<.5]
   unmatched.sort(key=lambda i: -((items[i]['bbox_native'][2]-items[i]['bbox_native'][0])*(items[i]['bbox_native'][3]-items[i]['bbox_native'][1])))
   chosen += [(i,'unmatched_singleton') for i in unmatched[:2]]
  else:
   good=[i for i in range(len(items)) if matches.get(i,(0,0))[1]>=.7];chosen=[(min(good,key=lambda i:key(items[i])),'matched_control')]
  for i,group in chosen:
   j,overlap=matches.get(i,(None,0));selected.append({'page':name,'group':group,'candidate_index':i,'components':items[i]['components'],'bbox_native':items[i]['bbox_native'],'line_id':refs[j]['line_id'] if j is not None and overlap>=.5 else None,'iou':overlap,'xml_sha256':xmlsha})
 assert len(selected)==8
 request={'instruction':'Read raw target only; use context only to understand visible clipped glyphs; never add neighboring lines. Preserve historical spelling. Return text, visual_role, clipped_edges, uncertain_spans, note per opaque ID; mark unreadable with [illegible].','items':[]};mapping=[]
 for x in selected:
  identifier='V'+hashlib.sha256(('A81:'+x['page']+str(x['components'])).encode()).hexdigest()[:8];asset=assets[x['page']];path=ROOT/asset['path'];assert sha(path)==asset['sha256'];im=Image.open(path);w,h=im.size
  a,b,c,d=x['bbox_native'];box=(max(0,math.floor(a)),max(0,math.floor(b)),min(w,math.ceil(c)),min(h,math.ceil(d)));height=box[3]-box[1];ctx=(max(0,box[0]-40),max(0,box[1]-height),min(w,box[2]+40),min(h,box[3]+height))
  paths=[];dims=[]
  for label,bounds in [('target',box),('context',ctx)]:
   image=im.crop(bounds);scale=min(2,1800/image.width);image=image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.LANCZOS);p=P/'blind'/f'{identifier}-{label}.png';image.save(p);paths.append(str(p.relative_to(ROOT)));dims.append(list(image.size))
  request['items'].append({'id':identifier,'images':paths,'sha256':[sha(ROOT/z) for z in paths],'dimensions':dims})
  mapping.append(dict(x,id=identifier,image_sha256=asset['sha256'],image_path=asset['path'],crop_box=box,context_box=ctx))
 request['items'].sort(key=lambda x:x['id']);(P/'blind/request.json').write_text(json.dumps(request,indent=2)+'\n');(P/'private-map.json').write_text(json.dumps({'selection':'consumed_oracle_stratified','protocol_sha256':sha(P/'PROTOCOL.md'),'source_candidates_sha256':sha(S/'routed/candidates.json'),'mapping':mapping},indent=2)+'\n');print('prepared8 targets,16 views')
if __name__=='__main__':main()
