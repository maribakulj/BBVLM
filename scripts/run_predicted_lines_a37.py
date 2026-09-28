#!/usr/bin/env python3
"""Full-page PERO inference and unchanged A32 refinement, without reading GT."""
from pathlib import Path
import configparser, hashlib, json, time

import cv2
import torch
from lxml import etree as E
from pero_ocr.core.layout import PageLayout
from pero_ocr.document_ocr.page_parser import PageParser

from bbvlm.component_boxes import PARAMETERS, refine_cells
from bbvlm.selective_refine import nonexpanding_vertical

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/loop/predicted-lines-a37"
SOURCE = EXP / "source"
MODEL = ROOT / "models/pero/pero_eu_cz_print_newspapers_2022-09-26"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def words_from_alto(text):
    root = E.fromstring(text.encode())
    lines = []
    for index, line in enumerate(root.findall(".//{*}TextLine")):
        x, y = float(line.get("HPOS")), float(line.get("VPOS"))
        box = [x, y, x + float(line.get("WIDTH")), y + float(line.get("HEIGHT"))]
        words = []
        for word in line.findall("{*}String"):
            wx, wy = float(word.get("HPOS")), float(word.get("VPOS"))
            words.append({"text": word.get("CONTENT") or "",
                          "bbox": [wx, wy, wx + float(word.get("WIDTH")), wy + float(word.get("HEIGHT"))]})
        lines.append({"id": line.get("ID") or f"line_{index:05d}", "bbox": box, "words": words})
    return lines


def main():
    split = json.loads((EXP / "split.json").read_text())
    opened = json.loads((EXP / "opened.json").read_text())
    assert opened["status"] == "opened_verified"
    # Protect GT by identity only. Its bytes are not opened in this process.
    gt_hashes = {x["path"]: x["sha256"] for x in opened["files"] if x["kind"] == "xml"}
    config = configparser.ConfigParser()
    config.read(MODEL / "config_cpu.ini")
    torch.set_num_threads(4)
    parser = PageParser(config, device=torch.device("cpu"), config_path=str(MODEL))
    pages = []
    for item in split["pages"]:
        image_path = SOURCE / item["image"]
        image = cv2.imread(str(image_path))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        tick = time.perf_counter()
        page = parser.process_page(image, PageLayout(id="A37_" + item["page"], page_size=image.shape[:2]))
        inference_seconds = time.perf_counter() - tick
        alto = page.to_altoxml_string()
        layout = page.to_pagexml_string()
        lines = words_from_alto(alto)
        tick = time.perf_counter()
        for line in lines:
            # ALTO serializes numeric geometry as floats; NumPy slice indices
            # must be integers. This conversion changes no box semantics.
            line_box = [int(round(v)) for v in line["bbox"]]
            boxes = [[int(round(v)) for v in w["bbox"]] for w in line["words"]]
            refined, _ = refine_cells(gray, line_box, boxes, "satellites") if boxes else ([], {})
            for word, bbox in zip(line["words"], refined):
                word["refined_bbox"] = bbox
                word["routed_bbox"] = nonexpanding_vertical(word["bbox"], bbox)
        refinement_seconds = time.perf_counter() - tick
        stem = item["page"]
        (EXP / "output").mkdir(parents=True, exist_ok=True)
        (EXP / "output" / f"{stem}.alto.xml").write_text(alto)
        (EXP / "output" / f"{stem}.page.xml").write_text(layout)
        pages.append({"page": stem, "image": item["image"], "image_sha256": digest(image_path),
                      "height": int(image.shape[0]), "width": int(image.shape[1]),
                      "predicted_lines": len(lines), "predicted_words": sum(len(x["words"]) for x in lines),
                      "inference_seconds": inference_seconds, "refinement_seconds": refinement_seconds,
                      "lines": lines})
        print(stem, pages[-1]["predicted_lines"], pages[-1]["predicted_words"], flush=True)
    # Verify protected XML after all predictions exist; hashes came from opener metadata.
    for rel, expected in gt_hashes.items():
        assert digest(SOURCE / rel) == expected
    out = {"schema": "bbvlm.predicted-lines-a37-predictions/1", "status": "predictions_sealed_before_gt_evaluation",
           "model": "PERO 0.7.0 eu/cz print-newspapers 2022-09-26 CPU", "parameters": PARAMETERS,
           "reference_inputs": False, "native_text_order_cardinality_preserved": True,
           "router": {"rule": "accept A32 only when refined height <= native height",
                      "parameters": 0, "reads_reference": False},
           "pages": pages, "cost": {"new_vlm_passes": 0, "recognizer_forwards": sum(x["predicted_lines"] for x in pages),
           "full_page_seconds": sum(x["inference_seconds"] for x in pages),
           "refinement_seconds": sum(x["refinement_seconds"] for x in pages)}}
    (EXP / "output/predictions.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
