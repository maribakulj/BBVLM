"""Post-hoc, explicitly oracle contamination audit for the consumed A72 masks."""
import hashlib
import json
import statistics
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from evaluate_crop_geometry_a65 import polygon


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    directory = ROOT / "experiments/loop/next-a72"
    report_path = directory / "report.json"
    report = json.loads(report_path.read_text())
    pages = []
    for page, audit in report["image_audit"].items():
        mask_path = directory / f"{page}-textline-mask.png"
        assert sha(mask_path) == audit["mask_sha256"]
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE) > 0
        xml_path = ROOT / "corpora/chronicling-germany/annotations" / f"{page}.xml"
        root = ET.fromstring(xml_path.read_bytes())
        ns = {"p": root.tag.split("}")[0][1:]}
        source_h, source_w = audit["shape"]
        target_h, target_w = audit["resized_shape"]
        scale = np.array([target_w / source_w, target_h / source_h])
        union = np.zeros(mask.shape, dtype=np.uint8)
        for region in root.find("p:Page", ns).findall("p:TextRegion", ns):
            for element in region.findall("p:TextLine", ns):
                geom = polygon(element, ns)
                if geom is not None:
                    points = np.rint(np.asarray(geom.exterior.coords) * scale).astype(np.int32)
                    cv2.fillPoly(union, [points], 1)
        positive = int(mask.sum())
        reference = int(union.sum())
        intersection = int(np.logical_and(mask, union > 0).sum())
        residual = [row["coverage"] for row in report["rows"]
                    if row["page"] == page and row["a70_zero_contributor"]]
        pages.append({
            "page": page,
            "mask_positive_pixels": positive,
            "reference_union_pixels": reference,
            "intersection_pixels": intersection,
            "mask_inside_reference_fraction": intersection / positive,
            "reference_covered_fraction": intersection / reference,
            "mask_outside_reference_fraction": (positive - intersection) / positive,
            "zero_contributor_count": len(residual),
            "zero_contributor_min_coverage": min(residual),
            "zero_contributor_median_coverage": statistics.median(residual),
            "zero_contributor_ge50pct": sum(value >= 0.5 for value in residual),
            "zero_contributor_ge80pct": sum(value >= 0.8 for value in residual),
            "xml_sha256": sha(xml_path),
        })
    output = {
        "status": "posthoc_consumed_oracle_contamination_audit",
        "input_report_sha256": sha(report_path),
        "pages": pages,
        "interpretation": "High line recall with bounded but non-zero mask spill; not box precision.",
        "limitations": [
            "This post-hoc audit uses the consumed PAGE polygons and cannot validate generalization.",
            "Polygon union precision is not object detection precision or ALTO box accuracy.",
        ],
        "all_scientific_gates_passed": False,
    }
    (directory / "contamination.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
