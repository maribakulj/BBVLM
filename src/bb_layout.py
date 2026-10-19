"""Propositions géométriques OLR depuis les pixels, sans lecteur ni référence."""
from pathlib import Path
import argparse
import hashlib
import json
import time

MODEL='PaddlePaddle/PP-DocLayoutV3_safetensors'
NON_TEXT={'image','chart','table','formula','seal'}


def separators(image):
    """Traits longs détectés dans l'encre native, jamais positions supposées."""
    import cv2
    gray=cv2.imread(str(image),cv2.IMREAD_GRAYSCALE)
    if gray is None:raise ValueError('image illisible')
    h,w=gray.shape
    mask=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY_INV,51,15)
    rows=[]
    for axis,kernel in [('horizontal',(max(101,round(w*.035)|1),1)),
                        ('vertical',(1,max(101,round(h*.035)|1)))]:
        opened=cv2.morphologyEx(mask,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,kernel))
        _,_,stats,_=cv2.connectedComponentsWithStats(opened,8)
        for x,y,bw,bh,area in stats[1:]:
            if axis=='horizontal' and (bw<10*bh or bh>.008*h):continue
            if axis=='vertical' and (bh<10*bw or bw>.008*w):continue
            rows.append(dict(id=f'S_{len(rows):04d}',label='separator',bbox=[int(x),int(y),int(x+bw),int(y+bh)],
                             score=1.,source='native_adaptive_ink_morphology',axis=axis))
    return rows


def nontext_regions(data, threshold=.5):
    kept=[]
    proposals=[b for b in data['blocks'] if b['label'] in {'image','chart','seal'} and b['score']>=threshold]
    for b in sorted(proposals,key=lambda b:-b['score']):
        x0,y0,x1,y1=b['bbox'];area=(x1-x0)*(y1-y0)
        if any(max(0,min(c['bbox'][2],x1)-max(c['bbox'][0],x0))*
               max(0,min(c['bbox'][3],y1)-max(c['bbox'][1],y0))/
               max(1,min(area,(c['bbox'][2]-c['bbox'][0])*(c['bbox'][3]-c['bbox'][1])))>=.8 for c in kept):
            continue
        kept.append({**b,'source':MODEL})
    return kept+data.get('separators',[])


def text_regions(data, threshold=.3):
    """Déduplication spatiale, sans utiliser de texte ni de régions humaines.

    Les candidats exclus restent dans le fichier brut pour mesurer omissions
    et non-texte ; ce filtre n'est pas une certification de couverture.
    """
    kept=[]
    for block in sorted(data['blocks'],key=lambda b:-b['score']):
        if block['score'] < threshold or block['label'] in NON_TEXT:
            continue
        x0,y0,x1,y1=block['bbox'];area=(x1-x0)*(y1-y0)
        duplicate=False
        for other in kept:
            a,b,c,d=other['bbox']
            inter=max(0,min(c,x1)-max(a,x0))*max(0,min(d,y1)-max(b,y0))
            if inter/max(1,min(area,(c-a)*(d-b))) >= .8:
                duplicate=True;break
        if not duplicate:
            kept.append(block)
    return sorted(kept,key=lambda b:b['rank'])


def detect(image,output,floor=.1):
    import torch
    from PIL import Image
    from transformers import AutoImageProcessor,AutoModelForObjectDetection
    torch.set_num_threads(4)
    im=Image.open(image).convert('RGB')
    model=AutoModelForObjectDetection.from_pretrained(MODEL,local_files_only=True).eval()
    processor=AutoImageProcessor.from_pretrained(MODEL,local_files_only=True)
    t=time.time();inputs=processor(images=im,return_tensors='pt')
    with torch.inference_mode():
        outputs=model(**inputs)
    result=processor.post_process_object_detection(outputs,threshold=floor,
                target_sizes=[(im.height,im.width)])[0]
    blocks=[]
    for i,(score,label,box) in enumerate(zip(result['scores'],result['labels'],result['boxes'])):
        x0,y0,x1,y1=map(float,box.tolist())
        bbox=[max(0,x0),max(0,y0),min(im.width,x1),min(im.height,y1)]
        if bbox[2]<=bbox[0] or bbox[3]<=bbox[1]:
            continue
        blocks.append(dict(id=f'R_{i:04d}',label=model.config.id2label[int(label)],
                           bbox=bbox,score=float(score),rank=i))
    data=dict(model=MODEL,revision=getattr(model.config,'_commit_hash',None),
              image=str(Path(image).resolve()),image_sha256=hashlib.sha256(Path(image).read_bytes()).hexdigest(),
              size=list(im.size),floor=floor,seconds=time.time()-t,blocks=blocks,
              separators=separators(image),version='image-layout-v1',
              scope='geometry candidates; Gemini classification/articles and independent evaluation still required')
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    return data


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('image');ap.add_argument('output');args=ap.parse_args()
    data=detect(args.image,args.output)
    print(json.dumps(dict(blocks=len(data['blocks']),seconds=data['seconds'],labels=sorted({b['label'] for b in data['blocks'] if b['score']>=.5}))))
