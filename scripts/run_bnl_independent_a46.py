#!/usr/bin/env python3
"""Blind PERO plus frozen A37 inference on the A45 BnL blocks."""
from pathlib import Path
import configparser
import hashlib
import json
import time

import cv2
import torch
from lxml import etree as E
from pero_ocr.core.layout import PageLayout
from pero_ocr.document_ocr.page_parser import PageParser

from bbvlm.component_boxes import PARAMETERS, refine_cells
from bbvlm.selective_refine import nonexpanding_vertical


ROOT = Path(__file__).resolve().parents[1]
A45 = ROOT / "experiments/loop/bnl-independent-a45"
EXP = ROOT / "experiments/loop/bnl-independent-a46"
MODEL = ROOT / "models/pero/pero_eu_cz_print_newspapers_2022-09-26"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lines_from_alto(text: str) -> list[dict]:
    root = E.fromstring(text.encode())
    lines = []
    for index, line in enumerate(root.findall(".//{*}TextLine")):
        x, y = float(line.get("HPOS")), float(line.get("VPOS"))
        words = []
        for word in line.findall("{*}String"):
            wx, wy = float(word.get("HPOS")), float(word.get("VPOS"))
            words.append({"text": word.get("CONTENT") or "",
                          "bbox": [wx, wy, wx + float(word.get("WIDTH")), wy + float(word.get("HEIGHT"))]})
        lines.append({"id": line.get("ID") or f"line_{index:05d}",
                      "bbox": [x, y, x + float(line.get("WIDTH")), y + float(line.get("HEIGHT"))],
                      "text": " ".join(word["text"] for word in words), "words": words})
    return lines


def main() -> None:
    split = json.loads((A45 / "split.json").read_text())
    config = configparser.ConfigParser()
    config.read(MODEL / "config_cpu.ini")
    torch.set_num_threads(4)
    parser = PageParser(config, device=torch.device("cpu"), config_path=str(MODEL))
    blocks = []
    output = EXP / "output"
    output.mkdir(parents=True, exist_ok=True)
    for identifier in split["selection"]["ids"]:
        image_path = A45 / "source" / f"{identifier}.png"
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"missing frozen image {identifier}")
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        started = time.perf_counter()
        page = parser.process_page(image, PageLayout(id="A46_" + identifier, page_size=image.shape[:2]))
        inference_seconds = time.perf_counter() - started
        alto, page_xml = page.to_altoxml_string(), page.to_pagexml_string()
        lines = lines_from_alto(alto)
        started = time.perf_counter()
        for line in lines:
            line_box = [int(round(value)) for value in line["bbox"]]
            native = [[int(round(value)) for value in word["bbox"]] for word in line["words"]]
            refined, _ = refine_cells(gray, line_box, native, "satellites") if native else ([], {})
            for word, box in zip(line["words"], refined):
                word["refined_bbox"] = box
                word["routed_bbox"] = nonexpanding_vertical(word["bbox"], box)
        refinement_seconds = time.perf_counter() - started
        (output / f"{identifier}.alto.xml").write_text(alto)
        (output / f"{identifier}.page.xml").write_text(page_xml)
        blocks.append({"id": identifier, "image_sha256": digest(image_path),
                       "height": int(image.shape[0]), "width": int(image.shape[1]),
                       "predicted_lines": len(lines),
                       "predicted_words": sum(len(line["words"]) for line in lines),
                       "inference_seconds": inference_seconds,
                       "refinement_seconds": refinement_seconds, "lines": lines})
        print(identifier, len(lines), blocks[-1]["predicted_words"], flush=True)
    report = {"schema": "bbvlm.bnl-independent-a46-predictions/1",
              "status": "predictions_sealed_before_reference_evaluation",
              "model": "PERO 0.7.0 eu/cz print-newspapers 2022-09-26 CPU",
              "reference_inputs": False, "parameters": PARAMETERS,
              "router": {"rule": "A37 accept A32 only when refined height <= native height",
                         "parameters": 0, "reads_reference": False},
              "blocks": blocks,
              "cost": {"new_vlm_passes": 0,
                       "recognizer_forwards": sum(block["predicted_lines"] for block in blocks),
                       "full_block_seconds": sum(block["inference_seconds"] for block in blocks),
                       "refinement_seconds": sum(block["refinement_seconds"] for block in blocks)}}
    (output / "predictions.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
