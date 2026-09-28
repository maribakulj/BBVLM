"""Extract full-mask connected line instances, seal them, then score A74."""
import hashlib
import json
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from evaluate_crop_geometry_a65 import polygon

OUT = ROOT / "experiments/loop/next-a75"
A74 = ROOT / "experiments/loop/next-a74"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def box_iou(left, right):
    if not len(left) or not len(right):
        return np.zeros((len(left), len(right)), dtype=np.float32)
    a, b = left[:, None, :], right[None, :, :]
    x0 = np.maximum(a[:, :, 0], b[:, :, 0])
    y0 = np.maximum(a[:, :, 1], b[:, :, 1])
    x1 = np.minimum(a[:, :, 2], b[:, :, 2])
    y1 = np.minimum(a[:, :, 3], b[:, :, 3])
    inter = np.maximum(0, x1 - x0) * np.maximum(0, y1 - y0)
    area_a = (a[:, :, 2] - a[:, :, 0]) * (a[:, :, 3] - a[:, :, 1])
    area_b = (b[:, :, 2] - b[:, :, 0]) * (b[:, :, 3] - b[:, :, 1])
    return inter / np.maximum(area_a + area_b - inter, 1e-9)


def parse_reference(name, expected):
    path = ROOT / "corpora/chronicling-germany/annotations" / f"{name}.xml"
    assert sha(path) == expected[path.name]
    root = ET.fromstring(path.read_bytes())
    ns = {"p": root.tag.split("}")[0][1:]}
    rows = []
    for region in root.find("p:Page", ns).findall("p:TextRegion", ns):
        for element in region.findall("p:TextLine", ns):
            geom = polygon(element, ns)
            if geom is not None:
                rows.append({"line_id": element.get("id"), "bbox": list(geom.bounds)})
    return rows, sha(path)


def summarize(iou, row_idx, col_idx, n_candidates, n_reference):
    matched = iou[row_idx, col_idx] if len(row_idx) else np.asarray([])
    result = {"candidates": n_candidates, "reference_lines": n_reference,
              "matched_pairs": len(matched),
              "mean_assigned_iou": float(matched.mean()) if len(matched) else 0.0}
    for threshold, label in ((0.5, "iou50"), (0.7, "iou70")):
        true = int((matched >= threshold).sum())
        precision = true / n_candidates if n_candidates else 0.0
        recall = true / n_reference if n_reference else 0.0
        result[label] = {"true_matches": true, "precision": precision,
                         "recall": recall,
                         "f1": 2 * precision * recall / (precision + recall)
                               if precision + recall else 0.0}
    result["candidate_merges_iou_gt10"] = int(((iou > 0.1).sum(axis=1) > 1).sum())
    result["reference_fragments_iou_gt10"] = int(((iou > 0.1).sum(axis=0) > 1).sum())
    return result


def main():
    started = time.perf_counter()
    split = json.loads((A74 / "split.json").read_text())
    predictions = json.loads((A74 / "predictions.json").read_text())
    assert set(split["pages"]) == set(predictions["pages"])

    sealed = {"schema": "bbvlm.a75.full-mask-components/1",
              "rule": {"connectivity": 8, "minimum_component_pixels": 4,
                       "contour_approximation_epsilon_mask_pixels": 1.0,
                       "proposal_rectangle": "component bounding rectangle"},
              "source_predictions_sha256": sha(A74 / "predictions.json"), "pages": {}}
    for name in split["pages"]:
        audit = predictions["pages"][name]
        mask_path = A74 / f"{name}-textline-mask.png"
        assert sha(mask_path) == audit["mask_sha256"]
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE) > 0
        count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
        source_h, source_w = audit["source_shape"]
        scale_x, scale_y = mask.shape[1] / source_w, mask.shape[0] / source_h
        rows = []
        for component in range(1, count):
            area = int(stats[component, cv2.CC_STAT_AREA])
            if area < 4:
                continue
            x, y, width, height = map(int, stats[component, :4])
            local = (labels[y:y + height, x:x + width] == component).astype(np.uint8)
            contours, _ = cv2.findContours(local, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contour = max(contours, key=cv2.contourArea)
            approximate = cv2.approxPolyDP(contour, 1.0, True)[:, 0, :] + np.array([x, y])
            rows.append({
                "component": component, "mask_pixels": area,
                "bbox_mask": [x, y, x + width, y + height],
                "bbox_native": [x / scale_x, y / scale_y,
                                (x + width) / scale_x, (y + height) / scale_y],
                "contour_native": [[float(px / scale_x), float(py / scale_y)]
                                   for px, py in approximate],
            })
        sealed["pages"][name] = {"mask_sha256": sha(mask_path),
                                  "source_shape": [source_h, source_w],
                                  "mask_shape": list(mask.shape), "instances": rows}
    OUT.mkdir(parents=True, exist_ok=True)
    candidates_path = OUT / "candidates.json"
    candidates_path.write_text(json.dumps(sealed, indent=2) + "\n")
    candidate_hash = sha(candidates_path)

    expected = {row["file"]: row["sha256"] for row in json.loads(
        (ROOT / "experiments/loop/chronicling-a58/audit.json").read_text())["files_detail"]}
    pages = {}
    totals = {"candidates": 0, "reference_lines": 0, "true50": 0, "true70": 0,
              "assigned_iou_sum": 0.0, "assigned_pairs": 0, "merges": 0, "fragments": 0}
    for name in split["pages"]:
        reference, xml_hash = parse_reference(name, expected)
        candidates = sealed["pages"][name]["instances"]
        cb = np.asarray([row["bbox_native"] for row in candidates], dtype=float).reshape(-1, 4)
        rb = np.asarray([row["bbox"] for row in reference], dtype=float).reshape(-1, 4)
        iou = box_iou(cb, rb)
        row_idx, col_idx = linear_sum_assignment(-iou)
        summary = summarize(iou, row_idx, col_idx, len(cb), len(rb))
        summary["xml_sha256"] = xml_hash
        pages[name] = summary
        matched = iou[row_idx, col_idx]
        totals["candidates"] += len(cb); totals["reference_lines"] += len(rb)
        totals["true50"] += int((matched >= 0.5).sum())
        totals["true70"] += int((matched >= 0.7).sum())
        totals["assigned_iou_sum"] += float(matched.sum()); totals["assigned_pairs"] += len(matched)
        totals["merges"] += summary["candidate_merges_iou_gt10"]
        totals["fragments"] += summary["reference_fragments_iou_gt10"]
    aggregate = {"candidates": totals["candidates"], "reference_lines": totals["reference_lines"],
                 "matched_pairs": totals["assigned_pairs"],
                 "mean_assigned_iou": totals["assigned_iou_sum"] / totals["assigned_pairs"],
                 "candidate_merges_iou_gt10": totals["merges"],
                 "reference_fragments_iou_gt10": totals["fragments"]}
    for true_key, label in (("true50", "iou50"), ("true70", "iou70")):
        true = totals[true_key]
        precision = true / totals["candidates"]
        recall = true / totals["reference_lines"]
        aggregate[label] = {"true_matches": true, "precision": precision, "recall": recall,
                            "f1": 2 * precision * recall / (precision + recall)}
    checks = {
        "precision_iou50_ge95pct": aggregate["iou50"]["precision"] >= 0.95,
        "recall_iou50_ge95pct": aggregate["iou50"]["recall"] >= 0.95,
        "precision_iou70_ge80pct": aggregate["iou70"]["precision"] >= 0.80,
        "recall_iou70_ge80pct": aggregate["iou70"]["recall"] >= 0.80,
        "every_page_recall_iou50_ge90pct": all(page["iou50"]["recall"] >= 0.90
                                                     for page in pages.values()),
        "new_model_forwards_zero": True, "test_pages_opened_zero": True,
    }
    report = {"schema": "bbvlm.a75.report/1",
              "status": "consumed_instance_diagnostic",
              "candidate_sha256_before_xml": candidate_hash,
              "pages": pages, "aggregate": aggregate, "gate_checks": checks,
              "local_gate_passed": all(checks.values()),
              "new_model_forwards": 0, "ocr_calls": 0, "vlm_calls": 0,
              "test_pages_opened": 0, "seconds": time.perf_counter() - started,
              "all_scientific_gates_passed": False,
              "limitations": ["A74 pages and masks are consumed development data.",
                              "PAGE line rectangles and component rectangles are convention-dependent.",
                              "No OCR or reading-order impact was measured."]}
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"aggregate": aggregate, "gate_checks": checks,
                      "local_gate_passed": report["local_gate_passed"],
                      "seconds": report["seconds"]}, indent=2))


if __name__ == "__main__":
    main()

