"""A25: pre-registered CTC/Otsu box diagnostic on a new SBB work.

The pages were opened before this implementation was sealed.  The report
therefore records the experiment as implementation-at-risk and never promotes
it to the project completion gate.
"""
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

from bbvlm.metrics import edit_distance, iou
from bbvlm.ocr_conventions import private_use_inventory, transform
from bbvlm.pero import bind_native_alto_ids, load_cache, realign, save_cache


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "loop" / "french-holdout-a25"
SOURCE = EXP / "source"
OUT = EXP / "output"
MODEL = ROOT / "models/pero/pero_eu_cz_print_newspapers_2022-09-26"
MODEL_SHA = "cb38dd0792c7145b8ba4dd64df255980e4633f4ca1d406f7f230b9c174c0c70d"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def points(value: str) -> np.ndarray:
    return np.asarray([list(map(float, p.split(","))) for p in value.split()], dtype=float)


def bbox(poly: np.ndarray) -> list[int]:
    lo, hi = np.floor(poly.min(0)), np.ceil(poly.max(0))
    return [int(lo[0]), int(lo[1]), int(hi[0]), int(hi[1])]


def unicode_text(node) -> str:
    return "".join(node.xpath('./*[local-name()="TextEquiv"][1]/*[local-name()="Unicode"]/text()'))


def load_rows(split: dict) -> tuple[list[dict], dict[str, Path]]:
    rows, images = [], {}
    for page in split["pages"]:
        xml_path = SOURCE / page["xml"]
        image_path = SOURCE / page["image"]
        tree = E.parse(str(xml_path), E.XMLParser(resolve_entities=False, no_network=True))
        page_id = page["page"]
        images[page_id] = image_path
        for line in tree.xpath('//*[local-name()="TextLine"]'):
            coords = line.xpath('./*[local-name()="Coords"]')
            words = line.xpath('./*[local-name()="Word"]')
            text = unicode_text(line)
            if not coords or not words or not text.strip():
                continue
            word_rows = []
            for word in words:
                wcoords = word.xpath('./*[local-name()="Coords"]')
                if not wcoords:
                    continue
                word_rows.append({"text": unicode_text(word), "bbox": bbox(points(wcoords[0].get("points")))})
            if not word_rows:
                continue
            if text.strip() != " ".join(w["text"] for w in word_rows).strip():
                raise ValueError(f"line/word text mismatch: {page_id}/{line.get('id')}")
            poly = points(coords[0].get("points"))
            internal = f"P{page_id}_{line.get('id')}"
            rows.append({"id": internal, "source_id": line.get("id"), "page": page_id,
                         "text": text, "polygon": poly.tolist(), "line_bbox": bbox(poly),
                         "words": word_rows})
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("duplicate internal line IDs")
    return rows, images


def make_proxy(text: str, alphabet: set[str]) -> tuple[str, list[dict]]:
    text = unicodedata.normalize("NFC", text)
    punctuation = {"‐": "-", "‑": "-", "‒": "-", "−": "-", "⸗": "-"}
    out, changes = [], []
    for char in text:
        if char in alphabet:
            out.append(char)
            continue
        candidate = punctuation.get(char)
        if candidate is None:
            candidate = "".join(c for c in unicodedata.normalize("NFKD", char)
                                if not unicodedata.combining(c))
        if not candidate or any(c not in alphabet for c in candidate):
            candidate = "�"
        changes.append({"from": char, "to": candidate,
                        "name": unicodedata.name(char, "UNKNOWN")})
        out.append(candidate)
    proxy = "".join(out)
    if len(proxy.split()) != len(text.split()) or any(c not in alphabet for c in proxy):
        raise ValueError("proxy changed token count or retained unsupported characters")
    return proxy, changes


def alto_rows(xml: bytes, ids: set[str]) -> dict[str, list[dict]]:
    root = E.fromstring(xml, E.XMLParser(resolve_entities=False, no_network=True))
    result = {}
    for line in root.xpath('.//*[local-name()="TextLine"]'):
        lid = line.get("ID")
        if lid not in ids:
            continue
        values = []
        for word in line.xpath('./*[local-name()="String"]'):
            x, y = int(word.get("HPOS")), int(word.get("VPOS"))
            w, h = int(word.get("WIDTH")), int(word.get("HEIGHT"))
            values.append({"text": word.get("CONTENT", ""), "bbox": [x, y, x+w, y+h]})
        result[lid] = values
    if set(result) != ids:
        raise ValueError("ALTO line ID mismatch")
    return result


def raw_otsu_boxes(gray: np.ndarray, line_bbox: list[int], forced: list[list[int]]) -> list[list[int]]:
    """Literal frozen A25 rule: one Otsu threshold per source line rectangle."""
    x0, y0, x1, y1 = line_bbox
    crop = gray[y0:y1, x0:x1]
    if crop.size == 0:
        return forced
    _, ink = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    occupied = (ink > 0).any(axis=0)
    separators = [x0]
    for left, right in zip(forced, forced[1:]):
        separators.append(int(round((left[2] + right[0]) / 2)))
    separators.append(x1)
    output = []
    for index, original in enumerate(forced):
        a = max(0, separators[index] - x0)
        b = min(occupied.size, separators[index+1] - x0)
        if b <= a:
            output.append(original)
            continue
        xs = np.flatnonzero(occupied[a:b])
        if not len(xs):
            output.append(original)
            continue
        xa, xb = a + int(xs.min()), a + int(xs.max()) + 1
        ys = np.flatnonzero((ink[:, xa:xb] > 0).any(axis=1))
        if not len(ys):
            output.append(original)
            continue
        output.append([x0+xa, y0+int(ys.min()), x0+xb, y0+int(ys.max())+1])
    return output


def build_layout(page: str, rows: list[dict], image_path: Path):
    from pero_ocr.core.layout import PageLayout, RegionLayout, TextLine
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(image_path)
    layout = PageLayout(id=f"A25_{page}", page_size=image.shape[:2])
    all_boxes = np.asarray([r["line_bbox"] for r in rows], dtype=float)
    lo, hi = all_boxes[:, :2].min(0), all_boxes[:, 2:].max(0)
    region = RegionLayout(f"REG_A25_{page}", np.asarray(
        [[lo[0], lo[1]], [hi[0], lo[1]], [hi[0], hi[1]], [lo[0], hi[1]]]))
    for row in rows:
        x0, y0, x1, y1 = row["line_bbox"]
        h = max(2.0, y1-y0)
        region.lines.append(TextLine(id=row["id"],
            baseline=np.asarray([[x0, y0+.8*h], [x1, y0+.8*h]], dtype=float),
            polygon=np.asarray(row["polygon"], dtype=float),
            heights=np.asarray([.8*h, .2*h], dtype=float)))
    layout.regions.append(region)
    return image, layout


def box_metrics(rows: list[dict], prediction: dict[str, list[dict]], label: str,
                index_aligned: bool) -> dict:
    gt_total = pred_total = 0
    scores, per_line = [], []
    x_errors, y_errors = [], []
    for row in rows:
        gt = [w["bbox"] for w in row["words"]]
        pr = [w["bbox"] for w in prediction.get(row["id"], [])]
        gt_total += len(gt); pred_total += len(pr)
        matched = []
        pairs = []
        if gt and pr:
            if index_aligned and len(gt) == len(pr):
                pairs = list(zip(range(len(gt)), range(len(pr))))
            elif not index_aligned:
                matrix = np.asarray([[iou(a, b) for b in pr] for a in gt])
                aa, bb = linear_sum_assignment(-matrix)
                pairs = list(zip(aa, bb))
            for gi, pi in pairs:
                matched.append(float(iou(gt[gi], pr[pi])))
                gw, gh = max(1, gt[gi][2]-gt[gi][0]), max(1, gt[gi][3]-gt[gi][1])
                x_errors.extend([abs(pr[pi][0]-gt[gi][0])/gw, abs(pr[pi][2]-gt[gi][2])/gw])
                y_errors.extend([abs(pr[pi][1]-gt[gi][1])/gh, abs(pr[pi][3]-gt[gi][3])/gh])
            scores.extend(matched)
        per_line.append({"id": row["id"], "reference_words": len(gt),
                         "predicted_words": len(pr), "matched_ious": matched,
                         "count_equal": len(gt) == len(pr)})
    at50 = sum(v >= .5 for v in scores); at80 = sum(v >= .8 for v in scores)
    return {"method": label, "matching": "index" if index_aligned else "hungarian_geometry",
            "reference_words": gt_total, "predicted_words": pred_total,
            "matched_pairs": len(scores), "mean_iou_matched": float(np.mean(scores)) if scores else None,
            "matches_iou50": at50, "precision_iou50": at50/pred_total if pred_total else None,
            "recall_iou50": at50/gt_total if gt_total else None,
            "matches_iou80": at80, "precision_iou80": at80/pred_total if pred_total else None,
            "recall_iou80": at80/gt_total if gt_total else None,
            "mean_abs_horizontal_boundary_error_normalized": float(np.mean(x_errors)) if x_errors else None,
            "mean_abs_vertical_boundary_error_normalized": float(np.mean(y_errors)) if y_errors else None,
            "lines_all_words_iou80": sum(r["count_equal"] and r["matched_ious"] and
                len(r["matched_ious"]) == r["reference_words"] and all(v >= .8 for v in r["matched_ious"])
                for r in per_line), "per_line": per_line}


def text_metrics(rows: list[dict], native: dict[str, list[dict]]) -> dict:
    result = {}
    for profile in ("strict", "glyph_decomposition_v1"):
        chars = edits = exact = 0
        per_line = []
        for row in rows:
            ref = transform(row["text"], profile)
            hyp = transform(" ".join(w["text"] for w in native[row["id"]]), profile)
            distance = edit_distance(ref, hyp)
            chars += len(ref); edits += distance; exact += ref == hyp
            per_line.append({"id": row["id"], "reference": ref,
                             "hypothesis": hyp, "edits": distance})
        result[profile] = {"characters": chars, "edits": edits,
                           "cer": edits/chars if chars else None,
                           "exact_lines": exact, "per_line": per_line}
    return result


def main() -> None:
    started = time.perf_counter(); OUT.mkdir(parents=True, exist_ok=True)
    split = json.loads((EXP / "split.json").read_text())
    opened = json.loads((EXP / "opened.json").read_text())
    if sha(EXP / "PROTOCOL.md") != split["protocol_sha256"]:
        raise ValueError("protocol changed after freeze")
    opened_hashes = {f["path"]: f["sha256"] for f in opened["files"]}
    protected = [EXP/"PROTOCOL.md", EXP/"split.json", EXP/"opened.json"]
    protected += [SOURCE/path for path in opened_hashes]
    before = {str(p.relative_to(ROOT)): sha(p) for p in protected}
    for path, expected in opened_hashes.items():
        if sha(SOURCE/path) != expected:
            raise ValueError(f"opened source changed: {path}")

    rows, image_paths = load_rows(split)
    by_page = defaultdict(list)
    for row in rows:
        by_page[row["page"]].append(row)

    import torch
    from pero_ocr.document_ocr.page_parser import PageParser
    torch.set_num_threads(4)
    config = configparser.ConfigParser(); config.read(MODEL / "config_cpu.ini")
    config["PAGE_PARSER"]["RUN_LAYOUT_PARSER"] = "no"
    tic = time.perf_counter()
    parser = PageParser(config, device=torch.device("cpu"), config_path=str(MODEL))
    load_seconds = time.perf_counter() - tic

    native, forced, otsu = {}, {}, {}
    proxy_report = {}; recognition_seconds = alignment_seconds = 0.0
    for page, group in sorted(by_page.items()):
        cache = OUT / "recognition" / page
        if not (cache / "cache.json").exists():
            image, layout = build_layout(page, group, image_paths[page])
            tic = time.perf_counter(); layout = parser.process_page(image, layout)
            recognition_seconds += time.perf_counter() - tic
            save_cache(layout, cache, "PERO 0.7.0 eu/cz newspapers 2022-09-26; oracle A25 lines")
        layout, _ = load_cache(cache)
        image = cv2.imread(str(image_paths[page]), cv2.IMREAD_GRAYSCALE)
        native_xml = layout.to_altoxml_string()
        if isinstance(native_xml, str): native_xml = native_xml.encode()
        native_xml = bind_native_alto_ids(native_xml, layout.regions)
        (OUT / f"native-{page}.alto.xml").write_bytes(native_xml)
        ids = {r["id"] for r in group}
        native.update(alto_rows(native_xml, ids))

        reference = {r["id"]: r["text"] for r in group}
        proxies, changes = {}, {}
        for line in layout.lines_iterator():
            proxies[line.id], changes[line.id] = make_proxy(reference[line.id], set(line.characters[:-1]))
        tic = time.perf_counter(); forced_xml, _ = realign(layout, proxies)
        alignment_seconds += time.perf_counter() - tic
        (OUT / f"forced-{page}.alto.xml").write_bytes(forced_xml)
        forced_page = alto_rows(forced_xml, ids)
        for row in group:
            lid = row["id"]; tokens = row["text"].split()
            if len(forced_page[lid]) != len(tokens) or len(tokens) != len(row["words"]):
                forced[lid] = []; otsu[lid] = []
                continue
            forced[lid] = [{"text": t, "bbox": w["bbox"]}
                           for t, w in zip(tokens, forced_page[lid])]
            boxes = raw_otsu_boxes(image, row["line_bbox"], [w["bbox"] for w in forced_page[lid]])
            otsu[lid] = [{"text": t, "bbox": b} for t, b in zip(tokens, boxes)]
        proxy_report.update({lid: {"reference": reference[lid], "proxy": proxies[lid],
                                   "changes": changes[lid]} for lid in ids})

    measurements = {
        "pero_native": box_metrics(rows, native, "pero_native_ocr_boxes", False),
        "reference_forced_ctc": box_metrics(rows, forced, "reference_text_forced_pero_ctc", True),
        "ctc_raw_otsu_v1": box_metrics(rows, otsu, "forced_ctc_separators_plus_line_otsu", True),
    }
    f, o, n = measurements["reference_forced_ctc"], measurements["ctc_raw_otsu_v1"], measurements["pero_native"]
    no_omission = o["predicted_words"] == o["reference_words"]
    gate = no_omission and all(o[k] >= f[k] and o[k] >= n[k]
        for k in ("mean_iou_matched", "recall_iou50", "recall_iou80"))
    language_probe = " ".join(r["text"] for r in rows[:12])
    report = {
        "schema": "bbvlm.french-holdout-a25/1",
        "scope": "all eligible lines on four pages from one previously unused SBB work; oracle line polygons and text",
        "selection_intent": "French holdout",
        "observed_language_warning": "opened transcription is predominantly historical German, not French",
        "language_probe_first_12_lines": language_probe,
        "reference_status": "external SBB provider transcription plus project post-correction; not independently adjudicated perfect truth",
        "reference_pua": private_use_inventory("".join(r["text"] for r in rows)),
        "model": {"package": "pero-ocr==0.7.0", "weights": MODEL.name,
                  "archive_sha256": MODEL_SHA, "torch": torch.__version__, "opencv": cv2.__version__,
                  "device": "cpu", "threads": 4},
        "counts": {"pages": len(by_page), "lines": len(rows),
                   "reference_words": sum(len(r["words"]) for r in rows)},
        "cost": {"model_load_seconds": load_seconds, "recognition_seconds": recognition_seconds,
                 "recognized_lines": len(rows), "recognizer_forwards": len(rows),
                 "forced_alignment_seconds": alignment_seconds, "new_vlm_tasks": 0,
                 "total_wall_seconds": time.perf_counter()-started},
        "native_ocr": text_metrics(rows, native), "measurements": measurements,
        "proxy": proxy_report,
        "candidate_local_gate_passed": gate,
        "invariants": {"protocol_frozen_before_source_open": True,
                       "implementation_frozen_before_source_open": False,
                       "source_git_blobs_verified": True,
                       "all_line_text_equals_joined_word_text": True,
                       "protected_inputs_unchanged": before == {str(p.relative_to(ROOT)): sha(p) for p in protected}},
        "limitations": [
            "A25 implementation was written after sources were opened; the candidate was described but Otsu details were underspecified, so this is validation-at-risk.",
            "The work was misidentified from its path as French; the opened content is predominantly historical German.",
            "All pages share one work and are not independent of each other.",
            "Line polygons, reference text and token counts are oracle inputs; this is conditional geometry, not end-to-end layout.",
            "Synthetic horizontal baselines may disadvantage PERO.",
            "Source word polygons are external corrected annotations, not independently adjudicated perfect boxes.",
        ],
        "accepted_for_project_completion_gate": False,
        "protected_input_sha256": before,
    }
    (OUT / "boxes.json").write_text(json.dumps({"native": native, "forced": forced, "otsu": otsu}, ensure_ascii=False, indent=2)+"\n")
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    summary = {"counts": report["counts"], "cost": report["cost"],
               "native_ocr": {k: {a:b for a,b in v.items() if a != "per_line"} for k,v in report["native_ocr"].items()},
               "measurements": {k: {a:b for a,b in v.items() if a != "per_line"} for k,v in measurements.items()},
               "candidate_local_gate_passed": gate}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
