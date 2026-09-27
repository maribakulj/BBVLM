"""Evaluate the frozen geometry-only order on one untouched validation page."""
from pathlib import Path
import json
import time

from lxml import etree as E
from bbvlm.order import infer_column_major_order

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/loop/spiritualist-v1/olr-v3-column"
PAGE = "0014"
NS = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}


def pair_accuracy(reference, predicted):
    pos = {rid: i for i, rid in enumerate(predicted)}
    pairs = [(a, b) for i, a in enumerate(reference) for b in reference[i + 1:]]
    correct = sum(pos[a] < pos[b] for a, b in pairs)
    return correct, len(pairs), correct / len(pairs) if pairs else 1.0


def main():
    config = json.loads((OUT / "config.json").read_text())
    xml = next((ROOT / "corpora/spiritualist/alto_xml/ocr_gt_labelled").glob(f"{PAGE}_*.xml"))
    tree = E.parse(str(xml)); page_node = tree.find(".//a:Page", NS)
    regions, known = [], []
    for block in tree.findall(".//a:TextBlock", NS):
        x, y = float(block.get("HPOS")), float(block.get("VPOS"))
        w, h = float(block.get("WIDTH")), float(block.get("HEIGHT"))
        rid = block.get("ID")
        regions.append({"id": rid, "bbox": [x, y, x + w, y + h]})
        order = int(block.get("READING_ORDER"))
        if order >= 0:
            known.append((order, rid))
    reference = [rid for _, rid in sorted(known)]
    start = time.perf_counter()
    result = infer_column_major_order(
        regions, [0, 0, float(page_node.get("WIDTH")), float(page_node.get("HEIGHT"))],
        gap_ratio=config["gap_ratio"], top_exclusion_ratio=config["top_exclusion_ratio"],
        max_anchor_width_ratio=config["max_anchor_width_ratio"])
    elapsed = time.perf_counter() - start
    correct, pairs, accuracy = pair_accuracy(reference, result["ordered_region_ids"])
    # Explicit generic baselines on exactly the same provided regions.
    row_major = [r["id"] for r in sorted(regions, key=lambda r: (r["bbox"][1], r["bbox"][0], r["id"]))]
    x_major = [r["id"] for r in sorted(regions, key=lambda r: (r["bbox"][0], r["bbox"][1], r["id"]))]
    _, _, row_accuracy = pair_accuracy(reference, row_major)
    _, _, x_accuracy = pair_accuracy(reference, x_major)
    report = {
        "schema": "bbvlm.column-order-evaluation/1", "page": PAGE,
        "split_role": "frozen_validation_consumed_after_this_evaluation",
        "scope": "oracle/reference TextBlock regions; no region detection claim",
        "passes": {"vlm": 0, "geometry_cpu": 1}, "runtime_seconds": elapsed,
        "regions": len(regions), "known_order_regions": len(reference),
        "reference_excluded_regions_still_in_raw_proposal": len(regions) - len(reference),
        "inferred_columns": len(result["column_anchors_x"]),
        "reading_order_correct_pairs": correct, "reading_order_pairs": pairs,
        "reading_order_pair_accuracy": accuracy,
        "baselines": {"row_major_pair_accuracy": row_accuracy, "global_x_then_y_pair_accuracy": x_accuracy},
        "frozen_parameters": result["parameters"],
        "gate": {"threshold": 0.95, "passed": accuracy >= 0.95},
        "accepted_for_project_completion_gate": False,
        "promotion_warning": "The raw proposal orders every supplied region. A separately validated role/eligibility filter is required before graph promotion.",
        "reference_warning": "Agreement with provisional distributed order labels on one page; not independently adjudicated and not end-to-end.",
    }
    (OUT / "validation-0014-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
