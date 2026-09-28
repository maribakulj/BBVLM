#!/usr/bin/env python3
"""A55: decompose A54 word-box edge errors without fitting parameters."""
from __future__ import annotations

import json
from pathlib import Path
import statistics
import xml.etree.ElementTree as ET

import numpy as np
from scipy.optimize import linear_sum_assignment


ROOT = Path(__file__).resolve().parents[1]
A54 = ROOT / "experiments/loop/bnl-independent-a54"
OUT = ROOT / "experiments/loop/bnl-geometry-a55"
NS = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}
SCALE = 300.0 / 254.0


def box(node: ET.Element) -> list[float]:
    x, y = float(node.attrib["HPOS"]), float(node.attrib["VPOS"])
    w, h = float(node.attrib["WIDTH"]), float(node.attrib["HEIGHT"])
    return [SCALE * v for v in (x, y, x + w, y + h)]


def iou(a: list[float], b: list[float]) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - inter
    return inter / union if union else 0.0


def axis_iou(a: list[float], b: list[float], axis: int) -> float:
    lo, hi = axis, axis + 2
    inter = max(0.0, min(a[hi], b[hi]) - max(a[lo], b[lo]))
    union = max(a[hi], b[hi]) - min(a[lo], b[lo])
    return inter / union if union else 0.0


def reference(identifier: str) -> list[dict]:
    root = ET.parse(A54 / "source" / f"{identifier}.xml").getroot()
    rows = []
    for line in root.findall(".//a:TextLine", NS):
        rows.append({
            "bbox": box(line),
            "words": [{"text": word.attrib.get("CONTENT", ""), "bbox": box(word)}
                      for word in line.findall("a:String", NS)],
        })
    return rows


def line_pairs(ref: list[dict], pred: list[dict]) -> list[tuple[dict, dict]]:
    matrix = np.asarray([[iou(a["bbox"], b["bbox"]) for b in pred] for a in ref])
    if not matrix.size:
        return []
    rr, pp = linear_sum_assignment(-matrix)
    return [(ref[r], pred[p]) for r, p in zip(rr, pp) if matrix[r, p] >= .1]


def word_pairs(ref: list[dict], pred: list[dict]) -> list[tuple[dict, dict]]:
    if len(ref) == len(pred):
        return list(zip(ref, pred))
    if not ref or not pred:
        return []
    matrix = np.asarray([[max(axis_iou(a["bbox"], b["bbox"], 0),
                               axis_iou(a["bbox"], b["routed_bbox"], 0))
                          for b in pred] for a in ref])
    rr, pp = linear_sum_assignment(-matrix)
    return [(ref[r], pred[p]) for r, p in zip(rr, pp) if matrix[r, p] >= .1]


def metrics(rows: list[dict], field: str) -> dict:
    values = []
    for row in rows:
        ref, pred = row["reference"], row[field]
        h = max(1e-9, ref[3] - ref[1])
        values.append({
            "iou": iou(ref, pred),
            "horizontal_iou": axis_iou(ref, pred, 0),
            "vertical_iou": axis_iou(ref, pred, 1),
            "left_error_h": (pred[0] - ref[0]) / h,
            "right_error_h": (pred[2] - ref[2]) / h,
            "top_error_h": (pred[1] - ref[1]) / h,
            "bottom_error_h": (pred[3] - ref[3]) / h,
            "width_ratio": (pred[2] - pred[0]) / max(1e-9, ref[2] - ref[0]),
            "height_ratio": (pred[3] - pred[1]) / h,
        })
    keys = [k for k in values[0] if k != "iou"] if values else []
    result = {
        "matched_words": len(values),
        "mean_iou": statistics.fmean(v["iou"] for v in values) if values else None,
        "recall_iou80_among_matched": sum(v["iou"] >= .8 for v in values) / len(values) if values else None,
    }
    for key in keys:
        sample = [v[key] for v in values]
        result[key] = {
            "mean": statistics.fmean(sample),
            "median": statistics.median(sample),
            "p10": float(np.quantile(sample, .1)),
            "p90": float(np.quantile(sample, .9)),
        }
    for edge in ("left_error_h", "right_error_h", "top_error_h", "bottom_error_h"):
        result[edge]["within_abs_0_10"] = sum(abs(v[edge]) <= .1 for v in values) / len(values) if values else None
    return result


def main() -> None:
    prediction = json.loads((A54 / "output/predictions.json").read_text())
    audit = json.loads((A54 / "audit.json").read_text())
    languages = {row["id"]: row["language_prediction"] for row in audit["rows"]}
    matches = []
    per_block = []
    for block in prediction["blocks"]:
        identifier = block["id"]
        local = []
        for rline, pline in line_pairs(reference(identifier), block["lines"]):
            for rword, pword in word_pairs(rline["words"], pline["words"]):
                row = {
                    "id": identifier,
                    "language": languages[identifier],
                    "reference_text": rword["text"],
                    "predicted_text": pword["text"],
                    "reference": rword["bbox"],
                    "native": pword["bbox"],
                    "refined": pword["refined_bbox"],
                    "routed": pword["routed_bbox"],
                }
                matches.append(row)
                local.append(row)
        per_block.append({"id": identifier, "language": languages[identifier],
                          "matches": len(local), "native": metrics(local, "native"),
                          "routed": metrics(local, "routed")})
    french = [row for row in matches if row["language"] == "fr"]
    report = {
        "schema": "bbvlm.bnl-geometry-a55/1",
        "status": "consumed_set_diagnostic_complete",
        "reference_status": "provider word rectangles; not certified as manually adjudicated perfect boxes",
        "coordinate_scale": SCALE,
        "aggregate": {
            "all": {"native": metrics(matches, "native"), "routed": metrics(matches, "routed")},
            "french": {"native": metrics(french, "native"), "routed": metrics(french, "routed")},
        },
        "per_block": per_block,
        "matches": matches,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    compact = dict(report)
    compact.pop("matches")
    print(json.dumps(compact, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
