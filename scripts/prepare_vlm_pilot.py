"""Prepare a fixed pilot. Reference text never enters the blind input directory."""
from pathlib import Path
import json, hashlib
from PIL import Image, ImageDraw
from lxml import etree
base=Path(__file__).resolve().parents[1]/'experiments/terra_luna'
r=etree.parse(str(base/'reference/page.xml')); ns={'p':r.getroot().nsmap[None]}
im=Image.open(base/'input/page.jpg').convert('RGB')
regions=[];selected=[];refs=[]
for ri,reg in enumerate(r.findall('.//p:TextRegion',ns),1):
 pts=[tuple(map(int,p.split(','))) for p in reg.find('p:Coords',ns).get('points').split()]
 rb=[min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)]
 rid=f'R{ri:02d}';regions.append({'id':rid,'bbox':rb})
 lines=reg.findall('p:TextLine',ns)
 for li,line in enumerate(lines[:3],1):
  pts=[tuple(map(int,p.split(','))) for p in line.find('p:Coords',ns).get('points').split()]
  bb=[min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)]
  lid=f'{rid}_L{li:02d}'
  selected.append({'id':lid,'region':rid,'bbox':bb})
  refs.append({'id':lid,'text':line.findtext('p:TextEquiv/p:Unicode',namespaces=ns),'source_id':line.get('id')})
# The selection depends on region/line indices only, never on text or difficulty.
for si,start in enumerate(range(0,len(selected),8),1):
 batch=selected[start:start+8]; crops=[]
 for line in batch:
  x0,y0,x1,y1=line['bbox'];c=im.crop((max(0,x0-2),max(0,y0-2),min(im.width,x1+2),min(im.height,y1+2)))
  crops.append(c)
 width=max(c.width for c in crops)+180;height=sum(c.height+24 for c in crops)+20
 sheet=Image.new('RGB',(width,height),'white');draw=ImageDraw.Draw(sheet);y=10
 for line,c in zip(batch,crops):
  draw.text((8,y+4),line['id'],fill='blue');sheet.paste(c,(170,y));y+=c.height+24
 sheet.save(base/f'input/lines_{si}.png')
 for l in batch:l['sheet']=f'lines_{si}.png'
context=im.copy();draw=ImageDraw.Draw(context)
for reg in regions:
 draw.rectangle(reg['bbox'],outline='red',width=3);draw.text((reg['bbox'][0],max(0,reg['bbox'][1]-18)),reg['id'],fill='blue',stroke_width=1,stroke_fill='white')
context.save(base/'input/regions.png')
manifest={'page_id':'P1','width':im.width,'height':im.height,'regions':regions,'lines':selected}
(base/'input/manifest.json').write_text(json.dumps(manifest,indent=2))
(base/'reference/selected.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2))
print(len(selected),'lines',len(regions),'regions')
