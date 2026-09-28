#!/usr/bin/env python3
"""A43: reject A37 only when added foreground is majority-owned by another line."""
from pathlib import Path
import json
import sys

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate_component_affinity_router_a42 as a42
from bbvlm.metrics import iou
from bbvlm.selective_refine import nonexpanding_vertical

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop"
OUT = BASE / "added-component-router-a43"
DATASETS = ("predicted-lines-a36", "predicted-lines-a37")


def added_wrong_fraction(ink, native, candidate, target_index, models):
    height, width = ink.shape
    x0, y0, x1, y1 = map(lambda value: int(round(value)), candidate)
    x0, x1 = max(0, x0), min(width, x1)
    y0, y1 = max(0, y0), min(height, y1)
    if x1 <= x0 or y1 <= y0:
        return 0.0, 0
    ys, xs = np.nonzero(ink[y0:y1, x0:x1])
    xs = xs.astype(float) + x0
    ys = ys.astype(float) + y0
    nx0, ny0, nx1, ny1 = map(float, native)
    added = ~((xs >= nx0) & (xs < nx1) & (ys >= ny0) & (ys < ny1))
    xs, ys = xs[added], ys[added]
    if not len(xs):
        return 0.0, 0
    target_distance = np.abs(ys - a42.centre_y(models[target_index], xs))
    other_distance = np.full(len(xs), np.inf)
    for index, model in enumerate(models):
        if index == target_index:
            continue
        left, right = model["baseline"][0][0], model["baseline"][-1][0]
        valid = (xs >= left) & (xs <= right)
        if valid.any():
            distance = np.abs(ys[valid] - a42.centre_y(model, xs[valid]))
            other_distance[valid] = np.minimum(other_distance[valid], distance)
    wrong = int(np.count_nonzero(other_distance + 1e-9 < target_distance))
    return wrong / len(xs), len(xs)


def evaluate_dataset(name):
    base = BASE / name
    split = json.loads((base / "split.json").read_text())
    prediction = json.loads((base / "output/predictions.json").read_text())
    by_page = {p["page"]: p for p in prediction["pages"]}
    methods = {key: {"values": [], "matches50": 0, "matches80": 0, "reference": 0,
                     "accepted": 0, "words": 0, "regressions": 0,
                     "regressions_over_0_1": 0, "pages": []}
               for key in ("vertical", "added_majority")}
    changed = []
    for item in split["pages"]:
        page = by_page[item["page"]]
        models = a42.a41.parse_line_models(base / "output" / f"{item['page']}.page.xml")
        gray = cv2.imread(str(base / "source" / item["image"]), cv2.IMREAD_GRAYSCALE)
        _, ink = cv2.threshold(gray, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        reference = a42.a41.reference_boxes(base / "source" / item["xml"])
        flat, vertical, majority = [], [], []
        for line_index, line in enumerate(page["lines"]):
            for word in line["words"]:
                native = list(word["bbox"])
                candidate = nonexpanding_vertical(native, word["refined_bbox"])
                fraction, pixels = added_wrong_fraction(ink, native, candidate, line_index, models)
                revised = native if candidate != native and pixels and fraction > .5 else candidate
                if revised != candidate:
                    changed.append({"dataset": name, "page": item["page"], "line": line["id"],
                                    "text": word["text"], "native": native, "candidate": candidate,
                                    "added_wrong_fraction": fraction, "added_ink_pixels": pixels})
                flat.append(word); vertical.append(candidate); majority.append(revised)
        native_boxes = [word["bbox"] for word in flat]
        native_r, native_c, native_values = a42.a41.assigned(reference, native_boxes)
        for method, boxes in (("vertical", vertical), ("added_majority", majority)):
            _, _, values = a42.a41.assigned(reference, boxes)
            fixed = np.array([iou(reference[r], boxes[c]) for r, c in zip(native_r, native_c)])
            delta = fixed - native_values
            row = methods[method]
            row["values"].extend(values.tolist()); row["matches50"] += int((values >= .5).sum())
            row["matches80"] += int((values >= .8).sum()); row["reference"] += len(reference)
            row["accepted"] += sum(box == list(word["refined_bbox"]) for box, word in zip(boxes, flat))
            row["words"] += len(flat); row["regressions"] += int((delta < -1e-12).sum())
            row["regressions_over_0_1"] += int((delta < -.1).sum())
            row["pages"].append({"page": item["page"], "mean_iou": float(values.mean()),
                                 "recall_iou50": float((values >= .5).sum() / len(reference)),
                                 "recall_iou80": float((values >= .8).sum() / len(reference)),
                                 "accepted": sum(box == list(word["refined_bbox"]) for box, word in zip(boxes, flat))})
    for row in methods.values():
        row["mean_iou"] = float(np.mean(row.pop("values")))
        row["recall_iou50"] = row.pop("matches50") / row["reference"]
        row["recall_iou80"] = row.pop("matches80") / row["reference"]
    return {"scope": "full-page predicted lines/native words; consumed development",
            "methods": methods, "changed_count": len(changed), "changed_cases": changed}


def main():
    datasets = {name: evaluate_dataset(name) for name in DATASETS}
    noninferior = all(d["methods"]["added_majority"][metric] >= d["methods"]["vertical"][metric]
                      for d in datasets.values() for metric in ("mean_iou", "recall_iou80"))
    strict = any(d["methods"]["added_majority"][metric] > d["methods"]["vertical"][metric]
                 for d in datasets.values() for metric in ("mean_iou", "recall_iou80"))
    report = {"schema": "bbvlm.added-component-router-a43/1", "status": "consumed_development_complete",
              "candidate": "A37 plus reject when a strict majority of newly added foreground pixels is nearer another PERO line centre",
              "parameters": 0, "majority_rule": "strict > 0.5", "reference_inputs_in_router": False,
              "datasets": datasets, "consistent_noninferiority_gate": noninferior,
              "strict_gain_present": strict,
              "decision": "freeze unchanged on new data" if noninferior and strict else "reject; retain A37 height router",
              "cost": {"new_vlm_passes": 0, "new_ocr_forwards": 0,
                       "inputs": "cached predictions, source pixels and PERO line geometry"},
              "accepted_for_project_completion_gate": False,
              "limitations": ["A36/A37 are consumed development evidence.",
                              "The strict-majority rule is literature-motivated, not a truth certificate.",
                              "Provider PAGE word rectangles remain independently unadjudicated."]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"decision": report["decision"],
                      "datasets": {name: data["methods"] for name, data in datasets.items()},
                      "changed": {name: data["changed_count"] for name, data in datasets.items()}}, indent=2))


if __name__ == "__main__":
    main()
