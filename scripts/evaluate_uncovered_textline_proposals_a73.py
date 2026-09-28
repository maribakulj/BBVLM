"""Convert sealed A72 line masks into image-only proposals, then score consumed GT."""
import hashlib
import json
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from evaluate_crop_geometry_a65 import polygon

OUT = ROOT / "experiments/loop/next-a73"
A72 = ROOT / "experiments/loop/next-a72"
PAGES = ["Reichs_Post_Reuter_1700-11-16_0001", "Koelnische_Zeitung_1924_0001"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_lines(page, expected):
    path = ROOT / "corpora/chronicling-germany/annotations" / f"{page}.xml"
    assert sha(path) == expected[path.name]
    root = ET.fromstring(path.read_bytes())
    ns = {"p": root.tag.split("}")[0][1:]}
    lines = []
    for region in root.find("p:Page", ns).findall("p:TextRegion", ns):
        for element in region.findall("p:TextLine", ns):
            geom = polygon(element, ns)
            if geom is not None:
                lines.append((element.get("id"), geom))
    return lines, sha(path)


def main():
    started = time.perf_counter()
    a72 = json.loads((A72 / "report.json").read_text())
    a70 = json.loads((ROOT / "experiments/loop/next-a70/report-v2.json").read_text())
    zero = {(row["page"], row["line_id"]) for row in a70["rows"] if not row["contributors"]}
    candidates = json.loads((ROOT / "experiments/loop/next-a69/candidates.json").read_text())["pages"]
    proposed = {"schema": "bbvlm.a73.image-only-proposals/1", "rule": {
        "connectivity": 8, "minimum_component_pixels": 4,
        "minimum_fraction_outside_native_yolo_union": 0.5,
        "proposal": "full_component_bounding_rectangle",
    }, "pages": {}}
    for page in PAGES:
        audit = a72["image_audit"][page]
        mask_path = A72 / f"{page}-textline-mask.png"
        assert sha(mask_path) == audit["mask_sha256"]
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE) > 0
        source_h, source_w = candidates[page]["shape"]
        scale_x, scale_y = mask.shape[1] / source_w, mask.shape[0] / source_h
        covered = np.zeros(mask.shape, dtype=np.uint8)
        for record in candidates[page]["native"]:
            x0, y0, x1, y1 = record["bbox"]
            cv2.rectangle(covered, (int(np.floor(x0 * scale_x)), int(np.floor(y0 * scale_y))),
                          (int(np.ceil(x1 * scale_x)), int(np.ceil(y1 * scale_y))), 1, -1)
        count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
        rows = []
        for component in range(1, count):
            area = int(stats[component, cv2.CC_STAT_AREA])
            if area < 4:
                continue
            selected = labels == component
            outside = int(np.logical_and(selected, covered == 0).sum())
            outside_fraction = outside / area
            if outside_fraction < 0.5:
                continue
            x, y, width, height = map(int, stats[component, :4])
            rows.append({
                "component": component, "mask_pixels": area,
                "outside_yolo_pixels": outside, "outside_yolo_fraction": outside_fraction,
                "bbox_mask": [x, y, x + width, y + height],
                "bbox_native": [x / scale_x, y / scale_y,
                                (x + width) / scale_x, (y + height) / scale_y],
            })
        proposed["pages"][page] = {
            "mask_sha256": sha(mask_path), "native_candidate_count": len(candidates[page]["native"]),
            "source_shape": [source_h, source_w], "mask_shape": list(mask.shape),
            "proposals": rows,
        }
    OUT.mkdir(parents=True, exist_ok=True)
    candidate_path = OUT / "candidates.json"
    candidate_path.write_text(json.dumps(proposed, indent=2) + "\n")
    candidate_hash = sha(candidate_path)

    expected = {row["file"]: row["sha256"] for row in json.loads(
        (ROOT / "experiments/loop/chronicling-a58/audit.json").read_text())["files_detail"]}
    page_reports, all_targets, recovered = {}, 0, 0
    all_proposals, false_proposals = 0, 0
    union_area, inside_area = 0.0, 0.0
    for page in PAGES:
        lines, xml_hash = parse_lines(page, expected)
        line_union = unary_union([geom for _, geom in lines])
        proposals = [box(*row["bbox_native"]) for row in proposed["pages"][page]["proposals"]]
        proposal_union = unary_union(proposals) if proposals else box(0, 0, 0, 0)
        page_union_area = proposal_union.area
        page_inside_area = proposal_union.intersection(line_union).area
        zero_rows = []
        for line_id, geom in lines:
            if (page, line_id) not in zero:
                continue
            coverage = geom.intersection(proposal_union).area / geom.area
            zero_rows.append({"line_id": line_id, "union_proposal_coverage": coverage,
                              "recovered_ge50pct": coverage >= 0.5})
        proposal_rows = []
        for record, geom in zip(proposed["pages"][page]["proposals"], proposals):
            inside = geom.intersection(line_union).area / geom.area if geom.area else 0.0
            proposal_rows.append({"component": record["component"],
                                  "box_inside_line_union_fraction": inside,
                                  "false_lt1pct": inside < 0.01})
        page_recovered = sum(row["recovered_ge50pct"] for row in zero_rows)
        page_false = sum(row["false_lt1pct"] for row in proposal_rows)
        all_targets += len(zero_rows); recovered += page_recovered
        all_proposals += len(proposal_rows); false_proposals += page_false
        union_area += page_union_area; inside_area += page_inside_area
        page_reports[page] = {
            "xml_sha256": xml_hash, "proposals": len(proposal_rows),
            "proposal_union_area": page_union_area,
            "proposal_union_inside_line_fraction": page_inside_area / page_union_area if page_union_area else 0.0,
            "zero_contributor_lines": len(zero_rows), "zero_recovered_ge50pct": page_recovered,
            "false_proposals_lt1pct": page_false, "zero_rows": zero_rows,
            "proposal_rows": proposal_rows,
        }
    recovery = recovered / all_targets if all_targets else 0.0
    precision_like = inside_area / union_area if union_area else 0.0
    checks = {
        "zero_recovery_ge80pct": recovery >= 0.8,
        "proposal_union_inside_lines_ge75pct": precision_like >= 0.75,
        "zero_false_proposals_lt1pct": false_proposals == 0,
    }
    report = {
        "status": "consumed_image_only_proposal_diagnostic",
        "candidate_sha256_before_xml": candidate_hash,
        "pages": page_reports, "proposals": all_proposals,
        "zero_contributor_lines": all_targets, "zero_recovered_ge50pct": recovered,
        "zero_recovery_ratio": recovery, "false_proposals_lt1pct": false_proposals,
        "proposal_union_inside_line_fraction": precision_like,
        "gate_checks": checks, "local_gate_passed": all(checks.values()),
        "new_model_forwards": 0, "ocr_calls": 0, "vlm_calls": 0,
        "test_pages_opened": 0, "seconds": time.perf_counter() - started,
        "all_scientific_gates_passed": False,
        "limitations": ["A72 pages and A70-selected residuals are consumed.",
                        "PAGE line polygons are an imperfect oracle.",
                        "Bounding mask components is not ALTO word or article ownership."],
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    keys = ("proposals", "zero_contributor_lines", "zero_recovered_ge50pct",
            "zero_recovery_ratio", "false_proposals_lt1pct",
            "proposal_union_inside_line_fraction", "gate_checks", "local_gate_passed", "seconds")
    print(json.dumps({key: report[key] for key in keys}, indent=2))


if __name__ == "__main__":
    main()
