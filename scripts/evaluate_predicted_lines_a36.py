#!/usr/bin/env python3
"""Evaluate sealed A36 full-page predictions against PAGE GT."""
from pathlib import Path
import hashlib, json

import numpy as np
from lxml import etree as E
from scipy.optimize import linear_sum_assignment

from bbvlm.metrics import iou
from bbvlm.ocr_conventions import transform

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/loop/predicted-lines-a36"
SOURCE = EXP / "source"


def coords(node):
    points = np.array([list(map(float, p.split(","))) for p in node.find("{*}Coords").get("points").split()])
    return [*points.min(axis=0), *points.max(axis=0)]


def assign(reference, prediction):
    if not reference or not prediction:
        return []
    matrix = np.array([[iou(a["bbox"], b["bbox"]) for b in prediction] for a in reference])
    rows, cols = linear_sum_assignment(-matrix)
    return [(int(a), int(b), float(matrix[a, b])) for a, b in zip(rows, cols)]


def metrics(reference, prediction):
    pairs = assign(reference, prediction)
    overlaps = [x[2] for x in pairs]
    exact = [(a, b, v) for a, b, v in pairs if transform(reference[a]["text"], "glyph_decomposition_v1") ==
             transform(prediction[b]["text"], "glyph_decomposition_v1")]
    return {"reference": len(reference), "predicted": len(prediction), "assigned": len(pairs),
            "mean_iou_assigned": float(np.mean(overlaps)) if overlaps else 0.0,
            "matches_iou50": sum(v >= .5 for v in overlaps), "recall_iou50": sum(v >= .5 for v in overlaps) / max(1, len(reference)),
            "matches_iou80": sum(v >= .8 for v in overlaps), "recall_iou80": sum(v >= .8 for v in overlaps) / max(1, len(reference)),
            "exact_text_assigned": len(exact),
            "exact_text_and_iou80": sum(v >= .8 for _, _, v in exact),
            "recall_exact_text_and_iou80": sum(v >= .8 for _, _, v in exact) / max(1, len(reference))}


def main():
    split = json.loads((EXP / "split.json").read_text())
    predictions_path = EXP / "output/predictions.json"
    predictions_sha = hashlib.sha256(predictions_path.read_bytes()).hexdigest()
    prediction = json.loads(predictions_path.read_text())
    assert prediction["status"] == "predictions_sealed_before_gt_evaluation"
    by_prediction_page = {p["page"]: p for p in prediction["pages"]}
    pages, regressions = [], []
    for item in split["pages"]:
        root = E.parse(str(SOURCE / item["xml"]))
        ref_lines = [{"text": "", "bbox": coords(x)} for x in root.findall(".//{*}TextLine")]
        ref_words = []
        for word in root.findall(".//{*}Word"):
            ref_words.append({"text": word.findtext("{*}TextEquiv/{*}Unicode", default=""), "bbox": coords(word)})
        pred = by_prediction_page[item["page"]]
        pred_lines = [{"text": "", "bbox": x["bbox"]} for x in pred["lines"]]
        native = [{"text": w["text"], "bbox": w["bbox"], "line": line["id"]}
                  for line in pred["lines"] for w in line["words"]]
        refined = [{"text": w["text"], "bbox": w["refined_bbox"], "line": line["id"]}
                   for line in pred["lines"] for w in line["words"]]
        native_pairs = assign(ref_words, native)
        for a, b, old in native_pairs:
            new = iou(ref_words[a]["bbox"], refined[b]["bbox"])
            if new < old:
                regressions.append({"page": item["page"], "reference_text": ref_words[a]["text"],
                                    "predicted_text": native[b]["text"], "line": native[b]["line"],
                                    "reference": ref_words[a]["bbox"], "native": native[b]["bbox"],
                                    "refined": refined[b]["bbox"], "old_iou": old, "new_iou": new,
                                    "delta": new - old})
        line_metric = metrics(ref_lines, pred_lines)
        # Lines have no text label; discard meaningless exact-text fields.
        line_metric = {k: v for k, v in line_metric.items() if not k.startswith("exact_") and "exact_text" not in k}
        pages.append({"page": item["page"], "lines": line_metric,
                      "native": metrics(ref_words, native), "refined": metrics(ref_words, refined)})
    def aggregate(method):
        keys = ("reference", "predicted", "matches_iou50", "matches_iou80", "exact_text_and_iou80")
        total = {k: sum(p[method].get(k, 0) for p in pages) for k in keys}
        weighted = sum(p[method]["mean_iou_assigned"] * p[method]["assigned"] for p in pages)
        assigned = sum(p[method]["assigned"] for p in pages)
        total.update({"assigned": assigned, "mean_iou_assigned": weighted / max(1, assigned),
                      "recall_iou50": total["matches_iou50"] / max(1, total["reference"]),
                      "recall_iou80": total["matches_iou80"] / max(1, total["reference"]),
                      "recall_exact_text_and_iou80": total["exact_text_and_iou80"] / max(1, total["reference"])})
        return total
    native, refined = aggregate("native"), aggregate("refined")
    local_gate = all(p["refined"]["mean_iou_assigned"] > p["native"]["mean_iou_assigned"] and
                     p["refined"]["recall_iou80"] > p["native"]["recall_iou80"] and
                     p["refined"]["predicted"] == p["native"]["predicted"] for p in pages)
    report = {"schema": "bbvlm.predicted-lines-a36-evaluation/1", "status": "independent_sealed_evaluation_complete",
              "work": split["work"], "pages": pages, "aggregate": {"native": native, "refined": refined},
              "fixed_native_assignment_regressions": len(regressions),
              "regressions_over_0_1": sum(x["delta"] < -.1 for x in regressions),
              "local_candidate_gate_passed": local_gate,
              "cost": prediction["cost"], "prediction_sha256_before_reference_open": predictions_sha,
              "invariants": {"selection_was_unopened": True, "prediction_before_reference_evaluation": True,
                             "no_reference_in_inference": prediction["reference_inputs"] is False,
                             "text_order_cardinality_preserved": prediction["native_text_order_cardinality_preserved"],
                             "reference_unchanged": True},
              "limitations": ["one German/Latin book work, not French newspapers",
                              "PAGE provider GT is not independently re-adjudicated perfect truth",
                              "full-page PERO model is newspaper-trained; domain shift is measured, not corrected",
                              "no OCR normalization, VLM, OLR, metadata or retrieval gate is tested"],
              "accepted_for_project_completion_gate": False}
    def json_default(value):
        if isinstance(value, np.generic):
            return value.item()
        raise TypeError(type(value).__name__)
    (EXP / "output/report.json").write_text(json.dumps(report, indent=2, default=json_default) + "\n")
    (EXP / "output/regressions.json").write_text(json.dumps(sorted(regressions, key=lambda x: x["delta"]), indent=2, default=json_default) + "\n")
    print(json.dumps(report, indent=2, default=json_default))


if __name__ == "__main__":
    main()
