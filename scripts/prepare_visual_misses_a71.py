"""Prepare opaque, text-blind views of A70 zero-contributor line residuals."""
import hashlib, json
from pathlib import Path
from PIL import Image
from evaluate_transfer_a69 import ROOT, parse_xml

A70=ROOT/'experiments/loop/next-a70'; OUT=ROOT/'experiments/loop/next-a71'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 rows=json.loads((A70/'report-v2.json').read_text())['rows']
 zero=[r for r in rows if not r['contributors']]
 zero.sort(key=lambda r: hashlib.sha256(('a71:'+r['page']+':'+r['line_id']).encode()).hexdigest())
 picked=[]; per={}
 for r in zero:
  if per.get(r['page'],0)>=2: continue
  picked.append(r); per[r['page']]=per.get(r['page'],0)+1
  if len(picked)==12: break
 expected={r['file']:r['sha256'] for r in json.loads((ROOT/'experiments/loop/chronicling-a58/audit.json').read_text())['files_detail']}
 views=OUT/'views';views.mkdir(parents=True,exist_ok=True); manifest=[]; private=[]
 for n,r in enumerate(picked,1):
  _,lines,_=parse_xml(r['page'],expected); poly=dict(lines)[r['line_id']]
  x0,y0,x1,y1=poly.bounds; image=Image.open(ROOT/'corpora/chronicling-germany/images'/f"{r['page']}.jpg").convert('RGB')
  px=max(40,int((x1-x0)*.12));py=max(30,int((y1-y0)*1.2))
  crop=image.crop((max(0,int(x0)-px),max(0,int(y0)-py),min(image.width,int(x1)+px),min(image.height,int(y1)+py)))
  oid=f'Q{n:03d}'; path=views/f'{oid}.png';crop.save(path)
  manifest.append({'id':oid,'path':str(path.relative_to(ROOT)),'sha256':sha(path),'width':crop.width,'height':crop.height})
  private.append({'id':oid,'page':r['page'],'line_id':r['line_id'],'bounds':[x0,y0,x1,y1]})
 (OUT/'manifest.json').write_text(json.dumps({'schema':'bbvlm.a71.views/1','views':manifest,'no_transcript_exposed':True},indent=2)+'\n')
 (OUT/'private-map.json').write_text(json.dumps(private,indent=2)+'\n')
 print(json.dumps({'views':len(manifest),'pages':per},indent=2))
if __name__=='__main__':main()
