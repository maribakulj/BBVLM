"""A23: diagnostic PERO CTC fallback on the already-consumed A22 reserve."""
from __future__ import annotations

from collections import defaultdict
import configparser
import hashlib
import json
from pathlib import Path
import re
import time
import unicodedata

import cv2
import numpy as np
from lxml import etree as E
from scipy.optimize import linear_sum_assignment

from bbvlm.gap_alignment import locate_words_without_recognizer
from bbvlm.metrics import edit_distance, iou
from bbvlm.pero import bind_native_alto_ids, load_cache, save_cache, realign
from ink import line_mask, vertical_extent

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop"
A22 = BASE / "reserve-a22"
SOURCE = BASE / "reference-a18/source"
OUT = BASE / "ctc-fallback-a23"
MODEL = ROOT / "models/pero/pero_eu_cz_print_newspapers_2022-09-26"
MODEL_SHA = "cb38dd0792c7145b8ba4dd64df255980e4633f4ca1d406f7f230b9c174c0c70d"
FAST_CONFIG = {"min_gap_height_ratio": .10, "gap_separation_ratio": 1.5}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pts(text: str) -> np.ndarray:
    return np.asarray([list(map(float, p.split(","))) for p in text.split()], dtype=float)


def make_proxy(text: str, alphabet: set[str]) -> tuple[str, list[dict]]:
    text = unicodedata.normalize("NFC", text)
    output, changes = [], []
    punctuation = {"‐": "-", "‑": "-", "‒": "-", "−": "-", "⸗": "-"}
    for char in text:
        if char in alphabet:
            output.append(char); continue
        candidates = punctuation.get(char)
        if candidates is None:
            candidates = "".join(c for c in unicodedata.normalize("NFKD", char)
                                 if not unicodedata.combining(c))
        if not candidates or any(c not in alphabet for c in candidates):
            candidates = "�"
        changes.append({"from": char, "to": candidates,
                        "name": unicodedata.name(char, "UNKNOWN")})
        output.append(candidates)
    proxy = "".join(output)
    if len(proxy.split()) != len(text.split()) or any(c not in alphabet for c in proxy):
        raise ValueError("proxy changed whitespace tokens or retained unsupported character")
    return proxy, changes


def alto_rows(xml: bytes, line_ids: set[str]) -> dict[str, list[dict]]:
    root = E.fromstring(xml, E.XMLParser(resolve_entities=False, no_network=True))
    out = {}
    for line in root.xpath('.//*[local-name()="TextLine"]'):
        lid = line.get("ID")
        if lid not in line_ids:
            continue
        values = []
        for word in line.xpath('./*[local-name()="String"]'):
            x, y = int(word.get("HPOS")), int(word.get("VPOS"))
            w, h = int(word.get("WIDTH")), int(word.get("HEIGHT"))
            values.append({"text": word.get("CONTENT", ""), "bbox": [x, y, x+w, y+h]})
        out[lid] = values
    if set(out) != line_ids:
        raise ValueError("ALTO missing line IDs")
    return out


def ink_spans(gray: np.ndarray, line_bbox, boxes: list[list[int]]) -> list[list[int]]:
    if len(boxes) <= 1:
        return boxes
    mask, ox, oy = line_mask(gray, [int(v) for v in line_bbox])
    if mask.size <= 1:
        return boxes
    occ = (mask > 0).any(axis=0)
    x0, _, x1, _ = map(int, line_bbox)
    separators = [x0]
    for left, right in zip(boxes, boxes[1:]):
        separators.append(int(round((left[2] + right[0]) / 2)))
    separators.append(x1)
    output = []
    for i, original in enumerate(boxes):
        a = max(0, separators[i] - ox)
        b = min(len(occ)-1, separators[i+1] - ox)
        if b < a:
            output.append(original); continue
        nz = np.flatnonzero(occ[a:b+1])
        if not len(nz):
            output.append(original); continue
        xa, xb = a + int(nz.min()), a + int(nz.max())
        ya, yb = vertical_extent(mask, xa, xb)
        output.append([ox+xa, oy+ya, ox+xb+1, oy+yb+1])
    return output


def metrics(rows: list[dict], predicted: dict[str, list[dict]], label: str) -> dict:
    pairs, per_line = [], []
    gt_total = pred_total = 0
    for row in rows:
        gt = [w["bbox"] for w in row["words"]]
        pr = [w["bbox"] for w in predicted.get(row["id"], [])]
        gt_total += len(gt); pred_total += len(pr)
        scores = []
        if gt and pr:
            matrix = np.asarray([[iou(a, b) for b in gt] for a in pr])
            aa, bb = linear_sum_assignment(-matrix)
            scores = [float(matrix[a, b]) for a, b in zip(aa, bb)]
            pairs.extend(scores)
        per_line.append({"id": row["id"], "reference_words": len(gt),
                         "predicted_words": len(pr), "matched_ious": scores})
    at50 = sum(v >= .5 for v in pairs); at80 = sum(v >= .8 for v in pairs)
    return {"method": label, "reference_words": gt_total, "predicted_words": pred_total,
            "matched_pairs": len(pairs), "mean_iou_matched": float(np.mean(pairs)) if pairs else None,
            "matches_iou50": at50, "precision_iou50": at50/pred_total if pred_total else None,
            "recall_iou50": at50/gt_total if gt_total else None,
            "matches_iou80": at80, "precision_iou80": at80/pred_total if pred_total else None,
            "recall_iou80": at80/gt_total if gt_total else None,
            "lines_all_words_iou80": sum(r["predicted_words"] == r["reference_words"] and
                                           len(r["matched_ious"]) == r["reference_words"] and
                                           all(v >= .8 for v in r["matched_ious"]) for r in per_line),
            "per_line": per_line}


def native_cer(rows: list[dict], native: dict[str, list[dict]]) -> dict:
    chars = edits = 0
    values = []
    for row in rows:
        ref = row["text"]
        hyp = " ".join(w["text"] for w in native[row["id"]])
        e = edit_distance(ref, hyp); chars += len(ref); edits += e
        values.append({"id": row["id"], "reference": ref, "hypothesis": hyp, "edits": e})
    return {"characters": chars, "edits": edits, "cer_strict": edits/chars, "per_line": values}


def build_layout(work: str, rows: list[dict]):
    from pero_ocr.core.layout import PageLayout, RegionLayout, TextLine
    image_path = SOURCE / rows[0]["source_image"]
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(image_path)
    layout = PageLayout(id="A23_" + re.sub(r"[^A-Za-z0-9_.-]", "_", work),
                        page_size=image.shape[:2])
    all_boxes = np.asarray([r["line_bbox"] for r in rows], dtype=float)
    lo = all_boxes[:, :2].min(axis=0); hi = all_boxes[:, 2:].max(axis=0)
    region = RegionLayout("REG_" + layout.id, np.asarray([[lo[0], lo[1]], [hi[0], lo[1]],
                                                           [hi[0], hi[1]], [lo[0], hi[1]]]))
    for row in rows:
        x0, y0, x1, y1 = row["line_bbox"]
        h = max(2., y1-y0); base_y = y0 + .8*h
        baseline = np.asarray([[x0, base_y], [x1, base_y]], dtype=float)
        region.lines.append(TextLine(id=row["id"], baseline=baseline,
                           polygon=np.asarray(row["polygon"], dtype=float),
                           heights=np.asarray([.8*h, .2*h], dtype=float)))
    layout.regions.append(region)
    return image, layout


def main():
    started = time.perf_counter(); OUT.mkdir(parents=True, exist_ok=True)
    protocol = OUT / "PROTOCOL.md"
    rows = json.loads((A22 / "private-reference.json").read_text())
    response = json.loads((A22 / "sol-response.json").read_text())
    sol = {r["id"]: r["text"] for r in response["lines"]}
    assert set(sol) == {r["id"] for r in rows}
    protected = [protocol, A22/"private-reference.json", A22/"sol-response.json", A22/"report.json"]
    protected += sorted({SOURCE/r["source_image"] for r in rows})
    before = {str(p.relative_to(ROOT)): sha(p) for p in protected}
    by_work = defaultdict(list)
    for row in rows: by_work[row["work"]].append(row)

    import torch
    from pero_ocr.document_ocr.page_parser import PageParser
    torch.set_num_threads(4)
    config = configparser.ConfigParser(); config.read(MODEL/"config_cpu.ini")
    config["PAGE_PARSER"]["RUN_LAYOUT_PARSER"] = "no"
    tic = time.perf_counter()
    parser = PageParser(config, device=torch.device("cpu"), config_path=str(MODEL))
    load_seconds = time.perf_counter()-tic
    recognition_seconds = 0.; cache_paths = {}
    native, forced, ink = {}, {}, {}
    proxy_report = {}; align_seconds = 0.
    image_by_work = {}
    for work, group in by_work.items():
        cache = OUT / "recognition" / work
        if not (cache/"cache.json").exists():
            image, layout = build_layout(work, group)
            tic = time.perf_counter(); layout = parser.process_page(image, layout)
            recognition_seconds += time.perf_counter()-tic
            save_cache(layout, cache, "PERO 0.7.0 eu/cz newspapers 2022-09-26; oracle A22 lines")
        layout, _ = load_cache(cache)
        image_by_work[work] = cv2.imread(str(SOURCE/group[0]["source_image"]), cv2.IMREAD_GRAYSCALE)
        native_xml = layout.to_altoxml_string()
        if isinstance(native_xml, str): native_xml = native_xml.encode()
        native_xml = bind_native_alto_ids(native_xml, layout.regions)
        (OUT/f"native-{work}.alto.xml").write_bytes(native_xml)
        native.update(alto_rows(native_xml, {r["id"] for r in group}))
        proxies = {}; changes = {}
        for line in layout.lines_iterator():
            alphabet = set(line.characters[:-1])
            proxies[line.id], changes[line.id] = make_proxy(sol[line.id], alphabet)
        if any(len(proxies[k].split()) != len(sol[k].split()) for k in proxies):
            raise ValueError("proxy token mismatch")
        tic = time.perf_counter(); forced_xml, alignment = realign(layout, proxies)
        align_seconds += time.perf_counter()-tic
        (OUT/f"forced-{work}.alto.xml").write_bytes(forced_xml)
        work_forced = alto_rows(forced_xml, {r["id"] for r in group})
        for row in group:
            lid = row["id"]
            if len(work_forced[lid]) != len(sol[lid].split()):
                raise ValueError("forced word count differs from Sol tokens: "+lid)
            forced[lid] = [{"text": token, "bbox": w["bbox"]}
                           for token, w in zip(sol[lid].split(), work_forced[lid])]
            boxes = ink_spans(image_by_work[work], row["line_bbox"],
                              [w["bbox"] for w in work_forced[lid]])
            ink[lid] = [{"text": token, "bbox": box}
                        for token, box in zip(sol[lid].split(), boxes)]
        proxy_report.update({lid: {"final": sol[lid], "proxy": proxies[lid],
                                   "changes": changes[lid]} for lid in proxies})
        cache_paths[work] = str(cache.relative_to(ROOT))

    fast = {}; hybrid = {}
    for row in rows:
        gray = image_by_work[row["work"]]
        proposal = locate_words_without_recognizer(gray, row["polygon"], row["line_bbox"],
                                                    sol[row["id"]].split(), **FAST_CONFIG)
        fast[row["id"]] = [{"text": t, "bbox": b} for t, b in
                            zip(sol[row["id"]].split(), proposal["boxes"])]
        hybrid[row["id"]] = fast[row["id"]] or ink[row["id"]]
    measurements = {"pero_native": metrics(rows, native, "pero_native_ocr_boxes"),
                    "vlm_forced_ctc": metrics(rows, forced, "vlm_text_forced_pero_ctc"),
                    "vlm_forced_ctc_ink": metrics(rows, ink, "forced_ctc_separators_plus_ink"),
                    "hybrid": metrics(rows, hybrid, "a19_fast_else_forced_ctc_ink")}
    report = {"schema": "bbvlm.ctc-fallback-a23/1",
      "scope": "post-hoc diagnostic on 16 consumed A22 lines; oracle line polygons",
      "model": {"package": "pero-ocr==0.7.0", "weights": MODEL.name,
                "archive_sha256": MODEL_SHA, "torch": torch.__version__, "device": "cpu",
                "threads": 4},
      "cost": {"model_load_seconds": load_seconds, "recognition_seconds": recognition_seconds,
               "recognized_lines": len(rows), "recognizer_forwards": len(rows),
               "forced_alignment_seconds": align_seconds, "new_vlm_tasks": 0,
               "total_wall_seconds": time.perf_counter()-started},
      "native_ocr": native_cer(rows, native), "proxy": proxy_report,
      "measurements": measurements, "cache_paths": cache_paths,
      "invariants": {"protocol_frozen_before_run": True, "final_sol_text_unchanged": True,
                     "all_forced_word_counts_equal_sol_tokens": True,
                     "protected_inputs_unchanged": before == {str(p.relative_to(ROOT)): sha(p) for p in protected}},
      "reference_status": "external SBB GT, provider+SBB post-correction/manual page inspection; not perfect adjudicated truth",
      "limitations": ["A22 was opened and scored previously, so this cannot be an independent validation",
        "line polygons and token counts are oracle-conditional", "proxy text guides geometry only and is not output",
        "one-to-one geometry matching does not certify word identity", "synthetic horizontal baselines may disadvantage PERO"],
      "accepted_for_project_completion_gate": False,
      "protected_input_sha256": before}
    (OUT/"final-transcriptions.json").write_text(json.dumps(sol, ensure_ascii=False, indent=2)+"\n")
    (OUT/"boxes.json").write_text(json.dumps({"native": native, "forced": forced, "ink": ink,
                                               "fast": fast, "hybrid": hybrid}, ensure_ascii=False, indent=2)+"\n")
    (OUT/"report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({"cost": report["cost"], "native_ocr": {k:v for k,v in report["native_ocr"].items() if k != "per_line"},
                      "measurements": {k:{a:b for a,b in v.items() if a != "per_line"}
                                       for k,v in measurements.items()}}, indent=2))


if __name__ == "__main__": main()
