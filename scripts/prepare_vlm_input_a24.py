"""Prepare reference-blind multiscale composites for one Sol diagnostic pass."""
from pathlib import Path
import json
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/loop';A22=BASE/'reserve-a22';OUT=BASE/'vlm-input-a24';SRC=BASE/'reference-a18/source'

def main():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'input').mkdir(exist_ok=True)
    rows=json.loads((A22/'private-reference.json').read_text())
    items=[]
    for row in rows:
        image=cv2.imread(str(SRC/row['source_image']))
        x0,y0,x1,y1=map(int,row['line_bbox']);h=max(8,y1-y0);w=max(8,x1-x0)
        # Full page locator: no OCR annotation, only a thin target rectangle.
        page=image.copy();cv2.rectangle(page,(x0,y0),(x1,y1),(0,0,255),4)
        scale=min(1.,1100/page.shape[1]);page=cv2.resize(page,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA)
        # Three line-heights of context, kept wide enough for whole target.
        mx=max(8,int(.02*w));cy0=max(0,y0-h);cy1=min(image.shape[0],y1+h)
        cx0=max(0,x0-mx);cx1=min(image.shape[1],x1+mx)
        context=image[cy0:cy1,cx0:cx1].copy()
        ty0=y0-cy0;ty1=y1-cy0;tx0=x0-cx0;tx1=x1-cx0
        cv2.rectangle(context,(tx0,ty0),(tx1,ty1),(0,0,255),2)
        context=cv2.resize(context,None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)
        # High-resolution isolated line with symmetric vertical/horizontal margin.
        pad_y=max(3,int(.15*h));pad_x=max(3,int(.01*w))
        crop=image[max(0,y0-pad_y):min(image.shape[0],y1+pad_y),max(0,x0-pad_x):min(image.shape[1],x1+pad_x)]
        crop=cv2.resize(crop,None,fx=4,fy=4,interpolation=cv2.INTER_LANCZOS4)
        target_w=max(page.shape[1],context.shape[1],crop.shape[1])
        panels=[]
        for panel in (page,context,crop):
            canvas=np.full((panel.shape[0],target_w,3),255,np.uint8)
            off=(target_w-panel.shape[1])//2;canvas[:,off:off+panel.shape[1]]=panel;panels.append(canvas)
        composite=np.vstack(panels)
        path=OUT/'input'/f"{row['id']}.png";cv2.imwrite(str(path),composite)
        items.append({'id':row['id'],'image':str(path.relative_to(ROOT)),
                      'panels':['full_page_locator','three_line_context_2x','isolated_line_4x']})
    request={'schema':'bbvlm.vlm-input-ablation-a24/1','consumed_diagnostic':True,'items':items,
      'task':'Transcribe only the target line. Preserve visible historical spelling, case, punctuation, printed hyphens, long s ſ, r rotunda ꝛ and abbreviation marks. Do not modernize or expand. Readable ligatures may be decomposed. Encode visible overbars using a precomposed macron where possible. Never invent private-use codes. Return JSON lines [{id,text,uncertain,reason}].'}
    (OUT/'input/request.json').write_text(json.dumps(request,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'items':len(items),'max_bytes':max((OUT/'input'/f"{r['id']}.png").stat().st_size for r in rows)}))
if __name__=='__main__':main()

