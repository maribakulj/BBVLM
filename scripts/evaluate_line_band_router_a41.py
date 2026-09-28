#!/usr/bin/env python3
"""A41 consumed-data test of PERO baseline/height-band ownership routing."""
from pathlib import Path
import ast
import json
import re
import sys

import numpy as np
from lxml import etree as E
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from bbvlm.metrics import iou
from bbvlm.selective_refine import nonexpanding_vertical, nonworsening_line_band

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop"
OUT = BASE / "line-band-router-a41"
DATASETS = ("predicted-lines-a36", "predicted-lines-a37")


def coords(node):
    points = np.array([list(map(float, p.split(","))) for p in node.find("{*}Coords").get("points").split()])
    return [*points.min(axis=0), *points.max(axis=0)]


def parse_points(value):
    return [list(map(float, point.split(","))) for point in value.split()]


def parse_line_models(path):
    root = E.parse(str(path))
    models = []
    for line in root.findall(".//{*}TextLine"):
        if not line.findtext("{*}TextEquiv/{*}Unicode", default="").strip():
            continue
        baseline = line.find("{*}Baseline")
        match = re.search(r"heights_v2:(\[[^]]+\])", line.get("custom", ""))
        if baseline is None or match is None:
            raise ValueError(f"missing PERO baseline/heights in {path.name}/{line.get('id')}")
        heights = ast.literal_eval(match.group(1))
        models.append({"baseline": parse_points(baseline.get("points")), "heights": heights})
    return models


def reference_boxes(path):
    root = E.parse(str(path))
    return [coords(word) for word in root.findall(".//{*}Word")]


def assigned(reference, prediction):
    matrix = np.array([[iou(a, b) for b in prediction] for a in reference])
    rr, cc = linear_sum_assignment(-matrix)
    return rr, cc, matrix[rr, cc]


def evaluate_dataset(name):
    base = BASE / name
    split = json.loads((base / "split.json").read_text())
    prediction = json.loads((base / "output/predictions.json").read_text())
    by_page = {p["page"]: p for p in prediction["pages"]}
    methods = {key: {"values": [], "matches50": 0, "matches80": 0, "reference": 0,
                     "accepted": 0, "words": 0, "regressions": 0,
                     "regressions_over_0_1": 0, "pages": []}
               for key in ("vertical", "line_band")}
    diagnostics = []
    for item in split["pages"]:
        page = by_page[item["page"]]
        models = parse_line_models(base / "output" / f"{item['page']}.page.xml")
        if len(models) != len(page["lines"]):
            raise ValueError("PAGE/ALTO line count mismatch")
        reference = reference_boxes(base / "source" / item["xml"])
        flat = []
        for line, model in zip(page["lines"], models):
            for word in line["words"]:
                flat.append((word, model, line["id"]))
        native = [word["bbox"] for word, _, _ in flat]
        native_r, native_c, native_values = assigned(reference, native)
        routes = {
            "vertical": [nonexpanding_vertical(w["bbox"], w["refined_bbox"]) for w, _, _ in flat],
            "line_band": [nonworsening_line_band(w["bbox"], w["refined_bbox"], m["baseline"], m["heights"])
                          for w, m, _ in flat],
        }
        for method, boxes in routes.items():
            rr, cc, values = assigned(reference, boxes)
            fixed = np.array([iou(reference[r], boxes[c]) for r, c in zip(native_r, native_c)])
            delta = fixed - native_values
            row = methods[method]
            row["values"].extend(values.tolist())
            row["matches50"] += int((values >= .5).sum())
            row["matches80"] += int((values >= .8).sum())
            row["reference"] += len(reference)
            row["accepted"] += sum(box == list(word["refined_bbox"]) for box, (word, _, _) in zip(boxes, flat))
            row["words"] += len(flat)
            row["regressions"] += int((delta < -1e-12).sum())
            row["regressions_over_0_1"] += int((delta < -.1).sum())
            row["pages"].append({"page": item["page"], "mean_iou": float(values.mean()),
                                 "recall_iou50": float((values >= .5).sum() / len(reference)),
                                 "recall_iou80": float((values >= .8).sum() / len(reference)),
                                 "accepted": sum(box == list(word["refined_bbox"])
                                                 for box, (word, _, _) in zip(boxes, flat))})
        for index, ((word, model, line_id), old, new) in enumerate(zip(flat, routes["vertical"], routes["line_band"])):
            if old != new:
                diagnostics.append({"dataset": name, "page": item["page"], "line": line_id,
                                    "word_index": index, "text": word["text"], "native": word["bbox"],
                                    "refined": word["refined_bbox"], "vertical": old, "line_band": new,
                                    "baseline": model["baseline"], "heights": model["heights"]})
    for row in methods.values():
        row["mean_iou"] = float(np.mean(row.pop("values")))
        row["recall_iou50"] = row.pop("matches50") / row["reference"]
        row["recall_iou80"] = row.pop("matches80") / row["reference"]
    return {"scope": "full-page predicted lines/native words; consumed development",
            "methods": methods, "changed_cases": diagnostics}


def main():
    datasets = {name: evaluate_dataset(name) for name in DATASETS}
    noninferior = all(d["methods"]["line_band"][metric] >= d["methods"]["vertical"][metric]
                      for d in datasets.values() for metric in ("mean_iou", "recall_iou80"))
    strict = any(d["methods"]["line_band"][metric] > d["methods"]["vertical"][metric]
                 for d in datasets.values() for metric in ("mean_iou", "recall_iou80"))
    report = {"schema": "bbvlm.line-band-router-a41/1", "status": "consumed_development_complete",
              "candidate": "A37 height guard plus non-worsening overshoot beyond PERO baseline/heights_v2 band",
              "parameters": 0, "reference_inputs_in_router": False, "datasets": datasets,
              "consistent_noninferiority_gate": noninferior, "strict_gain_present": strict,
              "decision": "freeze unchanged on new data" if noninferior and strict else "reject; retain A37 height router",
              "cost": {"new_vlm_passes": 0, "new_ocr_forwards": 0, "inputs": "cached predictions and PERO PAGE geometry"},
              "accepted_for_project_completion_gate": False,
              "limitations": ["A36/A37 are consumed and cannot validate the candidate.",
                              "PERO heights_v2 is an estimated local band, not word ownership truth.",
                              "The experiment scores provider PAGE rectangles, not independently adjudicated perfect boxes."]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
