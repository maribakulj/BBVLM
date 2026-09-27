#!/usr/bin/env python3
"""Open sealed A29 members and render opaque-ID visual inputs."""
from __future__ import annotations
import hashlib,json,random,time,zipfile
from pathlib import Path
import cv2,numpy as np
from lxml import etree as E

ROOT=Path(__file__).resolve().parents[1];EXP=ROOT/'experiments/loop/bnf-impact-olr-a29';A26=ROOT/'experiments/loop/bnf-impact-a26'
ARCHIVE=A26/'source/impact.zip';OPEN=EXP/'opened';VIS=EXP/'visual-input'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def sha_bytes(data):return hashlib.sha256(data).hexdigest()
def points(node):
    raw=node.get('points')
    if raw:return np.asarray([[float(a),float(b)] for a,b in (v.split(',') for v in raw.split())])
    return np.asarray([[float(x.get('x')),float(x.get('y'))] for x in node.xpath('./*[local-name()="Point"]')])

def main():
    split=json.loads((EXP/'split.json').read_text())
    if split['status']!='frozen_unopened':raise ValueError('split is not frozen_unopened')
    checks={'protocol':EXP/'PROTOCOL.md','prompt':EXP/'VLM_PROMPT.md','preparer':ROOT/'scripts/prepare_bnf_olr_a29.py',
      'evaluator':ROOT/'scripts/evaluate_bnf_olr_a29.py','merger':ROOT/'src/bbvlm/olr_continuation.py',
      'development':EXP/'development-report.json','archive_manifest':A26/'source/archive-manifest.json'}
    for key,path in checks.items():
        if sha(path)!=split['sealed_sha256'][key]:raise ValueError(f'sealed file changed: {key}')
    if sha(ARCHIVE)!=split['archive_sha256']:raise ValueError('archive hash mismatch')
    files=[]
    with zipfile.ZipFile(ARCHIVE) as z:
        for name in (split['page']['xml'],split['page']['image']):
            data=z.read(name);info=z.getinfo(name);dst=OPEN/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
            files.append({'name':name,'bytes':len(data),'crc32':f'{info.CRC:08x}','sha256':sha_bytes(data)})
    tree=E.parse(str(OPEN/split['page']['xml']),E.XMLParser(resolve_entities=False,no_network=True));regs=[]
    for node in tree.xpath('//*[local-name()="TextRegion"]'):
        coords=node.xpath('./*[local-name()="Coords"]')
        if not coords:continue
        poly=points(coords[0])
        if len(poly)>=3:regs.append({'source_id':node.get('id'),'polygon':poly})
    if not regs:raise ValueError('fail closed: zero TextRegion polygons')
    tokens=[f'R{i:03d}' for i in range(1,len(regs)+1)];random.Random(split['opaque_token_seed']).shuffle(tokens);mapping={token:r['source_id'] for token,r in zip(tokens,regs)}
    image=cv2.imread(str(OPEN/split['page']['image']),cv2.IMREAD_COLOR)
    if image is None:raise ValueError('image decode failed')
    height,width=image.shape[:2];VIS.mkdir(parents=True,exist_ok=True);preview=image.copy()
    for token,reg in zip(tokens,regs):
        poly=np.rint(reg['polygon']).astype(np.int32);cv2.polylines(preview,[poly],True,(0,80,255),2,cv2.LINE_AA);x,y=poly[:,0].min(),poly[:,1].min();cv2.rectangle(preview,(x,max(0,y-23)),(x+58,y+2),(255,255,255),-1);cv2.putText(preview,token,(x,max(18,y-4)),cv2.FONT_HERSHEY_SIMPLEX,.52,(0,0,0),1,cv2.LINE_AA)
    scale=1800/width;cv2.imwrite(str(VIS/'page-labelled.jpg'),cv2.resize(preview,(1800,round(height*scale)),interpolation=cv2.INTER_AREA),[cv2.IMWRITE_JPEG_QUALITY,94]);cv2.imwrite(str(VIS/'page-raw.jpg'),cv2.resize(image,(1800,round(height*scale)),interpolation=cv2.INTER_AREA),[cv2.IMWRITE_JPEG_QUALITY,94])
    panels=[]
    for i in range(6):
        x0=max(0,round(i*width/6)-35);x1=min(width,round((i+1)*width/6)+35);crop=preview[:,x0:x1];crop=cv2.resize(crop,(1200,round(height*1200/(x1-x0))),interpolation=cv2.INTER_CUBIC);path=VIS/f'column-{i+1}.jpg';cv2.imwrite(str(path),crop,[cv2.IMWRITE_JPEG_QUALITY,95]);panels.append(str(path.relative_to(ROOT)))
    (EXP/'sealed-map.json').write_text(json.dumps({'schema':'bbvlm.a29-private-map/1','token_to_source_id':mapping},indent=2)+'\n')
    task={'schema':'bbvlm.bnf-impact-olr-a29-task/1','page':split['page']['page'],'raw_page':str((VIS/'page-raw.jpg').relative_to(ROOT)),'labelled_page':str((VIS/'page-labelled.jpg').relative_to(ROOT)),'column_panels_left_to_right':panels,'tokens':sorted(tokens),'expected_token_count':len(tokens),'output_path':str((EXP/'candidate/luna.json').relative_to(ROOT))}
    (EXP/'public-task.json').write_text(json.dumps(task,indent=2)+'\n');(EXP/'opened.json').write_text(json.dumps({'schema':'bbvlm.bnf-impact-olr-a29-opened/1','opened_unix':time.time(),'split_sha256':sha(EXP/'split.json'),'files':files,'text_regions':len(regs),'visual_sha256':{p.name:sha(p) for p in sorted(VIS.glob('*.jpg'))}},indent=2)+'\n');print(json.dumps(task,indent=2))
if __name__=='__main__':main()
