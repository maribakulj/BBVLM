"""One-shot conditional validation of the frozen v6 typography rule on 0004."""
import itertools, json
from lxml import etree as E

from calibrate_spiritualist_typography_v6 import BASE, ROOT, NS, load, pair_set
from bbvlm.semantic import group_header_units, refine_stream_roles_by_typography


def pair_accuracy(reference_order, predicted_order):
    rpos={rid:i for i,rid in enumerate(reference_order)}; ppos={rid:i for i,rid in enumerate(predicted_order)}
    pairs=list(itertools.combinations(reference_order,2))
    return sum((rpos[a]<rpos[b])==(ppos[a]<ppos[b]) for a,b in pairs)/len(pairs) if pairs else 1.


def main():
    page="0004"; profile=json.loads((BASE/"profile.json").read_text()); config=profile["classifier"]
    regions,reference_roles,eligible,reference,page_bbox,typography,_=load(page)
    coarse={rid:("STREAM" if role in {"HEADER","TEXT"} else role) for rid,role in reference_roles.items()}
    predicted=refine_stream_roles_by_typography(regions,coarse,typography,**config)
    grouped=group_header_units(regions,page_bbox,predicted,eligible,**profile["order_config"],merge_overlapping_headers=True)
    stream=[rid for rid in eligible if reference_roles[rid] in {"HEADER","TEXT"}]
    role_accuracy=sum(predicted[rid]==reference_roles[rid] for rid in stream)/len(stream) if stream else 1.
    rp=pair_set(reference); pp=pair_set(g["region_ids"] for g in grouped["groups"]); tp=len(rp&pp)
    precision=tp/len(pp) if pp else 0.; recall=tp/len(rp) if rp else 1.
    f1=2*precision*recall/(precision+recall) if precision+recall else 0.
    tree=E.parse(str(next((ROOT/"corpora/spiritualist/alto_xml/ocr_gt_labelled").glob(f"{page}_*.xml"))))
    reference_order=[b.get("ID") for b in sorted(
        (b for b in tree.findall(".//a:TextBlock",NS) if int(b.get("READING_ORDER"))>=0),
        key=lambda b:int(b.get("READING_ORDER")))]
    reference_set=set(reference_order)
    predicted_order=[rid for rid in grouped["order"]["ordered_region_ids"] if rid in reference_set]
    order_accuracy=pair_accuracy(reference_order,predicted_order)
    passed=role_accuracy>=.8 and f1>=.8 and order_accuracy>=.95
    mismatches=[{"region_id":rid,"reference":reference_roles[rid],"predicted":predicted[rid],
                 "typography":typography[rid]} for rid in stream if predicted[rid]!=reference_roles[rid]]
    report={"schema":"bbvlm.semantic-v6-typography-validation/1","page":page,
        "scope":"conditional on distributed regions and oracle coarse STREAM membership",
        "protocol_frozen_before_labels":"profile.json selected on development only",
        "passes":{"vlm":0,"cpu_typography_order_grouping":1},
        "metrics":{"fine_role_accuracy":role_accuracy,"semantic_group_pair_precision":precision,
                   "semantic_group_pair_recall":recall,"semantic_group_pair_f1":f1,
                   "order_pair_accuracy":order_accuracy},
        "counts":{"stream_regions":len(stream),"role_mismatches":len(mismatches),
                  "predicted_units":len(grouped["groups"]),"reference_units":len(reference)},
        "gates":{"fine_role_accuracy_min":.8,"semantic_group_pair_f1_min":.8,"order_pair_accuracy_min":.95},
        "content_gate_passed":passed,"mismatches":mismatches,"accepted_for_project_completion_gate":False,
        "warning":"Page 0004 is consumed for this conditional task; labels are provisional and word boxes remain rejected."}
    (BASE/"validation-0004-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__": main()
