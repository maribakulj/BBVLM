#!/usr/bin/env python3
"""A39 consumed-data comparison of vertical-only and vertical-containment routing."""
from pathlib import Path
import json, sys

import numpy as np
from lxml import etree as E
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate_french_holdout_a25 as core
from bbvlm.metrics import iou
from bbvlm.selective_refine import nonexpanding_vertical, vertically_contained

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop"
EXP = BASE / "vertical-containment-a39"


def oracle_dataset(name):
    split = json.loads((BASE / name / "split.json").read_text())
    core.SOURCE = BASE / name / "source"
    rows, _ = core.load_rows(split)
    boxes = json.loads((BASE / "native-refinement-a35/boxes.json").read_text())[name]
    methods = {}
    for method, route in (("vertical", nonexpanding_vertical), ("contained", vertically_contained)):
        routed, accepted, total = {}, 0, 0
        for line_id, native in boxes["native"].items():
            routed[line_id] = []
            for old, new in zip(native, boxes["native_a32"][line_id]):
                bbox = route(old["bbox"], new["bbox"])
                accepted += bbox == list(new["bbox"])
                total += 1
                routed[line_id].append({"text": old["text"], "bbox": bbox})
        metric = core.box_metrics(rows, routed, method, False)
        methods[method] = {"words": total, "accepted": accepted,
                           "mean_iou": metric["mean_iou_matched"],
                           "recall_iou50": metric["recall_iou50"],
                           "recall_iou80": metric["recall_iou80"]}
    return {"scope": "oracle lines with native recognized words; consumed", "methods": methods}


def page_reference(path):
    root = E.parse(str(path))
    out = []
    for word in root.findall(".//{*}Word"):
        pts = np.array([list(map(float, p.split(","))) for p in word.find("{*}Coords").get("points").split()])
        out.append([*pts.min(axis=0), *pts.max(axis=0)])
    return out


def assigned(ref, pred):
    matrix = np.array([[iou(a, b) for b in pred] for a in ref])
    rr, cc = linear_sum_assignment(-matrix)
    return rr, cc, matrix[rr, cc]


def predicted_dataset(name):
    base = BASE / name
    split = json.loads((base / "split.json").read_text())
    prediction = json.loads((base / "output/predictions.json").read_text())
    by_page = {p["page"]: p for p in prediction["pages"]}
    methods = {"vertical": {"values": [], "matches50": 0, "matches80": 0, "reference": 0,
                             "accepted": 0, "words": 0, "regressions": 0, "regressions_over_0_1": 0, "pages": []},
               "contained": {"values": [], "matches50": 0, "matches80": 0, "reference": 0,
                         "accepted": 0, "words": 0, "regressions": 0, "regressions_over_0_1": 0, "pages": []}}
    for item in split["pages"]:
        ref = page_reference(base / "source" / item["xml"])
        words = [w for line in by_page[item["page"]]["lines"] for w in line["words"]]
        native = [w["bbox"] for w in words]
        native_r, native_c, native_values = assigned(ref, native)
        for method, route in (("vertical", nonexpanding_vertical), ("contained", vertically_contained)):
            pred = [route(w["bbox"], w["refined_bbox"]) for w in words]
            accepted_count = sum(b == list(w["refined_bbox"]) for b, w in zip(pred, words))
            rr, cc, values = assigned(ref, pred)
            fixed = np.array([iou(ref[r], pred[c]) for r, c in zip(native_r, native_c)])
            delta = fixed - native_values
            row = methods[method]
            row["values"].extend(values.tolist()); row["matches50"] += int((values >= .5).sum())
            row["matches80"] += int((values >= .8).sum()); row["reference"] += len(ref)
            row["accepted"] += accepted_count; row["words"] += len(words)
            row["regressions"] += int((delta < 0).sum()); row["regressions_over_0_1"] += int((delta < -.1).sum())
            row["pages"].append({"page": item["page"], "mean_iou": float(values.mean()),
                                 "recall_iou50": float((values >= .5).sum() / len(ref)),
                                 "recall_iou80": float((values >= .8).sum() / len(ref)),
                                 "accepted": accepted_count})
    for row in methods.values():
        row["mean_iou"] = float(np.mean(row.pop("values")))
        row["recall_iou50"] = row.pop("matches50") / row["reference"]
        row["recall_iou80"] = row.pop("matches80") / row["reference"]
    return {"scope": "full-page predicted lines/native words; consumed", "methods": methods}


def main():
    datasets = {name: oracle_dataset(name) for name in ("french-word-gt-a28", "word-transfer-a34")}
    datasets.update({name: predicted_dataset(name) for name in ("predicted-lines-a36", "predicted-lines-a37")})
    all_better = all(d["methods"]["contained"]["mean_iou"] >= d["methods"]["vertical"]["mean_iou"] and
                     d["methods"]["contained"]["recall_iou80"] >= d["methods"]["vertical"]["recall_iou80"]
                     for d in datasets.values())
    report = {"schema": "bbvlm.vertical-containment-a39/1", "status": "consumed_development_complete",
              "candidate": "accept A32 only when refined vertical interval is contained in native",
              "reference_inputs_in_router": False, "parameters": 0, "datasets": datasets,
              "consistent_noninferiority_gate": all_better,
              "decision": "freeze unchanged on new data" if all_better else "reject containment guard; retain A37 height router",
              "cost": {"new_vlm_passes": 0, "new_ocr_forwards": 0, "inputs": "cached predictions"},
              "accepted_for_project_completion_gate": False}
    EXP.mkdir(parents=True, exist_ok=True)
    (EXP / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
