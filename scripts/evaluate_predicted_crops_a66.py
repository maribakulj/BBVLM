"""Image-only predictions first; sealed XML geometry scoring afterwards."""
import collections, hashlib, importlib.metadata, json, time, xml.etree.ElementTree as ET
from pathlib import Path
import torch
from doclayout_yolo import YOLOv10
from shapely.geometry import box
from shapely.ops import unary_union
from evaluate_crop_geometry_a65 import polygon
from fetch_crop_pilot_a66 import NAMES
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'experiments/loop/next-a66'
WEIGHTS=ROOT/'models/doclayout-yolo/doclayout_yolo_docstructbench_imgsz1024.pt'
def coverage(line, boxes):
    best=max((line.intersection(p).area/line.area for p in boxes),default=0.)
    union=line.intersection(unary_union(boxes)).area/line.area if boxes else 0.
    assert -1e-8<=best<=union+1e-8 and union<=1+1e-8
    return min(1.,best),min(1.,union)
def main():
    assert coverage(box(0,0,10,2),[box(0,0,5,2),box(5,0,10,2)])==(.5,1.)
    assert coverage(box(0,0,10,2),[])==(0.,0.)
    assets=json.loads((OUT/'assets-v2.json').read_text())
    assert [r['page'] for r in assets['images']]==NAMES
    for r in assets['images']:
        assert hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256']
    assert hashlib.sha256(WEIGHTS.read_bytes()).hexdigest()=='9a2ee0220fe3d9ad31b47e1d9f1282f46959a54e4618fce9cffcc9715b8286e2'
    # This upstream pickle checkpoint is allowed only after its public digest is verified.
    torch.set_num_threads(4);torch.set_num_interop_threads(1)
    started=time.perf_counter();model=YOLOv10(str(WEIGHTS));predictions=[]
    for size in (1024,1600):
        for r in assets['images']:
            t=time.perf_counter()
            result=model.predict(str(ROOT/r['path']),imgsz=size,conf=.2,max_det=300,device='cpu',verbose=False,save=False)[0]
            boxes=[{'bbox':list(map(float,b)),'confidence':float(s),'class_id':int(c),'class_name':result.names[int(c)]}
                   for b,s,c in zip(result.boxes.xyxy.tolist(),result.boxes.conf.tolist(),result.boxes.cls.tolist())]
            predictions.append({'page':r['page'],'imgsz':size,'seconds':time.perf_counter()-t,'shape':list(result.orig_shape),'names':result.names,'boxes':boxes})
            print(r['page'],size,len(boxes),flush=True)
    inference_seconds=time.perf_counter()-started
    (OUT/'predictions.json').write_text(json.dumps(predictions,indent=2)+'\n')
    # No XML is opened before the image-only predictions have been saved.
    expected={r['file']:r['sha256'] for r in json.loads((ROOT/'experiments/loop/chronicling-a58/audit.json').read_text())['files_detail']}
    scores=[];invalid={};fingerprints={}
    for name in NAMES:
        path=ROOT/'corpora/chronicling-germany/annotations'/f'{name}.xml';raw=path.read_bytes()
        fingerprints[name]=hashlib.sha256(raw).hexdigest();assert fingerprints[name]==expected[path.name]
        root=ET.fromstring(raw);ns={'p':root.tag.split('}')[0][1:]};page=root.find('p:Page',ns)
        regions=[];lines=[];bad=collections.Counter()
        for el in page.findall('p:TextRegion',ns):
            p=polygon(el,ns)
            if p is None:bad['regions']+=1
            else:regions.append(p)
            for le in el.findall('p:TextLine',ns):
                lp=polygon(le,ns)
                if lp is None:bad['lines']+=1
                else:lines.append((le.get('id'),lp))
        invalid[name]=dict(bad)
        for pred in [p for p in predictions if p['page']==name]:
            assert pred['shape']==[int(page.get('imageHeight')),int(page.get('imageWidth'))]
            for policy in ('all','text_like'):
                selected=[b for b in pred['boxes'] if policy=='all' or b['class_id'] not in (3,5)]
                boxes=[box(*b['bbox']) for b in selected]
                rows=[]
                for lid,line in lines:
                    best,union=coverage(line,boxes)
                    rows.append({'id':lid,'best':best,'union':union})
                foreign=[]
                for crop in boxes:
                    intersections=[crop.intersection(r).area for r in regions]
                    if not intersections or max(intersections)==0:
                        foreign.append({'matched':False,'fraction':None});continue
                    ri=max(range(len(regions)),key=lambda i:intersections[i])
                    others=unary_union([r for i,r in enumerate(regions) if i!=ri])
                    fraction=crop.difference(regions[ri]).intersection(others).area/crop.area
                    assert 0<=fraction<=1+1e-8
                    foreign.append({'matched':True,'fraction':fraction})
                scores.append({'page':name,'imgsz':pred['imgsz'],'policy':policy,'lines':len(rows),'boxes':len(boxes),
                    'missed_union_lt50':sum(r['union']<.5 for r in rows),
                    'incomplete_single_lt95':sum(r['best']<.95 for r in rows),
                    'fragmented':sum(r['union']>=.95 and r['best']<.95 for r in rows),
                    'foreign_gt1pct':sum((r['fraction'] or 0)>.01 for r in foreign),'line_detail':rows,'crop_detail':foreign})
    summary={}
    for size in (1024,1600):
        for policy in ('all','text_like'):
            group=[s for s in scores if s['imgsz']==size and s['policy']==policy]
            summary[f'{size}_{policy}']={k:sum(r[k] for r in group) for k in ('lines','boxes','missed_union_lt50','incomplete_single_lt95','fragmented','foreign_gt1pct')}
    report={'status':'consumed_development_transfer_not_independent_validation','summary':summary,'scores':scores,
        'invalid':invalid,'xml_sha256':fingerprints,'model_forwards':10,'vlm_calls':0,'ocr_calls':0,'test_pages_opened':0,
        'inference_wall_seconds':inference_seconds,'total_seconds':time.perf_counter()-started,
        'versions':{k:importlib.metadata.version(k) for k in ('torch','torchvision','doclayout_yolo','numpy','shapely')},
        'all_scientific_gates_passed':False,'warning':'Annotation-area coverage is not character recall, CER, word-box accuracy or article-order truth.'}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
