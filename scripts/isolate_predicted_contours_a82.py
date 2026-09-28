"""Frozen contour-only crop isolation then consumed annotation-based pixel audit."""
import json,time,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
import cv2,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'experiments/loop/next-a82';S=ROOT/'experiments/loop/next-a80'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 start=time.perf_counter();mapping=json.loads((ROOT/'experiments/loop/next-a81/private-map.json').read_text())['mapping'];mapping=[x for x in mapping if x['line_id'] is not None];pred=json.loads((S/'dense/candidates.json').read_text());views=[];arrays={};manifest=[]
 for m in mapping:
  path=ROOT/m['image_path'];assert sha(path)==m['image_sha256'];image=cv2.imread(str(path));a,b,c,d=m['crop_box'];raw=image[b:d,a:c];mask=np.zeros(raw.shape[:2],np.uint8);components={x['component']:x for x in pred['pages'][m['page']]['instances']}
  for i in m['components']:
   pts=np.array(components[i]['contour_native'])-np.array([a,b]);cv2.fillPoly(mask,[np.rint(pts).astype(np.int32)],1)
  mask=cv2.dilate(mask,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)));new=raw.copy();new[mask==0]=255;identifier='P'+hashlib.sha256(('A82:'+m['id']).encode()).hexdigest()[:8];file=P/'blind'/f'{identifier}.png';im=Image.fromarray(cv2.cvtColor(new,cv2.COLOR_BGR2RGB));scale=min(2,1800/im.width);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);im.save(file);mp=P/f'{identifier}-mask.png';cv2.imwrite(str(mp),mask*255)
  views.append({'id':identifier,'images':[str(file.relative_to(ROOT))],'sha256':[sha(file)]});manifest.append({'id':identifier,'a81_id':m['id'],'image_sha256':sha(file),'mask_sha256':sha(mp),'components':m['components']});arrays[m['id']]=(raw,mask)
 (P/'candidates.json').write_text(json.dumps({'protocol_sha256':sha(P/'PROTOCOL.md'),'source_sha256':sha(S/'dense/candidates.json'),'items':manifest},indent=2)+'\n');seal=sha(P/'candidates.json');predict_seconds=time.perf_counter()-start
 (P/'blind/request.json').write_text(json.dumps({'instruction':'Transcribe the visible principal line diplomatically. Report unreadable/clipped glyphs and visual role. No modernizing or adding invisible words.','items':sorted(views,key=lambda x:x['id'])},indent=2)+'\n')
 rows=[]
 for m in mapping:
  raw,mask=arrays[m['id']];gray=cv2.cvtColor(raw,cv2.COLOR_BGR2GRAY);_,ink=cv2.threshold(gray,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU);ink=ink>0;a,b,c,d=m['crop_box'];xml=ROOT/'corpora/chronicling-germany/annotations'/f"{m['page']}.xml";assert sha(xml)==m['xml_sha256'];root=ET.parse(xml).getroot();ns={'p':root.tag.split('}')[0][1:]};own=np.zeros(gray.shape,np.uint8);other=own.copy()
  for el in root.findall('.//p:TextLine',ns):
   node=el.find('p:Coords',ns)
   if node is None:continue
   pts=np.array([[float(v) for v in p.split(',')] for p in node.get('points').split()])-np.array([a,b]);rm=np.zeros(gray.shape,np.uint8);cv2.fillPoly(rm,[np.rint(pts).astype(np.int32)],1)
   if el.get('id')==m['line_id']:own=rm
   else:other|=rm
  mainink=ink&(own>0);neighbor=ink&(other>0)&(own==0);keep=mask>0;before=int(neighbor.sum());after=int((neighbor&keep).sum());total=int(mainink.sum());retained=int((mainink&keep).sum());rows.append({'a81_id':m['id'],'assigned_ink_before':total,'assigned_ink_retained':retained,'retained_fraction':retained/max(1,total),'neighbor_ink_before':before,'neighbor_ink_after':after,'neighbor_reduction':1-after/max(1,before),'local_keep':retained/max(1,total)>=.995})
 assert sha(P/'candidates.json')==seal
 gate=all(x['local_keep'] and x['neighbor_ink_after']<=x['neighbor_ink_before'] for x in rows) and next(x for x in rows if x['a81_id']=='V243d7aaa')['neighbor_reduction']>=.9
 report={'status':'consumed_fixed_predicted_contour_mask','rows':rows,'local_gate_passed':gate,'prediction_seconds':predict_seconds,'seconds':time.perf_counter()-start,'candidate_sha256_before_xml':seal,'new_model_forwards':0,'global_completion':False,'test_pages_opened':0,'limitations':['Otsu/PAGE pixel attribution is not glyph truth','Six consumed oracle-selected matched crops','Mask can erase detached ink; originals retained']};(P/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
