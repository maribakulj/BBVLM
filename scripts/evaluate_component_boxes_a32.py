"""Consumed A28 component ablation; cached recognition, fresh CPU refinement."""
import hashlib
import json
from pathlib import Path
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw

import evaluate_french_holdout_a25 as core
from bbvlm.component_boxes import PARAMETERS, refine_cells
from bbvlm.metrics import iou

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop"
SOURCE = BASE / "french-word-gt-a28"
OUT = BASE / "component-boxes-a32"


def compact(metric):
    return {k: v for k, v in metric.items() if k != "per_line"}


def main():
    started = time.perf_counter()
    split = json.loads((SOURCE / "split.json").read_text())
    core.SOURCE = SOURCE / "source"
    rows, paths = core.load_rows(split)
    images = {p: cv2.imread(str(path), cv2.IMREAD_GRAYSCALE) for p, path in paths.items()}
    assert all(im is not None for im in images.values())
    frozen_paths = [SOURCE / "output/boxes.json"] + [core.SOURCE / p[k] for p in split["pages"] for k in ("xml", "image")]
    before = {str(p.relative_to(ROOT)): core.sha(p) for p in frozen_paths}
    predictions = json.loads((SOURCE / "output/boxes.json").read_text())
    times, diagnostics = {}, {}
    # Record implementation and parameters before scoring; source data already consumed.
    seal = {"status": "consumed_development", "parameters": PARAMETERS,
            "implementation_sha256": core.sha(ROOT / "src/bbvlm/component_boxes.py"),
            "evaluator_sha256": core.sha(Path(__file__)), "input_sha256": before}
    (OUT / "seal.json").write_text(json.dumps(seal, indent=2))
    for mode in ("area", "body", "satellites"):
        tick = time.perf_counter()
        predictions[mode], diagnostics[mode] = {}, {}
        for row in rows:
            forced = predictions["forced"][row["id"]]
            boxes, diag = refine_cells(images[row["page"]], row["line_bbox"], [w["bbox"] for w in forced], mode)
            predictions[mode][row["id"]] = [{"text": w["text"], "bbox": b} for w, b in zip(forced, boxes)]
            diagnostics[mode][row["id"]] = diag
        times[mode] = time.perf_counter()-tick
    measurements = {name: core.box_metrics(rows, pred, name, name != "native") for name, pred in predictions.items()}
    page_work = {p["page"]: p["work"] for p in split["pages"]}
    grouped = {}
    for category, values in (("page", paths), ("work", split["works"])):
        grouped[category] = {}
        for value in values:
            group = [r for r in rows if (r["page"] if category == "page" else page_work[r["page"]]) == value]
            grouped[category][value] = {name: compact(core.box_metrics(group, pred, name, name != "native")) for name, pred in predictions.items()}
    paired, cases = {}, []
    for mode in ("area", "body", "satellites"):
        delta = []
        for row in rows:
            lid = row["id"]
            assert len(row["words"]) == len(predictions[mode][lid]) == len(predictions["forced"][lid])
            assert [w["text"] for w in predictions[mode][lid]] == [w["text"] for w in predictions["forced"][lid]]
            for idx, word in enumerate(row["words"]):
                raw = predictions["otsu"][lid][idx]["bbox"]
                candidate = predictions[mode][lid][idx]["bbox"]
                old, new = iou(word["bbox"], raw), iou(word["bbox"], candidate)
                change = float(new-old)
                delta.append(change)
                if mode == "satellites":
                    cases.append({"line": lid, "page": row["page"], "word_index": idx,
                                  "text": word["text"], "reference": word["bbox"],
                                  "raw": raw, "candidate": candidate, "old_iou": old,
                                  "new_iou": new, "delta": change})
        paired[mode] = {"improved_words": sum(x > 1e-9 for x in delta),
                        "regressed_words": sum(x < -1e-9 for x in delta),
                        "unchanged_words": sum(abs(x) <= 1e-9 for x in delta),
                        "mean_delta_iou": float(np.mean(delta)),
                        "regressions_over_0_1": sum(x < -.1 for x in delta),
                        "fallback_cells": sum(d["fallback_cells"] for d in diagnostics[mode].values())}
    extremes = sorted(cases, key=lambda r: r["delta"])[:12] + sorted(cases, key=lambda r: -r["delta"])[:12]
    canvas = Image.new("RGB", (1000, 130*len(extremes)), "white")
    draw = ImageDraw.Draw(canvas)
    for i, case in enumerate(extremes):
        all_boxes = np.asarray([case[k] for k in ("reference", "raw", "candidate")])
        x0, y0 = np.maximum(0, all_boxes[:, :2].min(0)-8).astype(int)
        x1, y1 = (all_boxes[:, 2:].max(0)+8).astype(int)
        crop = Image.fromarray(images[case["page"]][y0:y1, x0:x1]).convert("RGB")
        cd = ImageDraw.Draw(crop)
        for key, color in (("reference", "green"), ("raw", "red"), ("candidate", "blue")):
            x, y, xx, yy = case[key]
            cd.rectangle([x-x0, y-y0, xx-x0-1, yy-y0-1], outline=color, width=1)
        scale = min(2, 990/crop.width, 95/crop.height)
        crop = crop.resize((max(1, round(crop.width*scale)), max(1, round(crop.height*scale))))
        canvas.paste(crop, (5, i*130+30))
        draw.text((5, i*130+5), f'{case["line"]} #{case["word_index"]}  IoU {case["old_iou"]:.3f} -> {case["new_iou"]:.3f} (green GT; red raw; blue component)', fill="black")
    canvas.save(OUT / "extremes.jpg", quality=90)
    after = {str(p.relative_to(ROOT)): core.sha(p) for p in frozen_paths}
    assert before == after
    result = {"schema": "bbvlm.component-boxes-a32/1", "status": "consumed_development_completed",
              "scope": "Oracle line rectangles/text/token order; cached forced CTC, synthetic baseline; no end-to-end claim",
              "counts": {"pages": len(paths), "lines": len(rows), "words": sum(len(r["words"]) for r in rows)},
              "parameters": PARAMETERS, "measurements": {k: compact(v) for k, v in measurements.items()},
              "by_group": grouped, "paired_against_raw_otsu": paired,
              "cost": {"incremental_refinement_seconds": times, "total_evaluator_seconds": time.perf_counter()-started,
                       "new_vlm_passes": 0, "new_recognizer_forwards": 0,
                       "cached_A28_recognition_seconds": 36.336, "cached_A28_alignment_seconds": 2.5516,
                       "note": "Cached recognition is a historical prerequisite, not a free end-to-end system."},
              "invariants": {"originals_unchanged": before == after, "ids_and_token_text_preserved": True,
                             "no_reference_word_boxes_in_refiner": True, "no_gt_replacement": True},
              "accepted_for_project_completion_gate": False}
    for name, value in (("boxes.json", predictions), ("diagnostics.json", diagnostics),
                        ("extremes.json", extremes), ("per-line.json", measurements), ("report.json", result)):
        (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2))
    print(json.dumps({"measurements": result["measurements"], "paired": paired, "cost": result["cost"]}, indent=2))


if __name__ == "__main__":
    main()
