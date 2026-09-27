"""Blind random sample of native predicted crops; no reference annotations read."""
from pathlib import Path
import sys,json,random,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from PIL import Image,ImageDraw
from bbvlm.formats import import_xml
from bbvlm.document import save
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/loop/french-vlm';out=base/'input';out.mkdir(parents=True,exist_ok=True)
p=ROOT/'experiments/loop/end-to-end/0253902-001';run=json.loads((p/'run.json').read_text());im=Image.open(ROOT/run['image']).convert('RGB')
from lxml import etree as E
xml=E.parse(str(p/'layout.xml'));repairs=[]
for node in xml.findall('.//{*}Coords')+xml.findall('.//{*}Baseline'):
    before=node.get('points');points=[]
    for pair in before.split():
        x,y=map(float,pair.split(','));points.append(f'{max(0,min(im.width,x))},{max(0,min(im.height,y))}')
    after=' '.join(points)
    if any(float(v)<0 for pair in before.split() for v in pair.split(',')):repairs.append({'id':node.getparent().get('id'),'before':before,'after':after})
    node.set('points',after)
xml.write(str(base/'bounded-input.xml'))
g=import_xml(base/'bounded-input.xml')
g['events'].append({'type':'clip_source_geometry_to_image_bounds','source':'native PERO PAGE','repairs':repairs})
ids={n['id']:n['kind'][0].upper()+hashlib.sha256(n['id'].encode()).hexdigest()[:10] for n in g['nodes']}
source_ids={v:k for k,v in ids.items()}
for n in g['nodes']:
    n['id']=ids[n['id']]
    if n.get('parent'):n['parent']=ids[n['parent']]
    n['page']=ids[n['page']]
    if n['kind']=='page':n['image']=run['image']
g['reading_order']=[];save(g,base/'native.graph.json')
selected=random.Random(20260926).sample([n for n in g['nodes'] if n['kind']=='line'],24)
regions=[{'id':n['id'],'bbox':n['bbox']} for n in g['nodes'] if n['kind']=='region']
manifest={'selection':'uniform sample of 24 predicted lines; seed 20260926; no reference used','requested_line_ids':[n['id'] for n in selected],'regions':regions,'lines':[]}
for si,start in enumerate(range(0,len(selected),6),1):
    batch=selected[start:start+6];crops=[]
    for n in batch:
        x0,y0,x1,y1=n['bbox'];c=im.crop((max(0,int(x0)-3),max(0,int(y0)-3),min(im.width,int(x1)+3),min(im.height,int(y1)+3)))
        crops.append(c)
    canvas=Image.new('RGB',(max(c.width for c in crops)+190,sum(c.height+32 for c in crops)+20),'white');draw=ImageDraw.Draw(canvas);y=10
    for n,c in zip(batch,crops):
        draw.text((5,y+4),n['id'],fill='blue');canvas.paste(c,(180,y));y+=c.height+32
        manifest['lines'].append({'id':n['id'],'region':n['parent'],'bbox':n['bbox'],'sheet':f'lines_{si}.png'})
    canvas.save(out/f'lines_{si}.png')
preview=im.copy();preview.thumbnail((2000,2800));preview.save(out/'page.jpg',quality=95)
(out/'request.json').write_text(json.dumps(manifest,indent=2));(base/'source_ids.json').write_text(json.dumps(source_ids,indent=2))
print('24 blind predicted lines prepared',im.size)
