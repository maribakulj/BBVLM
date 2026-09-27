"""Escalate uncertainty using expanded visual context, never reference text."""
from pathlib import Path
import json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/loop/french-vlm'
r=json.loads((base/'luna.response.json').read_text());request=json.loads((base/'input/request.json').read_text());ix={l['id']:l for l in request['lines']}
run=json.loads((ROOT/'experiments/loop/end-to-end/0253902-001/run.json').read_text());im=Image.open(ROOT/run['image']).convert('RGB');selected=[l for l in r['lines'] if l['uncertain']];out=base/'escalation-input';out.mkdir(exist_ok=True)
items=[];crops=[]
for l in selected:
    box=ix[l['id']]['bbox'];x0,y0,x1,y1=box;expanded=[max(0,int(x0)-70),max(0,int(y0)-15),min(im.width,int(x1)+70),min(im.height,int(y1)+15)]
    crop=im.crop(expanded);draw=ImageDraw.Draw(crop)
    # Thin target tick at left, outside source line pixels; original text remains unobscured.
    draw.line((2,y0-expanded[1],2,y1-expanded[1]),fill='blue',width=2)
    crops.append(crop);items.append({'id':l['id'],'original_bbox':box,'expanded_bbox':expanded,'candidate':l['text'],'reason':l['notes']})
canvas=Image.new('RGB',(max(c.width for c in crops)+190,sum(c.height+40 for c in crops)+20),'white');draw=ImageDraw.Draw(canvas);y=10
for l,c in zip(selected,crops):draw.text((5,y+4),l['id'],fill='blue');canvas.paste(c,(180,y));y+=c.height+40
canvas.save(out/'expanded.png');(out/'request.json').write_text(json.dumps({'requested_line_ids':[l['id'] for l in selected],'rule':'Luna uncertain=true only; no reference read','lines':items},ensure_ascii=False,indent=2))
print(len(items),'uncertain lines escalated')
