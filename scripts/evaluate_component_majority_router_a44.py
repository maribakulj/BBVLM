#!/usr/bin/env python3
"""A44: route A37 by whole-component majority ownership between predicted lines."""
from pathlib import Path
import json
import sys

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate_component_affinity_router_a42 as a42
from bbvlm.component_boxes import selected_ink
from bbvlm.metrics import iou
from bbvlm.selective_refine import nonexpanding_vertical

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop"
OUT = BASE / "component-majority-router-a44"
DATASETS = ("predicted-lines-a36", "predicted-lines-a37")


def component_owners(mask, offset, models):
    """Assign each complete selected component to its majority-nearest line."""
    count, labels = cv2.connectedComponents(mask.astype("uint8"), 8)
    y_offset, x_offset = offset
    ys, xs = np.nonzero(labels)
    component_ids = labels[ys, xs]
    xs = xs.astype(float) + x_offset
    ys = ys.astype(float) + y_offset
    distances = np.full((len(models), len(xs)), np.inf, dtype=float)
    for index, model in enumerate(models):
        left, right = model["baseline"][0][0], model["baseline"][-1][0]
        valid = (xs >= left) & (xs <= right)
        if valid.any():
            distances[index, valid] = np.abs(ys[valid] - a42.centre_y(model, xs[valid]))
    nearest = np.argmin(distances, axis=0)
    owners = {}
    for component in range(1, count):
        votes = np.bincount(nearest[component_ids == component], minlength=len(models))
        owners[component] = int(np.flatnonzero(votes == votes.max())[0])
    return labels, owners


def labels_in_box(labels, line_box, box):
    line_x0, line_y0, _, _ = map(lambda value: int(round(value)), line_box)
    x0, y0, x1, y1 = map(lambda value: int(round(value)), box)
    x0, x1 = max(0, x0 - line_x0), min(labels.shape[1], x1 - line_x0)
    y0, y1 = max(0, y0 - line_y0), min(labels.shape[0], y1 - line_y0)
    if x1 <= x0 or y1 <= y0:
        return set()
    return set(np.unique(labels[y0:y1, x0:x1])) - {0}


def evaluate_dataset(name):
    base = BASE / name
    split = json.loads((base / "split.json").read_text())
    prediction = json.loads((base / "output/predictions.json").read_text())
    by_page = {p["page"]: p for p in prediction["pages"]}
    methods = {key: {"values": [], "matches50": 0, "matches80": 0, "reference": 0,
                     "accepted": 0, "words": 0, "regressions": 0,
                     "regressions_over_0_1": 0, "pages": []}
               for key in ("vertical", "component_majority")}
    changed = []
    for item in split["pages"]:
        page = by_page[item["page"]]
        models = a42.a41.parse_line_models(base / "output" / f"{item['page']}.page.xml")
        if len(models) != len(page["lines"]):
            raise ValueError("PAGE/ALTO line count mismatch")
        gray = cv2.imread(str(base / "source" / item["image"]), cv2.IMREAD_GRAYSCALE)
        if gray is None:
            raise ValueError("missing source image")
        reference = a42.a41.reference_boxes(base / "source" / item["xml"])
        flat, vertical, majority = [], [], []
        for line_index, line in enumerate(page["lines"]):
            line_box = [int(round(value)) for value in line["bbox"]]
            lx0, ly0, lx1, ly1 = line_box
            crop = gray[ly0:ly1, lx0:lx1]
            _, ink = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            selected, _ = selected_ink(ink, "satellites")
            labels, owners = component_owners(selected, (ly0, lx0), models)
            for word in line["words"]:
                native = list(word["bbox"])
                candidate = nonexpanding_vertical(native, word["refined_bbox"])
                introduced = labels_in_box(labels, line_box, candidate) - labels_in_box(labels, line_box, native)
                foreign = sorted(component for component in introduced if owners[component] != line_index)
                revised = native if candidate != native and foreign else candidate
                if revised != candidate:
                    changed.append({"dataset": name, "page": item["page"], "line": line["id"],
                                    "text": word["text"], "native": native, "candidate": candidate,
                                    "introduced_components": sorted(int(x) for x in introduced),
                                    "foreign_components": [int(x) for x in foreign]})
                flat.append(word); vertical.append(candidate); majority.append(revised)
        native_boxes = [word["bbox"] for word in flat]
        native_r, native_c, native_values = a42.a41.assigned(reference, native_boxes)
        for method, boxes in (("vertical", vertical), ("component_majority", majority)):
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
    noninferior = all(d["methods"]["component_majority"][metric] >= d["methods"]["vertical"][metric]
                      for d in datasets.values() for metric in ("mean_iou", "recall_iou80"))
    strict = any(d["methods"]["component_majority"][metric] > d["methods"]["vertical"][metric]
                 for d in datasets.values() for metric in ("mean_iou", "recall_iou80"))
    report = {"schema": "bbvlm.component-majority-router-a44/1", "status": "consumed_development_complete",
              "candidate": "A37 plus reject a newly introduced whole selected component majority-owned by another PERO line centre",
              "parameters": 0, "reference_inputs_in_router": False, "datasets": datasets,
              "consistent_noninferiority_gate": noninferior, "strict_gain_present": strict,
              "decision": "freeze unchanged on new data" if noninferior and strict else "reject; retain A37 height router",
              "cost": {"new_vlm_passes": 0, "new_ocr_forwards": 0,
                       "inputs": "cached predictions, source pixels and PERO line geometry"},
              "accepted_for_project_completion_gate": False,
              "limitations": ["A36/A37 are consumed and cannot validate the candidate.",
                              "Line-centre majority is a component ownership heuristic, not truth.",
                              "Provider PAGE word rectangles remain independently unadjudicated."]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"decision": report["decision"],
                      "datasets": {name: data["methods"] for name, data in datasets.items()},
                      "changed": {name: data["changed_count"] for name, data in datasets.items()}}, indent=2))


if __name__ == "__main__":
    main()
