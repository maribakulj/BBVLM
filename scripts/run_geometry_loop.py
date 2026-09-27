"""G01: fixed split, native PERO baseline, development selection, one held-out report.
Inputs use reference lines/text (oracle); results are NOT end-to-end OCR scores.
Every reference word remains in denominator, including failed/unsupported lines.
"""
from pathlib import Path
import sys,json,copy,hashlib,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import cv2,numpy as np
from lxml import etree as E
from pero_ocr.core.layout import PageLayout,RegionLayout
from bbvlm.pero import load_cache
from bbvlm.refine import refine_words
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'experiments/loop/geometry-g01';OUT.mkdir(exist_ok=True)
protocol=json.loads((ROOT/'experiments/loop/protocol.json').read_text())['geometry_experiment']

def box(points):
    p=np.array([[float(x) for x in pair.split(',')] for pair in points.split()]);return [*p.min(0),*p.max(0)]
def native(page_id):
    dest=OUT/(page_id+'.native.json')
    if dest.exists():return json.loads(dest.read_text())
    cache=ROOT/'experiments/loop/cache'/page_id;run=json.loads((cache/'run.json').read_text())
    page,_=load_cache(cache);ix={l.id:l for l in page.lines_iterator()}
    root=E.parse(str(ROOT/run['source_xml']));ns={'p':root.getroot().nsmap[None]};rows=[]
    for node in root.findall('.//p:TextLine',ns):
        words=[]
        for w in node.findall('p:Word',ns):
            t=w.find('p:TextEquiv/p:Unicode',ns);c=w.find('p:Coords',ns)
            words.append({'text':t.text or '' if t is not None else '', 'box':box(c.get('points'))})
        if not words:continue
        row={'id':node.get('id'),'reference':words,'native':[],'error':None}
        line=ix.get(row['id'])
        try:
            if line is None:raise ValueError('missing reference line')
            row['polygon']=line.polygon.tolist();row['line_box']=[float(v) for v in [*line.polygon.min(0),*line.polygon.max(0)]]
            line.transcription=' '.join(w['text'] for w in words)
            codec=set(line.characters[:-1]) if len(line.characters)==line.logits.shape[1] else set(line.characters)
            row['unsupported']=sorted(set(line.transcription)-codec)
            # Use the native baseline exactly, including its unknown-glyph handling.
            p=PageLayout(id=page.id,page_size=page.page_size)
            r=RegionLayout(id='region',polygon=line.polygon);r.lines=[line];p.regions=[r]
            xml=E.fromstring(p.to_altoxml_string().encode())
            for w in xml.findall('.//{*}String'):
                x,y=float(w.get('HPOS')),float(w.get('VPOS'))
                row['native'].append({'text':w.get('CONTENT'),'box':[x,y,x+float(w.get('WIDTH')),y+float(w.get('HEIGHT'))]})
            row['confidence']=float(line.transcription_confidence or 0)
            if [w['text'] for w in row['native']]!=[w['text'] for w in words]:row['error']='native tokenization mismatch'
        except Exception as e:row['error']=type(e).__name__+': '+str(e)
        rows.append(row)
    result={'page':page_id,'image':run['image'],'rows':rows,'scope':'oracle lines and word text; native baseline unknown-character handling retained and flagged'}
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2));return result

def scores(data,config):
    gray=cv2.imread(str(ROOT/data['image']),0) if config else None
    ious=[];horizontal=[];vertical=[];fail=[];details=[];missing=0;unsupported=0;zero=0;degraded=0
    for row in data['rows']:
        gt=row['reference'];pred=row['native']
        unsupported+=bool(row.get('unsupported'));zero+=row.get('confidence')==0
        if row['error']:
            missing+=len(gt);ious.extend([0.]*len(gt));fail.append({'id':row['id'],'error':row['error'],'words':len(gt)});continue
        boxes=[p['box'] for p in pred]
        if config:boxes=refine_words(gray,boxes,row['polygon'],row['line_box'],**config)
        for ref,b in zip(gt,boxes):
            a=ref['box'];ix=max(0,min(a[2],b[2])-max(a[0],b[0]));iy=max(0,min(a[3],b[3])-max(a[1],b[1]));inter=ix*iy
            union=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter
            v=inter/union if union>0 else 0;ious.append(v)
            charwidth=max(1,(a[2]-a[0])/max(1,len(ref['text'])))
            he=max(abs(a[0]-b[0]),abs(a[2]-b[2]))/charwidth
            ve=max(abs(a[1]-b[1]),abs(a[3]-b[3]))/max(1,a[3]-a[1])
            horizontal.append(he);vertical.append(ve)
            details.append({'line':row['id'],'text':ref['text'],'iou':v,'horizontal_error_charwidth':he,'reference':a,'prediction':b})
    def dist(xs):return {'mean':float(np.mean(xs)),'p95':float(np.percentile(xs,95)),'p99':float(np.percentile(xs,99)),'max':float(max(xs))} if xs else None
    return {'words':len(ious),'missing_words':missing,'mean_iou':float(np.mean(ious)), 'iou_ge_05':sum(v>=.5 for v in ious)/len(ious),'iou_ge_075':sum(v>=.75 for v in ious)/len(ious),'horizontal_boundary_error_charwidth':dist(horizontal),'vertical_boundary_error_lineheight':dist(vertical),'failed_lines':fail,'lines_with_unsupported_characters':unsupported,'native_zero_confidence_lines':zero,'worst_words':sorted(details,key=lambda v:v['iou'])[:20]}

def eligible(a,b):return a['missing_words']<=b['missing_words'] and a['horizontal_boundary_error_charwidth']['p95']<=b['horizontal_boundary_error_charwidth']['p95']+1e-9

selected=OUT/'frozen_candidate.json'
if not selected.exists():
    dev=native(protocol['development_pages'][0]);baseline=scores(dev,None);trials=[]
    for mode in ['vertical','xy']:
        for margin in [0,1,2]:
            for binarization in ['otsu','local']:
                conf={'mode':mode,'margin':margin,'min_area':2,'binarization':binarization,'max_shrink':.5}
                s=scores(dev,conf);trials.append({'config':conf,'scores':s,'eligible':eligible(s,baseline)})
                print('dev',conf,'iou',round(s['mean_iou'],5),'eligible',eligible(s,baseline),flush=True)
    winner=max([t for t in trials if t['eligible']],key=lambda t:t['scores']['mean_iou'],default=None)
    (OUT/'development.json').write_text(json.dumps({'baseline':baseline,'trials':trials},indent=2))
    frozen={'config':winner['config'] if winner and winner['scores']['mean_iou']>baseline['mean_iou'] else None,'development_gain':winner['scores']['mean_iou']-baseline['mean_iou'] if winner else 0,'frozen_at_unix':time.time(),'source_sha256':hashlib.sha256((ROOT/'src/bbvlm/refine.py').read_bytes()).hexdigest()}
    selected.write_text(json.dumps(frozen,indent=2))
frozen=json.loads(selected.read_text())
assert frozen['source_sha256']==hashlib.sha256((ROOT/'src/bbvlm/refine.py').read_bytes()).hexdigest(),'candidate changed after freeze'
report=OUT/'heldout.json'
if not report.exists():
    results=[]
    for p in protocol['heldout_pages']:
        data=native(p);b=scores(data,None);a=scores(data,frozen['config'])
        passed=eligible(a,b) and a['mean_iou']>b['mean_iou']
        results.append({'page':p,'baseline':b,'candidate':a,'gate_passed':passed});print('heldout',p,b['mean_iou'],a['mean_iou'],passed,flush=True)
    report.write_text(json.dumps({'frozen_candidate':frozen,'results':results,'gate_passed':all(r['gate_passed'] for r in results),'scope': 'conditional geometry only; two heldout pages; not end-to-end or cross-domain; test is now consumed'},indent=2))
print(report,flush=True)
