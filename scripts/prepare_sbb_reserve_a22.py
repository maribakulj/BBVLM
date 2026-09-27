"""Open the pre-frozen SBB reserve exactly once and make blind Sol inputs."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, random, time, urllib.request
import cv2
import numpy as np
from lxml import etree as E

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/loop'
SOURCE=BASE/'reference-a18'
OUT=BASE/'reserve-a22'
REPO='OCR-D/OCR-D-GT-VD-SBB'
SEED=2026092722

def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def fetch(job):
    revision,relative,blob=job
    dest=SOURCE/'source'/relative
    if not dest.exists():
        url=f'https://raw.githubusercontent.com/{REPO}/{revision}/{relative}'
        with urllib.request.urlopen(url,timeout=60) as response: data=response.read()
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    data=dest.read_bytes()
    assert hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()==blob
    return {'path':relative,'bytes':len(data),'sha256':sha(dest),'git_blob_verified':True}

def points(node):
    return np.array([list(map(float,p.split(','))) for p in node.find('{*}Coords').get('points').split()])

def bbox(pts):
    return [float(pts[:,0].min()),float(pts[:,1].min()),float(pts[:,0].max()),float(pts[:,1].max())]

def text(node): return node.findtext('{*}TextEquiv/{*}Unicode') or ''

def main():
    assert (OUT/'PROTOCOL.md').exists(), 'Protocol must predate reserve opening'
    split=json.loads((SOURCE/'split.json').read_text())
    reserve=[p for p in split['pages'] if p['role']=='reserve']
    assert len(reserve)==4
    jobs=[(split['revision'],p[k],p[k+'_blob']) for p in reserve for k in ('xml','image')]
    started=time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as pool: files=list(pool.map(fetch,jobs))
    private=[];items=[];pages=[]
    for page in reserve:
        tree=E.parse(str(SOURCE/'source'/page['xml']))
        image=cv2.imread(str(SOURCE/'source'/page['image']))
        assert image is not None
        pn=tree.find('.//{*}Page')
        assert image.shape[1]==int(pn.get('imageWidth')) and image.shape[0]==int(pn.get('imageHeight'))
        lines=tree.findall('.//{*}TextLine')
        candidates=[l for l in lines if l.find('{*}TextEquiv') is not None]
        # Sampling key is ID only; content is not used to choose difficult/easy lines.
        chosen=random.Random(f'{SEED}:{page["work"]}').sample(sorted(candidates,key=lambda x:x.get('id')),min(4,len(candidates)))
        pages.append({'work':page['work'],'lines':len(lines),'sampled':len(chosen),'words':len(tree.findall('.//{*}Word'))})
        for line in chosen:
            token='R'+hashlib.sha256((page['xml']+line.get('id')).encode()).hexdigest()[:10]
            pts=points(line);b=bbox(pts)
            x0=max(0,int(np.floor(b[0]))-3);y0=max(0,int(np.floor(b[1]))-3)
            x1=min(image.shape[1],int(np.ceil(b[2]))+4);y1=min(image.shape[0],int(np.ceil(b[3]))+4)
            crop=image[y0:y1,x0:x1].copy();target=crop.copy()
            mask=np.zeros(crop.shape[:2],np.uint8)
            cv2.fillPoly(mask,[np.rint(pts-[x0,y0]).astype(np.int32)],255)
            mask=cv2.dilate(mask,np.ones((3,3),np.uint8));target[mask==0]=255
            target_path=OUT/'input'/f'{token}.png';context_path=OUT/'input'/f'{token}-context.png'
            target_path.parent.mkdir(parents=True,exist_ok=True)
            assert cv2.imwrite(str(target_path),target) and cv2.imwrite(str(context_path),crop)
            items.append({'id':token,'image':str(target_path.relative_to(ROOT)),
                          'original_image':str(context_path.relative_to(ROOT))})
            private.append({'id':token,'work':page['work'],'line_id':line.get('id'),'text':text(line),
              'polygon':pts.tolist(),'line_bbox':b,'crop_bbox':[x0,y0,x1,y1],
              'source_image':page['image'],'words':[{'text':text(w),'bbox':bbox(points(w))} for w in line.findall('{*}Word')]})
    random.Random(SEED).shuffle(items)
    task=('Transcribe only the isolated target line. Preserve visible historical spelling, case, punctuation, printed hyphens, long s ſ, r rotunda ꝛ and abbreviation marks. Do not modernize or expand. Readable ligatures may be decomposed; encode a visible e-above as combining U+0364. Use original_image only as glyph context. Flag uncertainty rather than inventing private-use codes. Return JSON lines [{id,text,uncertain,reason}].')
    write(OUT/'input/request.json',{'schema':'bbvlm.sbb-reserve-blind/1','items':items,'task':task})
    write(OUT/'private-reference.json',private)
    write(OUT/'opened.json',{'schema':'bbvlm.sbb-reserve-open/1','revision':split['revision'],'seed':SEED,
      'selection':'four TextLine IDs sampled per pre-frozen reserve work; content not used for difficulty selection',
      'pages':pages,'files':files,'sample_lines':len(private),'runtime_seconds':time.perf_counter()-started,
      'protocol_sha256':sha(OUT/'PROTOCOL.md'),'cost':{'layout':0,'recognition':0,'vlm':0}})
    print(json.dumps({'pages':pages,'sample_lines':len(private)},indent=2))

if __name__=='__main__': main()
