"""Compare crop support in source pixel coordinates, with unchanged PAGE references."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
import cv2,numpy as np
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'experiments/loop/next-a83'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 pred=json.loads((P/'predictions.json').read_text());old={x['id']:x for x in json.loads((ROOT/'experiments/loop/next-a81/private-map.json').read_text())['mapping']};rows=[]
 for c in pred['selected_crops']:
  assert sha(ROOT/c['map_file'])==c['map_sha256'] and sha(ROOT/c['file'])==c['sha256'];m=old[c['a81_id']];image=cv2.imread(str(ROOT/m['image_path']),cv2.IMREAD_GRAYSCALE);assert sha(ROOT/m['image_path'])==m['image_sha256'];_,ink=cv2.threshold(image,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU);ink=ink>0
  xml=ROOT/'corpora/chronicling-germany/annotations'/f"{m['page']}.xml";assert sha(xml)==m['xml_sha256'];root=ET.parse(xml).getroot();ns={'p':root.tag.split('}')[0][1:]};own=np.zeros(image.shape,np.uint8);other=own.copy()
  for el in root.findall('.//p:TextLine',ns):
   node=el.find('p:Coords',ns)
   if node is None:continue
   pts=np.array([[float(v) for v in p.split(',')] for p in node.get('points').split()]);rm=np.zeros(image.shape,np.uint8);cv2.fillPoly(rm,[np.rint(pts).astype(np.int32)],1)
   if el.get('id')==m['line_id']:own=rm
   else:other|=rm
  xy=np.load(ROOT/c['map_file'])['xy'];boundary=np.concatenate([xy[0,:,:],xy[1:,-1,:],xy[-1,-2::-1,:],xy[-2:0:-1,0,:]],axis=0);new=np.zeros(image.shape,np.uint8);cv2.fillPoly(new,[np.rint(boundary).astype(np.int32)],1);base=np.zeros(image.shape,np.uint8);a,b,d,e=m['crop_box'];base[b:e,a:d]=1;target=ink&(own>0);neighbor=ink&(other>0)&(own==0);total=int(target.sum());stats={}
  for label,mask in [('a80_rectangle',base),('pero_baseline_support',new)]:
   k=mask>0;ret=int((k&target).sum());cont=int((k&neighbor).sum());n=int((k&ink).sum());stats[label]={'assigned_ink_retained':ret,'assigned_ink_total':total,'assigned_ink_recall':ret/max(1,total),'other_line_ink':cont,'crop_ink':n,'other_line_ink_fraction':cont/max(1,n)}
  rows.append({'id':m['id'],'association_predicted_box_iou':c['predicted_box_iou'],**stats})
 report={'status':'consumed_source_coordinate_support_audit','rows':rows,'method':'Whole-page Otsu fixed per image; PAGE polygons source attribution; PERO support rasterized from forward-map boundary','limitations':['Polygon/Otsu support proxy is not glyph truth','Rounding/interpolation boundary not exact subpixel visibility','No word geometry or OCR CER measured','Predicted crop association chosen by image-derived boxes; source sample itself consumed/oracle-selected'],'new_model_forwards':0,'global_completion':False};(P/'mapping-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
