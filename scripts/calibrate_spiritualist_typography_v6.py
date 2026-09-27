"""Select an internal-typography HEADER rule on frozen v6 development pages."""
from collections import defaultdict
from pathlib import Path
import itertools, json, statistics

from lxml import etree as E
from bbvlm.semantic import group_header_units, refine_stream_roles_by_typography

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/loop/spiritualist-v1/semantic-v6-typography"
NS={"a":"http://www.loc.gov/standards/alto/ns-v4#"}


def pair_set(groups):
    return {tuple(sorted(p)) for g in groups for p in itertools.combinations(g,2)}


def load(page):
    path=next((ROOT/"corpora/spiritualist/alto_xml/ocr_gt_labelled").glob(f"{page}_*.xml"))
    tree=E.parse(str(path)); node=tree.find(".//a:Page",NS)
    page_bbox=[0,0,float(node.get("WIDTH")),float(node.get("HEIGHT"))]
    regions=[]; roles={}; eligible=[]; reference=defaultdict(list); typography={}; orders={}
    for block in tree.findall(".//a:TextBlock",NS):
        rid=block.get("ID"); x,y,w,h=map(float,(block.get("HPOS"),block.get("VPOS"),block.get("WIDTH"),block.get("HEIGHT")))
        regions.append({"id":rid,"bbox":[x,y,x+w,y+h]}); roles[rid]=block.get("BLOCK_TYPE")
        order=int(block.get("READING_ORDER")); orders[rid]=order
        if order>=0: eligible.append(rid)
        reference[block.get("SSU_ID")].append(rid)
        lines=block.findall("./a:TextLine",NS)
        heights=[float(line.get("HEIGHT")) for line in lines]
        text=" ".join(s.get("CONTENT","") for line in lines for s in line.findall("./a:String",NS))
        alpha=sum(c.isalpha() for c in text); upper=sum(c.isupper() for c in text)
        typography[rid]={"line_count":len(lines),
            "median_line_height_page_ratio":statistics.median(heights)/page_bbox[3] if heights else 0.0,
            "uppercase_ratio":upper/alpha if alpha else 0.0}
    return regions,roles,eligible,list(reference.values()),page_bbox,typography,orders


def score_page(page, config):
    regions,reference_roles,eligible,reference,page_bbox,typography,_=load(page)
    coarse={rid:("STREAM" if role in {"HEADER","TEXT"} else role) for rid,role in reference_roles.items()}
    predicted=refine_stream_roles_by_typography(regions,coarse,typography,**config)
    grouped=group_header_units(regions,page_bbox,predicted,eligible,gap_ratio=.14,top_exclusion_ratio=.055,
        max_anchor_width_ratio=.55,min_anchor_width_ratio=.02,assign_by_overlap=True,
        merge_overlapping_headers=True)
    rp=pair_set(reference); pp=pair_set(g["region_ids"] for g in grouped["groups"])
    tp=len(rp&pp); precision=tp/len(pp) if pp else 0.; recall=tp/len(rp) if rp else 1.
    f1=2*precision*recall/(precision+recall) if precision+recall else 0.
    stream=[rid for rid in eligible if reference_roles[rid] in {"HEADER","TEXT"}]
    accuracy=sum(predicted[rid]==reference_roles[rid] for rid in stream)/len(stream) if stream else 1.
    return {"page":page,"pair_f1":f1,"stream_role_accuracy":accuracy,
            "predicted_units":len(grouped["groups"]),"reference_units":len(reference)}


def main():
    split=json.loads((BASE/"split.json").read_text()); pages=split["development_pages"]
    candidates=[]
    for max_lines in (1,2,3):
        for min_height in (.008,.009,.010,.011,.012,.013,.014,.015,.016,1.0):
            for min_upper in (.5,.6,.7,.8,.9,1.01):
                config={"max_header_line_count":max_lines,
                        "min_median_line_height_page_ratio":min_height,
                        "min_uppercase_ratio":min_upper}
                scored=[score_page(page,config) for page in pages]
                candidates.append({**config,
                    "macro_pair_f1":sum(x["pair_f1"] for x in scored)/len(scored),
                    "macro_stream_role_accuracy":sum(x["stream_role_accuracy"] for x in scored)/len(scored),
                    "pages":scored})
    selected=max(candidates,key=lambda c:(c["macro_pair_f1"],c["macro_stream_role_accuracy"],
        -c["max_header_line_count"],c["min_median_line_height_page_ratio"],c["min_uppercase_ratio"]))
    config={k:selected[k] for k in ("max_header_line_count","min_median_line_height_page_ratio","min_uppercase_ratio")}
    profile={"schema":"bbvlm.semantic-v6-typography-profile/1","selected_on":"frozen v6 development pages only",
        "development_pages":pages,"classifier":config,
        "decision":"HEADER iff STREAM, line_count <= max, and median line height OR uppercase ratio reaches threshold",
        "text_policy":"OCR text is read only for uppercase ratio; diplomatic text is never changed",
        "coarse_scope":"oracle STREAM membership during calibration; no VLM claim",
        "order_config":{"gap_ratio":.14,"top_exclusion_ratio":.055,"max_anchor_width_ratio":.55,
                        "min_anchor_width_ratio":.02,"assign_by_overlap":True},
        "validation_page":"0004","validation_labels_not_read_during_selection":True,
        "warning":"Distributed roles and SSU are provisional and cannot validate word geometry."}
    report={"schema":"bbvlm.semantic-v6-typography-calibration/1","selected":selected,
            "profile":profile,"candidate_count":len(candidates),"candidates":candidates}
    (BASE/"profile.json").write_text(json.dumps(profile,indent=2)+"\n")
    (BASE/"development-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"selected":selected,"candidate_count":len(candidates)},indent=2))


if __name__=="__main__": main()
