"""A33 consumed-development evaluation of text-guided punctuation rescue."""
import json
from pathlib import Path
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw

import evaluate_french_holdout_a25 as core
from bbvlm.component_boxes import TEXT_RESCUE_PARAMETERS, refine_cells_text
from bbvlm.metrics import iou

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop"
SOURCE = BASE / "french-word-gt-a28"
OUT = BASE / "text-punctuation-a33"


def compact(metric):
    return {k: v for k, v in metric.items() if k != "per_line"}


def main():
    started = time.perf_counter()
    split = json.loads((SOURCE / "split.json").read_text())
    core.SOURCE = SOURCE / "source"
    rows, paths = core.load_rows(split)
    images = {p: cv2.imread(str(path), cv2.IMREAD_GRAYSCALE) for p, path in paths.items()}
    assert all(im is not None for im in images.values())
    frozen = [SOURCE / "output/boxes.json"] + [core.SOURCE / p[k] for p in split["pages"] for k in ("xml", "image")]
    before = {str(p.relative_to(ROOT)): core.sha(p) for p in frozen}
    old = json.loads((SOURCE / "output/boxes.json").read_text())
    a32 = json.loads((BASE / "component-boxes-a32/boxes.json").read_text())
    predictions = {"otsu": old["otsu"], "satellites": a32["satellites"]}
    seal = {"status": "consumed_development", "parameters": TEXT_RESCUE_PARAMETERS,
            "implementation_sha256": core.sha(ROOT / "src/bbvlm/component_boxes.py"),
            "evaluator_sha256": core.sha(Path(__file__)), "input_sha256": before}
    (OUT / "seal.json").write_text(json.dumps(seal, indent=2))
    diagnostics, times = {}, {}
    for name, leading in (("terminal", False), ("both_edges", True)):
        tick = time.perf_counter(); predictions[name] = {}; diagnostics[name] = {}
        for row in rows:
            forced = old["forced"][row["id"]]
            boxes, diag = refine_cells_text(images[row["page"]], row["line_bbox"], forced, leading=leading)
            predictions[name][row["id"]] = [{"text": w["text"], "bbox": b} for w, b in zip(forced, boxes)]
            diagnostics[name][row["id"]] = diag
        times[name] = time.perf_counter()-tick
    metrics = {name: core.box_metrics(rows, pred, name, True) for name, pred in predictions.items()}
    page_work = {p["page"]: p["work"] for p in split["pages"]}
    groups = {"page": {}, "work": {}}
    for kind, values in (("page", paths), ("work", split["works"])):
        for value in values:
            selected = [r for r in rows if (r["page"] if kind == "page" else page_work[r["page"]]) == value]
            groups[kind][value] = {name: compact(core.box_metrics(selected, pred, name, True)) for name,pred in predictions.items()}
    comparisons, changes = {}, []
    for name in ("terminal", "both_edges"):
        deltas = []; rescued = []
        for row in rows:
            lid = row["id"]
            assert [x["text"] for x in predictions[name][lid]] == [x["text"] for x in old["forced"][lid]]
            for wi, gt in enumerate(row["words"]):
                prior = predictions["satellites"][lid][wi]["bbox"]
                new = predictions[name][lid][wi]["bbox"]
                delta = float(iou(gt["bbox"], new)-iou(gt["bbox"], prior)); deltas.append(delta)
                if new != prior:
                    item = {"mode": name, "line": lid, "page": row["page"], "word_index": wi,
                            "text": gt["text"], "reference": gt["bbox"], "prior": prior, "candidate": new,
                            "old_iou": iou(gt["bbox"], prior), "new_iou": iou(gt["bbox"], new), "delta": delta}
                    rescued.append(item); changes.append(item)
        comparisons[name] = {"changed_words": len(rescued), "improved_words": sum(x>1e-9 for x in deltas),
                             "regressed_words": sum(x < -1e-9 for x in deltas),
                             "unchanged_words": sum(abs(x)<=1e-9 for x in deltas),
                             "mean_delta_iou": float(np.mean(deltas)),
                             "rescued_components": sum(len(d["rescues"]) for d in diagnostics[name].values())}
    # Every changed word, original pixels without contours plus prior/new/GT metadata.
    unique = [x for x in changes if x["mode"] == "both_edges"]
    tile_h = 115
    canvas = Image.new("RGB", (1100, max(1,len(unique))*tile_h), "white")
    draw = ImageDraw.Draw(canvas)
    for i,item in enumerate(unique):
        boxes=np.asarray([item[k] for k in ("reference","prior","candidate")])
        x0,y0=np.maximum(0,boxes[:,:2].min(0)-8).astype(int); x1,y1=(boxes[:,2:].max(0)+8).astype(int)
        crop=Image.fromarray(images[item["page"]][y0:y1,x0:x1]).convert("RGB")
        scale=min(3, 450/max(1,crop.width), 75/max(1,crop.height))
        crop=crop.resize((max(1,round(crop.width*scale)),max(1,round(crop.height*scale))))
        canvas.paste(crop,(5,i*tile_h+32))
        draw.text((5,i*tile_h+5),f'{item["line"]} #{item["word_index"]} {item["text"]}: {item["old_iou"]:.3f}->{item["new_iou"]:.3f}; prior {item["prior"]}; new {item["candidate"]}; GT {item["reference"]}',fill="black")
    canvas.save(OUT / "all-changes-clean.png")
    after = {str(p.relative_to(ROOT)): core.sha(p) for p in frozen}; assert before == after
    report = {"schema":"bbvlm.text-punctuation-a33/1","status":"consumed_development_completed",
              "scope":"Oracle line rectangles/text/token order; cached forced CTC; no end-to-end claim",
              "counts":{"pages":len(paths),"lines":len(rows),"words":sum(len(r["words"]) for r in rows)},
              "parameters":TEXT_RESCUE_PARAMETERS,"measurements":{k:compact(v) for k,v in metrics.items()},
              "by_group":groups,"paired_against_a32_satellites":comparisons,
              "cost":{"incremental_seconds":times,"total_evaluator_seconds":time.perf_counter()-started,
                      "new_vlm_passes":0,"new_recognizer_forwards":0,
                      "historical_prerequisite":"A28 cached recognition and CTC alignment remain required"},
              "invariants":{"originals_unchanged":before==after,"ids_text_token_counts_preserved":True,
                            "reference_boxes_hidden_from_refiner":True,"no_gt_replacement":True},
              "accepted_for_project_completion_gate":False}
    for name,value in (("boxes.json",predictions),("diagnostics.json",diagnostics),("changes.json",changes),
                       ("per-line.json",metrics),("report.json",report)):
        (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2))
    print(json.dumps({"measurements":report["measurements"],"paired":comparisons,"cost":report["cost"]},indent=2))


if __name__ == "__main__": main()
