"""Prepare a consumed, oracle-selected blind visual audit; preserve sources."""
import hashlib,json,math,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image,ImageDraw
from shapely.geometry import box
from evaluate_crop_geometry_a65 import polygon
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'experiments/loop/next-a67'
def main():
    scores=json.loads((ROOT/'experiments/loop/next-a66/report.json').read_text())
    preds=json.loads((ROOT/'experiments/loop/next-a66/predictions.json').read_text())
    cases=[];private=[];ids=['K482','K719','K263','K951'];blind=OUT/'blind';blind.mkdir(parents=True,exist_ok=True)
    for s in scores['scores']:
        if s['imgsz']!=1024 or s['policy']!='text_like':continue
        candidates=sorted([x for x in s['line_detail'] if x['union']>=.95 and x['best']<.95],key=lambda x:x['id'])
        if not candidates:continue
        row=candidates[0];name=s['page'];opaque=ids[len(cases)]
        path=ROOT/'corpora/chronicling-germany/annotations'/f'{name}.xml';raw=path.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==scores['xml_sha256'][name]
        tree=ET.fromstring(raw);ns={'p':tree.tag.split('}')[0][1:]}
        line=next(e for e in tree.findall('.//p:TextLine',ns) if e.get('id')==row['id']);shape=polygon(line,ns)
        pred=next(p for p in preds if p['page']==name and p['imgsz']==1024)
        boxes=[b for b in pred['boxes'] if b['class_id'] not in (3,5)]
        chosen=max(boxes,key=lambda b:shape.intersection(box(*b['bbox'])).area)
        source=ROOT/'corpora/chronicling-germany/images'/f'{name}.jpg';im=Image.open(source).convert('RGB');w,h=im.size
        x0,y0,x1,y1=chosen['bbox'];bounds=[max(0,math.floor(x0)),max(0,math.floor(y0)),min(w,math.ceil(x1)),min(h,math.ceil(y1))]
        lx,ly,rx,ry=shape.bounds;context=[max(0,math.floor(lx)-100),max(0,math.floor(ly)-100),min(w,math.ceil(rx)+100),min(h,math.ceil(ry)+100)]
        cut=im.crop(bounds);plain=im.crop(context);marked=plain.copy();draw=ImageDraw.Draw(marked)
        draw.rectangle([x0-context[0],y0-context[1],x1-context[0],y1-context[1]],outline='red',width=2)
        views=[]
        for label,img in [('crop',cut),('context',plain),('boundary',marked)]:
            target=blind/f'{opaque}-{label}.png';img.save(target)
            views.append({'role':label,'path':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'size':list(img.size)})
        cases.append({'id':opaque,'views':views});private.append({'id':opaque,'page':name,'line_id':row['id'],'metric':row,'box':chosen,'context':context,'integer_crop':bounds,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
    assert len(cases)==4
    cases.sort(key=lambda c:hashlib.sha256(c['id'].encode()).hexdigest())
    request={'schema':'bbvlm.visual-crop-audit/1','cases':cases,'instruction':'Inspect every native image; compare crop with unmarked context and red boundary. Report visible clipping yes/no/uncertain, affected_edge, evidence, additional_text_separate yes/no/uncertain, confidence and uncertainties. Do not assume there is an error. Return exact IDs; record inspected paths.'}
    (blind/'request.json').write_text(json.dumps(request,indent=2)+'\n');(OUT/'private-map.json').write_text(json.dumps(private,indent=2)+'\n')
    print(json.dumps({'cases':4,'views':12,'test_pages_opened':0}))
if __name__=='__main__':main()
