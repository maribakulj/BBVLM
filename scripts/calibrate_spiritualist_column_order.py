"""Select one geometry-only column-order threshold on development pages."""
from pathlib import Path
import json

from lxml import etree as E
from bbvlm.order import infer_column_major_order

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/loop/spiritualist-v1/olr-v3-column"
PAGES = ("0009", "0038", "0041", "0043")
GAPS = (0.08, 0.10, 0.12, 0.14, 0.16, 0.18)
FIXED = {"top_exclusion_ratio": 0.055, "max_anchor_width_ratio": 0.55}
NS = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}


def load(page):
    xml = next((ROOT / "corpora/spiritualist/alto_xml/ocr_gt_labelled").glob(f"{page}_*.xml"))
    tree = E.parse(str(xml)); node = tree.find(".//a:Page", NS)
    regions, reference = [], []
    for block in tree.findall(".//a:TextBlock", NS):
        x, y = float(block.get("HPOS")), float(block.get("VPOS"))
        w, h = float(block.get("WIDTH")), float(block.get("HEIGHT"))
        rid = block.get("ID")
        regions.append({"id": rid, "bbox": [x, y, x + w, y + h]})
        order = int(block.get("READING_ORDER"))
        if order >= 0:
            reference.append((order, rid))
    return regions, [rid for _, rid in sorted(reference)], [0, 0, float(node.get("WIDTH")), float(node.get("HEIGHT"))]


def pair_accuracy(reference, predicted):
    pos = {rid: i for i, rid in enumerate(predicted)}
    pairs = [(a, b) for i, a in enumerate(reference) for b in reference[i + 1:]]
    return sum(pos[a] < pos[b] for a, b in pairs) / len(pairs) if pairs else 1.0, len(pairs)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    candidates = []
    for gap in GAPS:
        pages, total_columns = [], 0
        for page in PAGES:
            regions, reference, page_bbox = load(page)
            result = infer_column_major_order(regions, page_bbox, gap_ratio=gap, **FIXED)
            score, pairs = pair_accuracy(reference, result["ordered_region_ids"])
            total_columns += len(result["column_anchors_x"])
            pages.append({"page": page, "known_regions": len(reference), "pairs": pairs,
                          "pair_accuracy": score, "inferred_columns": len(result["column_anchors_x"])})
        candidates.append({"gap_ratio": gap, "macro_pair_accuracy": sum(p["pair_accuracy"] for p in pages) / len(pages),
                           "total_inferred_columns": total_columns, "pages": pages})
    # Predeclared selection: best macro accuracy, then simplest total column count,
    # then the smaller gap (less risk of merging true adjacent columns).
    best = max(candidates, key=lambda c: (c["macro_pair_accuracy"], -c["total_inferred_columns"], -c["gap_ratio"]))
    config = {"schema": "bbvlm.column-order-config/1", "selected_on": "development_only",
              "development_pages": list(PAGES), "gap_ratio": best["gap_ratio"], **FIXED,
              "selection_rule": "max macro pair accuracy; then minimum total inferred columns; then smaller gap"}
    report = {"schema": "bbvlm.column-order-calibration/1", "scope": "oracle/reference TextBlock regions",
              "candidates": candidates, "selected": config,
              "warning": "Perfect development agreement only identifies this corpus convention; it is not evidence for complex non-columnar reading order."}
    (OUT / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    (OUT / "development-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
