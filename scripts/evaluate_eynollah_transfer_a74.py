"""Run the frozen A72 textline stage on the sealed A74 transfer pages."""
import hashlib
import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np

from evaluate_crop_geometry_a65 import polygon
from evaluate_eynollah_textline_keras_a72 import (
    ROOT, TARGET_WIDTH, load_predictor, predict_tiled, verify_model,
)

OUT = ROOT / "experiments/loop/next-a74"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rasterize(lines, shape, sx, sy):
    union = np.zeros(shape, dtype=np.uint8)
    polygons = []
    for line_id, geom in lines:
        pts = np.rint(np.asarray(geom.exterior.coords) * np.array([sx, sy])).astype(np.int32)
        cv2.fillPoly(union, [pts], 1)
        polygons.append((line_id, pts))
    return union.astype(bool), polygons


def local_coverage(mask, pts):
    x, y, width, height = cv2.boundingRect(pts)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(mask.shape[1], x + width), min(mask.shape[0], y + height)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    local = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.fillPoly(local, [pts - np.array([x0, y0])], 1)
    denominator = int(local.sum())
    return float(np.logical_and(mask[y0:y1, x0:x1], local).sum() / denominator) if denominator else 0.0


def parse_lines(name, expected):
    path = ROOT / "corpora/chronicling-germany/annotations" / f"{name}.xml"
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
    split_path = OUT / "split.json"
    split = json.loads(split_path.read_text())
    assert split["status"] == "frozen_unopened_for_a74"
    assert sha(OUT / "PROTOCOL.md") == split["protocol_sha256"]
    assets = json.loads((OUT / "assets.json").read_text())
    asset = {row["page"]: row for row in assets["images"]}
    assert set(asset) == set(split["pages"])
    prediction_path = OUT / "predictions.json"
    reused = prediction_path.exists()
    if reused:
        prediction = json.loads(prediction_path.read_text())
        assert prediction["split_sha256"] == sha(split_path)
        assert set(prediction["pages"]) == set(split["pages"])
        for name, audit in prediction["pages"].items():
            assert sha(ROOT / asset[name]["path"]) == audit["image_sha256"]
            assert sha(OUT / f"{name}-textline-mask.png") == audit["mask_sha256"]
    else:
        verify_model()
        predict, output_name = load_predictor()
        # Seal all image-only predictions before opening any A74 XML for scoring.
        prediction = {
            "schema": "bbvlm.a74.predictions/1",
            "split_sha256": sha(split_path),
            "implementation": "A72 native Eynollah textline SavedModel unchanged",
            "signature_output": output_name,
            "pages": {},
        }
        for name in split["pages"]:
            path = ROOT / asset[name]["path"]
            assert sha(path) == asset[name]["sha256"]
            image = cv2.imread(str(path), cv2.IMREAD_COLOR)
            assert image is not None
            height, width = image.shape[:2]
            resized_height = round(height * TARGET_WIDTH / width)
            resized = cv2.resize(image, (TARGET_WIDTH, resized_height), interpolation=cv2.INTER_AREA)
            tick = time.perf_counter()
            mask, tiles = predict_tiled(predict, resized)
            seconds = time.perf_counter() - tick
            mask_path = OUT / f"{name}-textline-mask.png"
            assert cv2.imwrite(str(mask_path), mask.astype(np.uint8) * 255)
            prediction["pages"][name] = {
                "image_sha256": sha(path), "source_shape": [height, width],
                "mask_shape": list(mask.shape), "mask_sha256": sha(mask_path),
                "positive_pixels": int(mask.sum()), "tiles": tiles, "seconds": seconds,
            }
        prediction_path.write_text(json.dumps(prediction, indent=2) + "\n")
    prediction_hash = sha(prediction_path)

    expected = {row["file"]: row["sha256"] for row in json.loads(
        (ROOT / "experiments/loop/chronicling-a58/audit.json").read_text())["files_detail"]}
    pages = {}
    all_line_coverages = []
    total_mask = total_mask_inside = total_reference = total_reference_hit = 0
    for name in split["pages"]:
        audit = prediction["pages"][name]
        mask_path = OUT / f"{name}-textline-mask.png"
        assert sha(mask_path) == audit["mask_sha256"]
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE) > 0
        source_h, source_w = audit["source_shape"]
        sx, sy = mask.shape[1] / source_w, mask.shape[0] / source_h
        lines, xml_hash = parse_lines(name, expected)
        reference, line_masks = rasterize(lines, mask.shape, sx, sy)
        coverages = []
        rows = []
        for line_id, pts in line_masks:
            coverage = local_coverage(mask, pts)
            coverages.append(coverage)
            rows.append({"line_id": line_id, "coverage": coverage,
                         "hit_ge1pct": coverage >= 0.01})
        mask_pixels = int(mask.sum())
        inside = int(np.logical_and(mask, reference).sum())
        reference_pixels = int(reference.sum())
        pages[name] = {
            "xml_sha256": xml_hash, "lines": len(rows),
            "lines_hit_ge1pct": sum(row["hit_ge1pct"] for row in rows),
            "line_hit_ratio": sum(row["hit_ge1pct"] for row in rows) / len(rows),
            "mask_inside_line_union_fraction": inside / mask_pixels if mask_pixels else 0.0,
            "line_union_covered_fraction": inside / reference_pixels if reference_pixels else 0.0,
            "rows": rows,
        }
        all_line_coverages.extend(coverages)
        total_mask += mask_pixels; total_mask_inside += inside
        total_reference += reference_pixels; total_reference_hit += inside
    aggregate = {
        "lines": len(all_line_coverages),
        "lines_hit_ge1pct": sum(value >= 0.01 for value in all_line_coverages),
        "line_hit_ratio": sum(value >= 0.01 for value in all_line_coverages) / len(all_line_coverages),
        "mask_inside_line_union_fraction": total_mask_inside / total_mask,
        "line_union_covered_fraction": total_reference_hit / total_reference,
    }
    checks = {
        "line_hit_ratio_ge99pct": aggregate["line_hit_ratio"] >= 0.99,
        "every_page_mask_precision_ge75pct": all(
            page["mask_inside_line_union_fraction"] >= 0.75 for page in pages.values()),
        "aggregate_line_union_coverage_ge50pct": aggregate["line_union_covered_fraction"] >= 0.50,
        "test_pages_opened_zero": split["test_pages_opened"] == 0,
    }
    report = {
        "schema": "bbvlm.a74.report/1",
        "status": "frozen_training_transfer_dense_mask_not_boxes",
        "prediction_sha256_before_xml": prediction_hash,
        "pages": pages, "aggregate": aggregate, "gate_checks": checks,
        "local_gate_passed": all(checks.values()),
        "model_forwards": sum(page["tiles"] for page in prediction["pages"].values()),
        "new_model_forwards_in_scoring_retry": 0 if reused else sum(
            page["tiles"] for page in prediction["pages"].values()),
        "inference_reused_after_interrupted_scoring": reused,
        "ocr_calls": 0, "vlm_calls": 0, "test_pages_opened": 0,
        "seconds": time.perf_counter() - started,
        "all_scientific_gates_passed": False,
        "limitations": [
            "Dense mask evidence is not an ALTO rectangle or individual-line segmentation.",
            "Training PAGE polygons were structurally audited in A58 and are not perfect truth.",
            "No OCR, reading order, article, metadata or retrieval output was evaluated.",
        ],
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"aggregate": aggregate, "gate_checks": checks,
                      "local_gate_passed": report["local_gate_passed"],
                      "model_forwards": report["model_forwards"],
                      "seconds": report["seconds"]}, indent=2))


if __name__ == "__main__":
    main()
