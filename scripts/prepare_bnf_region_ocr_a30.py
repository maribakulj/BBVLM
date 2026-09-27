#!/usr/bin/env python3
"""Open A30 after sealing and render sixteen opaque polygon crops."""
from __future__ import annotations
import hashlib,json,random,time,zipfile,unicodedata
from pathlib import Path
import cv2,numpy as np
from lxml import etree as E
ROOT=Path(__file__).resolve().parents[1];EXP=ROOT/'experiments/loop/bnf-region-ocr-a30';A26=ROOT/'experiments/loop/bnf-impact-a26';ARCH=A26/'source/impact.zip';OPEN=EXP/'opened';VIS=EXP/'visual-input'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def shab(b):return hashlib.sha256(b).hexdigest()
def points(node):
 raw=node.get('points')
 if raw:return np.asarray([[float(a),float(b)] for a,b in (v.split(',') for v in raw.split())])
 return np.asarray([[float(p.get('x')),float(p.get('y'))] for p in node.xpath('./*[local-name()="Point"]')])
def region_text(node):
 values=node.xpath('./*[local-name()="TextEquiv"]/*[local-name()="Unicode"]/text()')
 return unicodedata.normalize('NFC',values[0].replace('\r\n','\n').replace('\r','\n').strip()) if values else ''
def main():
 s=json.loads((EXP/'split.json').read_text());checks={'protocol':EXP/'PROTOCOL.md','prompt':EXP/'VLM_PROMPT.md','preparer':ROOT/'scripts/prepare_bnf_region_ocr_a30.py','evaluator':ROOT/'scripts/evaluate_bnf_region_ocr_a30.py','metrics':ROOT/'src/bbvlm/metrics.py','archive_manifest':A26/'source/archive-manifest.json'}
 for k,p in checks.items():
  if sha(p)!=s['sealed_sha256'][k]:raise ValueError(f'sealed file changed: {k}')
 if sha(ARCH)!=s['archive_sha256']:raise ValueError('archive hash mismatch')
 files=[]
 with zipfile.ZipFile(ARCH) as z:
  for name in (s['page']['xml'],s['page']['image']):
   data=z.read(name);info=z.getinfo(name);dst=OPEN/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data);files.append({'name':name,'bytes':len(data),'crc32':f'{info.CRC:08x}','sha256':shab(data)})
 tree=E.parse(str(OPEN/s['page']['xml']),E.XMLParser(resolve_entities=False,no_network=True));eligible=[]
 for n in tree.xpath('//*[local-name()="TextRegion"]'):
  coords=n.xpath('./*[local-name()="Coords"]');text=region_text(n)
  if not coords or n.get('type') not in {'paragraph','heading'} or not 40<=len(text)<=400:continue
  poly=points(coords[0]);x0,y0=poly.min(axis=0);x1,y1=poly.max(axis=0)
  if x1-x0>=180 and y1-y0>=35:eligible.append({'source_id':n.get('id'),'text':text,'poly':poly})
 if len(eligible)<16:raise ValueError(f'fail closed: only {len(eligible)} eligible regions')
 eligible=sorted(eligible,key=lambda r:hashlib.sha256((s['selection_seed']+r['source_id']).encode()).hexdigest())[:16];tokens=[f'T{i:03d}' for i in range(1,17)];random.Random(s['opaque_seed']).shuffle(tokens);image=cv2.imread(str(OPEN/s['page']['image']),cv2.IMREAD_COLOR)
 if image is None:raise ValueError('image decode failed')
 VIS.mkdir(parents=True,exist_ok=True);mapping={};items=[];h,w=image.shape[:2]
 for token,r in zip(tokens,eligible):
  poly=np.rint(r['poly']).astype(np.int32);x0=max(0,int(poly[:,0].min())-12);y0=max(0,int(poly[:,1].min())-12);x1=min(w,int(poly[:,0].max())+13);y1=min(h,int(poly[:,1].max())+13);crop=image[y0:y1,x0:x1].copy();local=poly-[x0,y0];mask=np.zeros(crop.shape[:2],np.uint8);cv2.fillPoly(mask,[local],255);crop[mask==0]=255;cv2.polylines(crop,[local],True,(0,0,220),2,cv2.LINE_AA)
  if crop.shape[1]<1200:
   scale=1200/crop.shape[1];crop=cv2.resize(crop,(1200,round(crop.shape[0]*scale)),interpolation=cv2.INTER_CUBIC)
  path=VIS/f'{token}.png';cv2.imwrite(str(path),crop,[cv2.IMWRITE_PNG_COMPRESSION,3]);mapping[token]={'source_id':r['source_id'],'reference':r['text'],'crop_bbox':[x0,y0,x1,y1]};items.append({'id':token,'image':str(path.relative_to(ROOT)),'sha256':sha(path)})
 items.sort(key=lambda x:x['id']);(EXP/'private-reference.json').write_text(json.dumps({'schema':'bbvlm.bnf-region-ocr-a30-private/1','items':mapping},ensure_ascii=False,indent=2)+'\n');task={'schema':'bbvlm.bnf-region-ocr-a30-task/1','page':s['page']['page'],'items':items,'expected_ids':[x['id'] for x in items],'output_path':str((EXP/'candidate/luna.json').relative_to(ROOT))};(EXP/'public-task.json').write_text(json.dumps(task,indent=2)+'\n');(EXP/'opened.json').write_text(json.dumps({'schema':'bbvlm.bnf-region-ocr-a30-opened/1','opened_unix':time.time(),'split_sha256':sha(EXP/'split.json'),'files':files,'eligible_regions':len(eligible),'selected_regions':16},indent=2)+'\n');print(json.dumps(task,indent=2))
if __name__=='__main__':main()
