"""Evaluate A11 with frozen A10 typography instead of whole-block height."""
import json, statistics
from lxml import etree as E

import evaluate_spiritualist_coarse_v4 as base
from bbvlm.semantic import refine_stream_roles_by_typography

BASE=base.ROOT/"experiments/loop/spiritualist-v1/semantic-v6-full-validation"
PROFILE=base.ROOT/"experiments/loop/spiritualist-v1/semantic-v6-typography/full-validation-profile.json"
NS={"a":"http://www.loc.gov/standards/alto/ns-v4#"}


def typography():
    page="0010"; path=next((base.ROOT/"corpora/spiritualist/alto_xml/ocr_gt_labelled").glob(f"{page}_*.xml"))
    tree=E.parse(str(path)); node=tree.find(".//a:Page",NS); page_height=float(node.get("HEIGHT")); result={}
    for block in tree.findall(".//a:TextBlock",NS):
        rid="R"+__import__('hashlib').sha256(f"spiritualist|{page}|{block.get('ID')}".encode()).hexdigest()[:16]
        lines=block.findall("./a:TextLine",NS); heights=[float(line.get("HEIGHT")) for line in lines]
        text=" ".join(s.get("CONTENT","") for line in lines for s in line.findall("./a:String",NS))
        alpha=sum(c.isalpha() for c in text); upper=sum(c.isupper() for c in text)
        result[rid]={"line_count":len(lines),"median_line_height_page_ratio":statistics.median(heights)/page_height if heights else 0.,
                     "uppercase_ratio":upper/alpha if alpha else 0.}
    return result


def frozen_typography(regions, page_bbox, coarse_roles, *, max_header_height_page_ratio):
    del page_bbox,max_header_height_page_ratio
    cfg=json.loads(PROFILE.read_text())["typography_config"]
    params={k:cfg[k] for k in ("max_header_line_count","min_median_line_height_page_ratio","min_uppercase_ratio")}
    return refine_stream_roles_by_typography(regions,coarse_roles,typography(),**params)


def main():
    base.BASE=BASE; base.refine_stream_roles_by_height=frozen_typography; base.main()
    path=BASE/"report.json"; report=json.loads(path.read_text())
    report["schema"]="bbvlm.coarse-role-plus-frozen-typography-evaluation/1"
    report["fine_role_method"]="A10 internal line count, median line height and uppercase ratio; frozen before 0010"
    report["reference_warning"]="Page 0010 is consumed after this one fixed evaluation; labels are provisional and word boxes remain rejected."
    path.write_text(json.dumps(report,indent=2)+"\n")


if __name__=="__main__": main()
