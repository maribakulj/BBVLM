"""Calibrate a HEADER/TEXT height split on development pages only."""
from collections import defaultdict
from pathlib import Path
import itertools,json

from lxml import etree as E
from bbvlm.semantic import group_header_units

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"experiments/loop/spiritualist-v1/semantic-v4-coarse"
PAGES=("0009","0038","0041","0043");NS={"a":"http://www.loc.gov/standards/alto/ns-v4#"}


def pairs(groups):return {tuple(sorted(p)) for g in groups for p in itertools.combinations(g,2)}


def load(page):
    tree=E.parse(str(next((ROOT/"corpora/spiritualist/alto_xml/ocr_gt_labelled").glob(f"{page}_*.xml"))));node=tree.find(".//a:Page",NS)
    regions=[];roles={};eligible=[];reference=defaultdict(list)
    for b in tree.findall(".//a:TextBlock",NS):
        rid=b.get("ID");x,y,w,h=map(float,(b.get("HPOS"),b.get("VPOS"),b.get("WIDTH"),b.get("HEIGHT")))
        regions.append({"id":rid,"bbox":[x,y,x+w,y+h]});roles[rid]=b.get("BLOCK_TYPE")
        if int(b.get("READING_ORDER"))>=0:eligible.append(rid)
        reference[b.get("SSU_ID")].append(rid)
    return regions,roles,eligible,list(reference.values()),[0,0,float(node.get("WIDTH")),float(node.get("HEIGHT"))]


def main():
    hc=json.loads((ROOT/"experiments/loop/spiritualist-v1/semantic-v2-header/config.json").read_text());oc=hc["order_config"]
    candidates=[]
    for ratio in [i/1000 for i in range(8,61,2)]:
        pages=[]
        for page in PAGES:
            regions,reference_roles,eligible,reference,page_bbox=load(page);pred={}
            for r in regions:
                role=reference_roles[r["id"]]
                pred[r["id"]]="HEADER" if role in {"HEADER","TEXT"} and (r["bbox"][3]-r["bbox"][1])/page_bbox[3]<=ratio else ("TEXT" if role in {"HEADER","TEXT"} else role)
            result=group_header_units(regions,page_bbox,pred,eligible,gap_ratio=oc["gap_ratio"],top_exclusion_ratio=oc["top_exclusion_ratio"],
              max_anchor_width_ratio=oc["max_anchor_width_ratio"],merge_overlapping_headers=hc["merge_overlapping_headers"])
            rp,pp=pairs(reference),pairs(g["region_ids"] for g in result["groups"]);tp=len(rp&pp);p=tp/len(pp) if pp else 0.;r=tp/len(rp) if rp else 1.;f=2*p*r/(p+r) if p+r else 0.
            stream=[rid for rid in eligible if reference_roles[rid] in {"HEADER","TEXT"}];acc=sum(pred[rid]==reference_roles[rid] for rid in stream)/len(stream)
            pages.append({"page":page,"pair_f1":f,"stream_role_accuracy":acc,"predicted_units":len(result["groups"]),"reference_units":len(reference)})
        candidates.append({"max_header_height_page_ratio":ratio,"macro_pair_f1":sum(x["pair_f1"] for x in pages)/len(pages),
          "macro_stream_role_accuracy":sum(x["stream_role_accuracy"] for x in pages)/len(pages),"pages":pages})
    selected=max(candidates,key=lambda c:(c["macro_pair_f1"],c["macro_stream_role_accuracy"],-c["max_header_height_page_ratio"]))
    config={"schema":"bbvlm.header-geometry-config/1","selected_on":"development_only","development_pages":list(PAGES),
      "max_header_height_page_ratio":selected["max_header_height_page_ratio"],"coarse_role_contract":"VLM supplies STREAM versus MASTHEAD/OTHER/UNKNOWN; CPU splits STREAM into HEADER/TEXT",
      "selection_rule":"maximum macro SSU pair F1, then macro HEADER/TEXT accuracy, then smaller threshold"}
    report={"schema":"bbvlm.header-geometry-calibration/1","scope":"development-only oracle coarse stream membership and regions",
      "selected":selected,"config":config,"candidates":candidates,"warning":"Do not score consumed page 0039 as independent validation; next validation must use 0044 or 0050."}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/"config.json").write_text(json.dumps(config,indent=2)+"\n");(OUT/"development-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"selected":selected,"config":config},indent=2))


if __name__=="__main__":main()
