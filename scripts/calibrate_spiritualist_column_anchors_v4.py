"""Calibrate a minimum anchor width on development pages only."""
from pathlib import Path
from statistics import median
import json
from lxml import etree as E
from bbvlm.order import infer_column_major_order

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"experiments/loop/spiritualist-v1/olr-v4-column-anchors"
PAGES=("0009","0038","0041","0043");MINS=(0.0,0.01,0.02,0.04,0.06,0.08,0.10,0.12)
FIXED={"gap_ratio":0.14,"top_exclusion_ratio":0.055,"max_anchor_width_ratio":0.55,"assign_by_overlap":True}
NS={"a":"http://www.loc.gov/standards/alto/ns-v4#"}

def load(page):
    tree=E.parse(str(next((ROOT/"corpora/spiritualist/alto_xml/ocr_gt_labelled").glob(f"{page}_*.xml"))));node=tree.find(".//a:Page",NS)
    regions=[];reference=[];columns={}
    for b in tree.findall(".//a:TextBlock",NS):
        x,y,w,h=map(float,(b.get("HPOS"),b.get("VPOS"),b.get("WIDTH"),b.get("HEIGHT")));rid=b.get("ID")
        regions.append({"id":rid,"bbox":[x,y,x+w,y+h]});order=int(b.get("READING_ORDER"))
        if order>=0:columns.setdefault(b.get("COLUMN_ID"),[]).append(x)
        if order>=0:reference.append((order,rid))
    bbox=[0,0,float(node.get("WIDTH")),float(node.get("HEIGHT"))]
    anchors=sorted(median(xs) for xs in columns.values());perturbed=list(regions)
    # Stress width (1.6% of page) is fixed from the consumed A08 failure class;
    # selection and all accuracy measurements remain development-only.
    for i,(a,b) in enumerate(zip(anchors,anchors[1:])):
        x=(a+b)/2;perturbed.append({"id":f"SYNTHETIC_NARROW_BRIDGE_{i}","bbox":[x,bbox[3]*.1,x+bbox[2]*.016,bbox[3]*.12]})
    return regions,perturbed,[rid for _,rid in sorted(reference)],bbox

def score(reference,predicted):
    pos={rid:i for i,rid in enumerate(predicted)};pairs=[(a,b) for i,a in enumerate(reference) for b in reference[i+1:]]
    return sum(pos[a]<pos[b] for a,b in pairs)/len(pairs) if pairs else 1.

def main():
    candidates=[]
    for minimum in MINS:
        pages=[]
        for page in PAGES:
            regions,perturbed,reference,bbox=load(page)
            result=infer_column_major_order(regions,bbox,min_anchor_width_ratio=minimum,**FIXED)
            robust=infer_column_major_order(perturbed,bbox,min_anchor_width_ratio=minimum,**FIXED)
            pages.append({"page":page,"pair_accuracy":score(reference,result["ordered_region_ids"]),
                          "narrow_bridge_pair_accuracy":score(reference,robust["ordered_region_ids"]),"columns":len(result["column_anchors_x"])})
        candidates.append({"min_anchor_width_ratio":minimum,"macro_pair_accuracy":sum(p["pair_accuracy"] for p in pages)/len(pages),
                           "macro_narrow_bridge_pair_accuracy":sum(p["narrow_bridge_pair_accuracy"] for p in pages)/len(pages),
                           "total_columns":sum(p["columns"] for p in pages),"pages":pages})
    best=max(candidates,key=lambda c:(c["macro_pair_accuracy"],c["macro_narrow_bridge_pair_accuracy"],-c["min_anchor_width_ratio"],-c["total_columns"]))
    config={"schema":"bbvlm.column-anchor-config/1","selected_on":"development_only","development_pages":list(PAGES),
            **FIXED,"min_anchor_width_ratio":best["min_anchor_width_ratio"],
            "selection_rule":"maximum original macro pair accuracy; then synthetic narrow-bridge robustness; then smaller minimum width; then fewer columns"}
    report={"schema":"bbvlm.column-anchor-calibration/1","scope":"oracle/reference TextBlock regions; 0044 excluded from selection",
            "selected":best,"config":config,"candidates":candidates,"warning":"0044 is consumed and may only be reported as a posthoc diagnostic; validation must use 0050."}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/"config.json").write_text(json.dumps(config,indent=2)+"\n");(OUT/"development-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"selected":best,"config":config},indent=2))

if __name__=="__main__":main()
