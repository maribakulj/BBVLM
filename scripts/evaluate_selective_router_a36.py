#!/usr/bin/env python3
"""Consumed-data development measurement for non-expanding A32 routing."""
from pathlib import Path
import json, sys

import numpy as np
from lxml import etree as E
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate_french_holdout_a25 as core
from bbvlm.metrics import iou
from bbvlm.selective_refine import nonexpanding_vertical

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop"
EXP = BASE / "predicted-lines-a36"


def a35_dataset(name):
    split = json.loads((BASE / name / "split.json").read_text())
    core.SOURCE = BASE / name / "source"
    rows, _ = core.load_rows(split)
    boxes = json.loads((BASE / "native-refinement-a35/boxes.json").read_text())[name]
    routed = {}
    accepted = total = 0
    for line_id, native in boxes["native"].items():
        routed[line_id] = []
        for old, new in zip(native, boxes["native_a32"][line_id]):
            bbox = nonexpanding_vertical(old["bbox"], new["bbox"])
            accepted += bbox == list(new["bbox"])
            total += 1
            routed[line_id].append({"text": old["text"], "bbox": bbox})
    metric = core.box_metrics(rows, routed, "selective", False)
    return {"words": total, "accepted_refinements": accepted,
            "mean_iou": metric["mean_iou_matched"], "recall_iou80": metric["recall_iou80"]}


def a36_dataset():
    split = json.loads((EXP / "split.json").read_text())
    prediction = json.loads((EXP / "output/predictions.json").read_text())
    by_page = {p["page"]: p for p in prediction["pages"]}
    all_values, matches80, references, accepted, total = [], 0, 0, 0, 0
    pages = []
    for item in split["pages"]:
        root = E.parse(str(EXP / "source" / item["xml"]))
        ref = []
        for word in root.findall(".//{*}Word"):
            pts = np.array([list(map(float, p.split(","))) for p in word.find("{*}Coords").get("points").split()])
            ref.append([*pts.min(axis=0), *pts.max(axis=0)])
        pred = []
        for line in by_page[item["page"]]["lines"]:
            for word in line["words"]:
                box = nonexpanding_vertical(word["bbox"], word["refined_bbox"])
                accepted += box == list(word["refined_bbox"])
                total += 1
                pred.append(box)
        matrix = np.array([[iou(a, b) for b in pred] for a in ref])
        rr, cc = linear_sum_assignment(-matrix)
        values = matrix[rr, cc]
        pages.append({"page": item["page"], "mean_iou": float(values.mean()),
                      "recall_iou80": float((values >= .8).sum() / len(ref))})
        all_values.extend(values.tolist())
        matches80 += int((values >= .8).sum())
        references += len(ref)
    return {"words": total, "accepted_refinements": accepted,
            "mean_iou": float(np.mean(all_values)), "recall_iou80": matches80 / references, "pages": pages}


def main():
    report = {"schema": "bbvlm.selective-router-a36/1", "status": "consumed_development_complete",
              "rule": "accept A32 only when refined vertical extent <= native vertical extent",
              "reference_inputs_in_router": False, "parameters": 0,
              "datasets": {name: a35_dataset(name) for name in ("french-word-gt-a28", "word-transfer-a34")}}
    report["datasets"]["predicted-lines-a36"] = a36_dataset()
    report["decision"] = "freeze unchanged rule on a new unopened work; do not promote from consumed development"
    report["accepted_for_project_completion_gate"] = False
    (EXP / "output/selective-router-development.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
