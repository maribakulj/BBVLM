#!/usr/bin/env python3
"""A42: route A37 boxes by foreground-pixel affinity to predicted line centres."""
from pathlib import Path
import json
import sys

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate_line_band_router_a41 as a41
from bbvlm.metrics import iou
from bbvlm.selective_refine import nonexpanding_vertical

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop"
OUT = BASE / "component-affinity-router-a42"
DATASETS = ("predicted-lines-a36", "predicted-lines-a37")


def centre_y(model, x):
    ascender, descender = model["heights"]
    points = np.asarray(model["baseline"], dtype=float)
    return np.interp(x, points[:, 0], points[:, 1]) + (float(descender) - float(ascender)) / 2


def wrong_line_fraction(ink, box, target_index, models):
    height, width = ink.shape
    x0, y0, x1, y1 = map(lambda value: int(round(value)), box)
    x0, x1 = max(0, x0), min(width, x1)
    y0, y1 = max(0, y0), min(height, y1)
    if x1 <= x0 or y1 <= y0:
        return 0.0, 0
    ys, xs = np.nonzero(ink[y0:y1, x0:x1])
    if not len(xs):
        return 0.0, 0
    xs = xs.astype(float) + x0
    ys = ys.astype(float) + y0
    target = models[target_index]
    target_distance = np.abs(ys - centre_y(target, xs))
    other_distance = np.full(len(xs), np.inf)
    for index, model in enumerate(models):
        if index == target_index:
            continue
        left, right = model["baseline"][0][0], model["baseline"][-1][0]
        valid = (xs >= left) & (xs <= right)
        if valid.any():
            distance = np.abs(ys[valid] - centre_y(model, xs[valid]))
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
               for key in ("vertical", "component_affinity")}
    changed = []
    for item in split["pages"]:
        page = by_page[item["page"]]
        models = a41.parse_line_models(base / "output" / f"{item['page']}.page.xml")
        if len(models) != len(page["lines"]):
            raise ValueError("PAGE/ALTO line count mismatch")
        gray = cv2.imread(str(base / "source" / item["image"]), cv2.IMREAD_GRAYSCALE)
        if gray is None:
            raise ValueError("missing source image")
        _, ink = cv2.threshold(gray, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        reference = a41.reference_boxes(base / "source" / item["xml"])
        flat = []
        vertical = []
        affinity = []
        for line_index, (line, model) in enumerate(zip(page["lines"], models)):
            for word in line["words"]:
                old = list(word["bbox"])
                candidate = nonexpanding_vertical(old, word["refined_bbox"])
                revised = candidate
                old_fraction, old_pixels = wrong_line_fraction(ink, old, line_index, models)
                new_fraction, new_pixels = wrong_line_fraction(ink, candidate, line_index, models)
                if candidate != old and new_fraction > old_fraction + 1e-12:
                    revised = old
                    changed.append({"dataset": name, "page": item["page"], "line": line["id"],
                                    "text": word["text"], "native": old, "candidate": candidate,
                                    "native_wrong_fraction": old_fraction,
                                    "candidate_wrong_fraction": new_fraction,
                                    "native_ink_pixels": old_pixels, "candidate_ink_pixels": new_pixels})
                flat.append(word)
                vertical.append(candidate)
                affinity.append(revised)
        native = [word["bbox"] for word in flat]
        native_r, native_c, native_values = a41.assigned(reference, native)
        for method, boxes in (("vertical", vertical), ("component_affinity", affinity)):
            rr, cc, values = a41.assigned(reference, boxes)
            fixed = np.array([iou(reference[r], boxes[c]) for r, c in zip(native_r, native_c)])
            delta = fixed - native_values
            row = methods[method]
            row["values"].extend(values.tolist())
            row["matches50"] += int((values >= .5).sum())
            row["matches80"] += int((values >= .8).sum())
            row["reference"] += len(reference)
            row["accepted"] += sum(box == list(word["refined_bbox"]) for box, word in zip(boxes, flat))
            row["words"] += len(flat)
            row["regressions"] += int((delta < -1e-12).sum())
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
    noninferior = all(d["methods"]["component_affinity"][metric] >= d["methods"]["vertical"][metric]
                      for d in datasets.values() for metric in ("mean_iou", "recall_iou80"))
    strict = any(d["methods"]["component_affinity"][metric] > d["methods"]["vertical"][metric]
                 for d in datasets.values() for metric in ("mean_iou", "recall_iou80"))
    report = {"schema": "bbvlm.component-affinity-router-a42/1", "status": "consumed_development_complete",
              "candidate": "A37 plus non-worsening fraction of foreground pixels nearer another PERO line centre",
              "parameters": 0, "reference_inputs_in_router": False, "datasets": datasets,
              "consistent_noninferiority_gate": noninferior, "strict_gain_present": strict,
              "decision": "freeze unchanged on new data" if noninferior and strict else "reject; retain A37 height router",
              "cost": {"new_vlm_passes": 0, "new_ocr_forwards": 0,
                       "inputs": "cached predictions, source pixels and PERO line geometry"},
              "accepted_for_project_completion_gate": False,
              "limitations": ["A36/A37 are consumed and cannot validate the candidate.",
                              "Nearest predicted line centre is an ownership heuristic, not ground truth.",
                              "Provider PAGE rectangles remain imperfect and independently unadjudicated."]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"schema": report["schema"], "decision": report["decision"],
                      "datasets": {name: data["methods"] for name, data in datasets.items()},
                      "changed": {name: data["changed_count"] for name, data in datasets.items()}},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
