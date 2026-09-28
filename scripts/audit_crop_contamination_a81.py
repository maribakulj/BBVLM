"""Consumed pixel attribution to existing PAGE polygons, never perfect glyph GT."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
import cv2,numpy as np
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'experiments/loop/next-a81'
def main():
 data=json.loads((P/'private-map.json').read_text());rows=[]
 for m in data['mapping']:
  if m['line_id'] is None:continue
  image=cv2.imread(str(ROOT/m['image_path']),cv2.IMREAD_GRAYSCALE);a,b,c,d=m['crop_box'];crop=image[b:d,a:c];_,ink=cv2.threshold(crop,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU);ink=ink>0
  xml=ROOT/'corpora/chronicling-germany/annotations'/f"{m['page']}.xml";assert hashlib.sha256(xml.read_bytes()).hexdigest()==m['xml_sha256'];root=ET.parse(xml).getroot();ns={'p':root.tag.split('}')[0][1:]};own=np.zeros(crop.shape,np.uint8);other=own.copy();contacts=[]
  for el in root.findall('.//p:TextLine',ns):
   coord=el.find('p:Coords',ns)
   if coord is None:continue
   points=np.array([[float(v) for v in p.split(',')] for p in coord.get('points').split()],np.float32);points-=np.array([a,b]);mask=np.zeros(crop.shape,np.uint8);cv2.fillPoly(mask,[np.rint(points).astype(np.int32)],1)
   if el.get('id')==m['line_id']:own=mask
   else:
    if np.any((mask>0)&ink):contacts.append(el.get('id'))
    other|=mask
  total=int(ink.sum());cont=int(((other>0)&(own==0)&ink).sum());rows.append({'id':m['id'],'crop_ink_pixels':total,'ink_in_assigned_polygon':int(((own>0)&ink).sum()),'ink_in_other_polygons_not_assigned':cont,'other_polygon_ink_fraction':cont/max(1,total),'other_line_polygon_contacts':contacts})
 out={'method':'Otsu ink attributed to immutable PAGE polygons; convention-dependent proxy, not glyph truth','rows':rows,'new_model_forwards':0,'originals_unchanged':True};(P/'contamination.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
