"""Compare and freeze header-boundary grouping on development pages only."""
from collections import defaultdict
from pathlib import Path
import itertools
import json

from lxml import etree as E
from bbvlm.semantic import group_header_units

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/loop/spiritualist-v1/semantic-v2-header"
PAGES = ("0009", "0038", "0041", "0043")
NS = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}


def pairs(groups):
    return {tuple(sorted(pair)) for members in groups for pair in itertools.combinations(members, 2)}


def load(page):
    xml = next((ROOT / "corpora/spiritualist/alto_xml/ocr_gt_labelled").glob(f"{page}_*.xml"))
    tree = E.parse(str(xml)); node = tree.find(".//a:Page", NS)
    regions, roles, eligible, reference = [], {}, [], defaultdict(list)
    for block in tree.findall(".//a:TextBlock", NS):
        rid = block.get("ID"); x, y = float(block.get("HPOS")), float(block.get("VPOS"))
        w, h = float(block.get("WIDTH")), float(block.get("HEIGHT"))
        regions.append({"id": rid, "bbox": [x, y, x + w, y + h]})
        roles[rid] = block.get("BLOCK_TYPE")
        if int(block.get("READING_ORDER")) >= 0: eligible.append(rid)
        reference[block.get("SSU_ID")].append(rid)
    return regions, roles, eligible, list(reference.values()), [0, 0, float(node.get("WIDTH")), float(node.get("HEIGHT"))]


def main():
    order_config = json.loads((ROOT / "experiments/loop/spiritualist-v1/olr-v3-column/config.json").read_text())
    candidates = []
    for merge in (False, True):
        pages = []
        for page in PAGES:
            regions, roles, eligible, reference, page_bbox = load(page)
            result = group_header_units(regions, page_bbox, roles, eligible,
                gap_ratio=order_config["gap_ratio"], top_exclusion_ratio=order_config["top_exclusion_ratio"],
                max_anchor_width_ratio=order_config["max_anchor_width_ratio"], merge_overlapping_headers=merge)
            rp, pp = pairs(reference), pairs(g["region_ids"] for g in result["groups"])
            tp = len(rp & pp); precision = tp / len(pp) if pp else (1.0 if not rp else 0.0)
            recall = tp / len(rp) if rp else 1.0
            f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
            pages.append({"page": page, "reference_units": len(reference), "predicted_units": len(result["groups"]),
                          "pair_precision": precision, "pair_recall": recall, "pair_f1": f1,
                          "false_positive_pairs": len(pp-rp), "false_negative_pairs": len(rp-pp)})
        candidates.append({"merge_overlapping_headers": merge,
                           "macro_pair_f1": sum(p["pair_f1"] for p in pages) / len(pages), "pages": pages})
    # Frozen selection rule: highest macro F1; ties prefer the stricter rule.
    selected = max(candidates, key=lambda c: (c["macro_pair_f1"], not c["merge_overlapping_headers"]))
    config = {"schema": "bbvlm.header-unit-config/1", "selected_on": "development_only",
              "development_pages": list(PAGES), "merge_overlapping_headers": selected["merge_overlapping_headers"],
              "order_config": order_config,
              "selection_rule": "maximum macro pair F1; ties prefer not merging overlapping headers"}
    report = {"schema": "bbvlm.header-unit-calibration/1", "scope": "oracle regions, roles and eligibility",
              "candidates": candidates, "selected": config,
              "warning": "Development agreement learns this corpus convention only; validation must use predicted roles and an untouched page."}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    (OUT / "development-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
