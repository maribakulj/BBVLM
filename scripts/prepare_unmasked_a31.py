"""A31 posthoc input ablation: identical A30 targets, untouched pixels + context."""
import hashlib,json,time
from pathlib import Path
import cv2

ROOT=Path(__file__).resolve().parents[1]
A30=ROOT/'experiments/loop/bnf-region-ocr-a30'
EXP=ROOT/'experiments/loop/unmasked-a31'

def main():
    source=A30/'opened/IMPACT/T/00123532.tif'
    page=cv2.imread(str(source)); h,w=page.shape[:2]
    refs=json.loads((A30/'private-reference.json').read_text())['items']
    dest=EXP/'input';dest.mkdir(parents=True,exist_ok=True)
    items=[]
    for token,item in sorted(refs.items()):
        x0,y0,x1,y1=item['crop_bbox']; files={}
        for kind,box in [('target',(x0,y0,x1,y1)),('context',(max(0,x0-12),max(0,y0-65),min(w,x1+12),min(h,y1+65)))]:
            a,b,c,d=box; crop=page[b:d,a:c].copy()
            if crop.shape[1]<1200:
                scale=1200/crop.shape[1];crop=cv2.resize(crop,(1200,round(crop.shape[0]*scale)),interpolation=cv2.INTER_CUBIC)
            path=dest/f'{token}-{kind}.png';cv2.imwrite(str(path),crop)
            files[kind]={'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        items.append({'id':token,**files})
    (EXP/'task.json').write_text(json.dumps({'items':items,'output':'experiments/loop/unmasked-a31/sol.json'},indent=2)+'\n')
    (EXP/'manifest.json').write_text(json.dumps({'created_unix':time.time(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'status':'posthoc development ablation on consumed A30; not independent validation','same_ids_and_targets':True,'changes':['no polygon masking','no red overlay','separate unmasked context 65px above/below, 12px left/right'],'unchanged':['same TIFF','same targets','minimum width 1200 cubic interpolation','same transcription contract except target designation'],'new_vlm_tasks_planned':1},indent=2)+'\n')

if __name__=='__main__':main()
