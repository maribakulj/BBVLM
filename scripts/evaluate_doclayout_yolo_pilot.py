"""Diagnostic DocLayout-YOLO region coverage on consumed Spiritualist 0044."""
from collections import Counter
from pathlib import Path
import json,time

import cv2
import numpy as np
from lxml import etree as E
from doclayout_yolo import YOLOv10

ROOT=Path(__file__).resolve().parents[1]
PAGE="0044";REV="8c3299a30b8ff29a1503c4431b035b93220f7b11"
WEIGHTS=ROOT/"models/doclayout-yolo/doclayout_yolo_docstructbench_imgsz1024.pt"
IMAGE=ROOT/f"corpora/spiritualist/companion/Spiritualist_Images/{PAGE}.png"
OUT=ROOT/"experiments/loop/spiritualist-v1/doclayout-yolo-pilot-0044"
NS={"a":"http://www.loc.gov/standards/alto/ns-v4#"}


def iou(a,b):
    x0,y0=max(a[0],b[0]),max(a[1],b[1]);x1,y1=min(a[2],b[2]),min(a[3],b[3])
    inter=max(0,x1-x0)*max(0,y1-y0)
    return inter/((a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter) if inter else 0.


def main():
    tree=E.parse(str(next((ROOT/"corpora/spiritualist/alto_xml/ocr_gt_labelled").glob(f"{PAGE}_*.xml"))))
    refs=[]
    for b in tree.findall(".//a:TextBlock",NS):
        x,y,w,h=map(float,(b.get("HPOS"),b.get("VPOS"),b.get("WIDTH"),b.get("HEIGHT")))
        refs.append({"id":b.get("ID"),"role":b.get("BLOCK_TYPE"),"bbox":[x,y,x+w,y+h]})
    model=YOLOv10(str(WEIGHTS));start=time.perf_counter()
    result=model.predict(str(IMAGE),imgsz=1024,conf=.2,device="cpu",verbose=False)[0]
    elapsed=time.perf_counter()-start;names=result.names;pred=[]
    if result.boxes is not None:
        for box,score,cls in zip(result.boxes.xyxy.cpu().tolist(),result.boxes.conf.cpu().tolist(),result.boxes.cls.cpu().tolist()):
            pred.append({"bbox":[float(x) for x in box],"score":float(score),"class_id":int(cls),"class_name":str(names[int(cls)])})
    candidates=sorted(((iou(r["bbox"],p["bbox"]),ri,pi) for ri,r in enumerate(refs) for pi,p in enumerate(pred)),reverse=True)
    used_r=set();used_p=set();matches=[]
    for score,ri,pi in candidates:
        if score<=0 or ri in used_r or pi in used_p:continue
        used_r.add(ri);used_p.add(pi);matches.append({"reference_id":refs[ri]["id"],"prediction_index":pi,"iou":score})
    for threshold in (.25,.5,.75):
        pass
    image=cv2.imread(str(IMAGE));h,w=image.shape[:2];scale=.25;shape=(round(h*scale),round(w*scale))
    rm=np.zeros((shape[0],shape[1]),np.uint8);pm=np.zeros_like(rm)
    for row,mask in ((refs,rm),(pred,pm)):
        for item in row:
            x0,y0,x1,y1=[round(v*scale) for v in item["bbox"]];cv2.rectangle(mask,(x0,y0),(x1,y1),1,-1)
    overlap=int(np.count_nonzero((rm==1)&(pm==1)));ra=int(rm.sum());pa=int(pm.sum())
    thresholds={}
    for threshold in (.25,.5,.75):
        n=sum(m["iou"]>=threshold for m in matches);precision=n/len(pred) if pred else 0.;recall=n/len(refs) if refs else 1.
        thresholds[str(threshold)]={"matches":n,"precision":precision,"recall":recall,"f1":2*precision*recall/(precision+recall) if precision+recall else 0.}
    report={"schema":"bbvlm.doclayout-yolo-diagnostic/1","page":PAGE,"status":"posthoc_diagnostic_on_consumed_page_not_independent_validation",
      "model":{"repository":"juliozhao/DocLayout-YOLO-DocStructBench","revision":REV,"weights":WEIGHTS.name,
               "imgsz":1024,"confidence":.2,"device":"cpu"},"runtime_seconds":elapsed,"reference_regions":len(refs),
      "predictions":len(pred),"class_counts":dict(sorted(Counter(p["class_name"] for p in pred).items())),
      "greedy_one_to_one_iou":thresholds,"reference_union_coverage":overlap/ra if ra else 1.,
      "prediction_union_precision":overlap/pa if pa else 0.,"matches":matches,"reference":refs,"predicted":pred,
      "warning":"Distributed TextBlock rectangles are provisional and this consumed page cannot open an independent gate; this test only checks whether a generic region detector merits a frozen benchmark."}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    annotated=result.plot(pil=False,line_width=3,font_size=18);cv2.imwrite(str(OUT/"predictions.jpg"),annotated)
    print(json.dumps({k:report[k] for k in ("runtime_seconds","reference_regions","predictions","class_counts","greedy_one_to_one_iou","reference_union_coverage","prediction_union_precision")},indent=2))


if __name__=="__main__":main()
