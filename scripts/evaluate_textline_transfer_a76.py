"""Infer and seal A76 image-only line instances, then score frozen transfer."""
import hashlib
import json
import time
from pathlib import Path

import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment

from evaluate_eynollah_textline_keras_a72 import ROOT, TARGET_WIDTH, load_predictor, predict_tiled, verify_model
from evaluate_textline_instances_a75 import box_iou, parse_reference, summarize

OUT = ROOT / "experiments/loop/next-a76"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    started = time.perf_counter()
    split_path = OUT / "split.json"
    split = json.loads(split_path.read_text())
    assert split["status"] == "frozen_unopened_for_a76"
    assert sha(OUT / "PROTOCOL.md") == split["protocol_sha256"]
    assets = json.loads((OUT / "assets.json").read_text())
    asset = {row["page"]: row for row in assets["images"]}
    assert set(asset) == set(split["pages"])

    prediction_path = OUT / "predictions.json"
    candidate_path = OUT / "candidates.json"
    reused = prediction_path.exists() and candidate_path.exists()
    if reused:
        predictions = json.loads(prediction_path.read_text())
        sealed = json.loads(candidate_path.read_text())
        assert predictions["split_sha256"] == sha(split_path)
        assert sealed["source_predictions_sha256"] == sha(prediction_path)
        for name in split["pages"]:
            assert sha(ROOT / asset[name]["path"]) == predictions["pages"][name]["image_sha256"]
            assert sha(OUT / f"{name}-textline-mask.png") == predictions["pages"][name]["mask_sha256"]
    else:
        verify_model()
        predict, output_name = load_predictor()
        predictions = {"schema": "bbvlm.a76.predictions/1", "split_sha256": sha(split_path),
                       "implementation": "A72/A74 native Eynollah textline SavedModel unchanged",
                       "signature_output": output_name, "pages": {}}
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
            predictions["pages"][name] = {"image_sha256": sha(path), "source_shape": [height, width],
                "mask_shape": list(mask.shape), "mask_sha256": sha(mask_path),
                "positive_pixels": int(mask.sum()), "tiles": tiles, "seconds": seconds}
        prediction_path.write_text(json.dumps(predictions, indent=2) + "\n")

        sealed = {"schema": "bbvlm.a76.full-mask-components/1",
                  "rule": {"connectivity": 8, "minimum_component_pixels": 4,
                           "contour_approximation_epsilon_mask_pixels": 1.0,
                           "proposal_rectangle": "component bounding rectangle"},
                  "source_predictions_sha256": sha(prediction_path), "pages": {}}
        for name in split["pages"]:
            audit = predictions["pages"][name]
            mask_path = OUT / f"{name}-textline-mask.png"
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
                rows.append({"component": component, "mask_pixels": area,
                    "bbox_mask": [x, y, x + width, y + height],
                    "bbox_native": [x / scale_x, y / scale_y, (x + width) / scale_x, (y + height) / scale_y],
                    "contour_native": [[float(px / scale_x), float(py / scale_y)] for px, py in approximate]})
            sealed["pages"][name] = {"mask_sha256": sha(mask_path), "source_shape": [source_h, source_w],
                                     "mask_shape": list(mask.shape), "instances": rows}
        candidate_path.write_text(json.dumps(sealed, indent=2) + "\n")

    # XML is opened only after every image-only prediction and candidate is sealed.
    prediction_hash, candidate_hash = sha(prediction_path), sha(candidate_path)
    expected = {row["file"]: row["sha256"] for row in json.loads(
        (ROOT / "experiments/loop/chronicling-a58/audit.json").read_text())["files_detail"]}
    pages, totals = {}, {"candidates": 0, "reference_lines": 0, "true50": 0, "true70": 0,
        "assigned_iou_sum": 0.0, "assigned_pairs": 0, "merges": 0, "fragments": 0}
    for name in split["pages"]:
        reference, xml_hash = parse_reference(name, expected)
        candidates = sealed["pages"][name]["instances"]
        cb = np.asarray([row["bbox_native"] for row in candidates], dtype=float).reshape(-1, 4)
        rb = np.asarray([row["bbox"] for row in reference], dtype=float).reshape(-1, 4)
        iou = box_iou(cb, rb)
        row_idx, col_idx = linear_sum_assignment(-iou)
        page = summarize(iou, row_idx, col_idx, len(cb), len(rb)); page["xml_sha256"] = xml_hash
        pages[name] = page
        matched = iou[row_idx, col_idx]
        totals["candidates"] += len(cb); totals["reference_lines"] += len(rb)
        totals["true50"] += int((matched >= .5).sum()); totals["true70"] += int((matched >= .7).sum())
        totals["assigned_iou_sum"] += float(matched.sum()); totals["assigned_pairs"] += len(matched)
        totals["merges"] += page["candidate_merges_iou_gt10"]; totals["fragments"] += page["reference_fragments_iou_gt10"]
    aggregate = {"candidates": totals["candidates"], "reference_lines": totals["reference_lines"],
        "matched_pairs": totals["assigned_pairs"],
        "mean_assigned_iou": totals["assigned_iou_sum"] / totals["assigned_pairs"],
        "candidate_merges_iou_gt10": totals["merges"], "reference_fragments_iou_gt10": totals["fragments"]}
    for key, label in (("true50", "iou50"), ("true70", "iou70")):
        true = totals[key]; precision = true / totals["candidates"]; recall = true / totals["reference_lines"]
        aggregate[label] = {"true_matches": true, "precision": precision, "recall": recall,
                            "f1": 2 * precision * recall / (precision + recall)}
    checks = {"precision_iou50_ge95pct": aggregate["iou50"]["precision"] >= .95,
        "recall_iou50_ge95pct": aggregate["iou50"]["recall"] >= .95,
        "precision_iou70_ge80pct": aggregate["iou70"]["precision"] >= .80,
        "recall_iou70_ge80pct": aggregate["iou70"]["recall"] >= .80,
        "every_page_precision_iou50_ge85pct": all(p["iou50"]["precision"] >= .85 for p in pages.values()),
        "every_page_recall_iou50_ge90pct": all(p["iou50"]["recall"] >= .90 for p in pages.values()),
        "test_pages_opened_zero": split["test_pages_opened"] == 0}
    report = {"schema": "bbvlm.a76.report/1", "status": "frozen_training_instance_transfer",
        "prediction_sha256_before_xml": prediction_hash, "candidate_sha256_before_xml": candidate_hash,
        "pages": pages, "aggregate": aggregate, "gate_checks": checks, "local_gate_passed": all(checks.values()),
        "model_forwards": sum(p["tiles"] for p in predictions["pages"].values()),
        "new_model_forwards_in_scoring_retry": 0 if reused else sum(p["tiles"] for p in predictions["pages"].values()),
        "ocr_calls": 0, "vlm_calls": 0, "test_pages_opened": 0, "seconds": time.perf_counter() - started,
        "all_scientific_gates_passed": False,
        "limitations": ["Training PAGE rectangles are convention-dependent and not perfect truth.",
                        "Line rectangles are not word-level ALTO boxes.",
                        "No OCR, reading order, article, metadata or retrieval output was evaluated."]}
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"aggregate": aggregate, "pages": pages, "gate_checks": checks,
                      "local_gate_passed": report["local_gate_passed"], "seconds": report["seconds"]}, indent=2))


if __name__ == "__main__":
    main()
