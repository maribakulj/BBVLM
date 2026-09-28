#!/usr/bin/env python3
"""A55b development grid for a reference-free horizontal expansion guard."""
from __future__ import annotations

import json
from pathlib import Path
import statistics

from diagnose_bnl_geometry_a55 import iou


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/loop/bnl-geometry-a55"
CEILINGS = (1.00, 1.02, 1.05, 1.10, 1.20)


def route(native: list[float], refined: list[float], ceiling: float) -> list[float]:
    nh, rh = native[3] - native[1], refined[3] - refined[1]
    nw, rw = native[2] - native[0], refined[2] - refined[0]
    return refined if rh <= nh and rw <= ceiling * nw else native


def score(rows: list[dict], ceiling: float) -> dict:
    values = [iou(row["reference"], route(row["native"], row["refined"], ceiling))
              for row in rows]
    return {"words": len(values), "mean_iou": statistics.fmean(values),
            "recall_iou80": sum(v >= .8 for v in values) / len(values)}


def main() -> None:
    diag = json.loads((EXP / "report.json").read_text())
    matches = diag["matches"]
    predictions = json.loads((ROOT / "experiments/loop/bnl-independent-a54/output/predictions.json").read_text())
    # Resolve refined boxes by the immutable (block, line, word) traversal used
    # by the diagnostic. The same geometry order is reconstructed from texts
    # and native boxes, with duplicate-safe queues.
    lookup = {}
    for block in predictions["blocks"]:
        for line in block["lines"]:
            for word in line["words"]:
                key = (block["id"], tuple(word["bbox"]), word["text"])
                lookup.setdefault(key, []).append(word["refined_bbox"])
    for row in matches:
        key = (row["id"], tuple(row["native"]), row["predicted_text"])
        choices = lookup.get(key)
        if not choices:
            raise ValueError(f"unresolved refined box {key}")
        row["refined"] = choices[0]

    native_by_block = {}
    for identifier in {r["id"] for r in matches}:
        local = [r for r in matches if r["id"] == identifier]
        native_by_block[identifier] = statistics.fmean(iou(r["reference"], r["native"]) for r in local)

    candidates = []
    for ceiling in CEILINGS:
        french = [r for r in matches if r["language"] == "fr"]
        per_french = {}
        for identifier in {r["id"] for r in french}:
            local = [r for r in french if r["id"] == identifier]
            per_french[identifier] = score(local, ceiling)["mean_iou"]
        all_score, french_score = score(matches, ceiling), score(french, ceiling)
        eligible = (french_score["mean_iou"] >= diag["aggregate"]["french"]["native"]["mean_iou"]
                    and all(per_french[k] >= native_by_block[k] - .01 for k in per_french))
        candidates.append({"ceiling": ceiling, "all": all_score, "french": french_score,
                           "per_french_mean_iou": per_french, "eligible": eligible})
    eligible = [c for c in candidates if c["eligible"]]
    selected = max(eligible, key=lambda c: c["all"]["mean_iou"]) if eligible else None
    report = {"schema": "bbvlm.width-guard-a55/1", "status": "development_complete",
              "consumed_input": "A54", "candidates": candidates, "selected": selected,
              "promotion_allowed": False,
              "next": "freeze unseen BnL blocks and evaluate selected ceiling without changes"}
    (EXP / "width-guard-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

