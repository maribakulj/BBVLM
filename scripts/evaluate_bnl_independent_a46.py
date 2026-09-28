#!/usr/bin/env python3
"""Evaluate sealed A46 predictions against the frozen BnL ALTO references."""
from pathlib import Path
import json
import sys
import time
import xml.etree.ElementTree as ET

import numpy as np
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from bbvlm.metrics import edit_distance, iou
from bbvlm.text_views import diplomatic_nfc, lexical_alnum, search_v1


ROOT = Path(__file__).resolve().parents[1]
A45 = ROOT / "experiments/loop/bnl-independent-a45"
EXP = ROOT / "experiments/loop/bnl-independent-a46"
NS = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}
MM10_TO_300PPI_PIXELS = 300.0 / 254.0


def rectangle(node: ET.Element, scale: float) -> list[float]:
    x, y = float(node.attrib["HPOS"]), float(node.attrib["VPOS"])
    return [scale * value for value in
            (x, y, x + float(node.attrib["WIDTH"]), y + float(node.attrib["HEIGHT"]))]


def reference(identifier: str) -> dict:
    root = ET.parse(A45 / "source" / f"{identifier}.xml").getroot()
    measurement = root.findtext(".//a:MeasurementUnit", namespaces=NS)
    if measurement != "mm10":
        raise ValueError(f"unexpected ALTO measurement unit for {identifier}: {measurement!r}")
    scale = MM10_TO_300PPI_PIXELS
    lines, words = [], []
    for line in root.findall(".//a:TextLine", NS):
        line_words = line.findall("a:String", NS)
        lines.append({"bbox": rectangle(line, scale),
                      "text": " ".join(word.attrib.get("CONTENT", "") for word in line_words)})
        words.extend({"bbox": rectangle(word, scale), "text": word.attrib.get("CONTENT", "")} for word in line_words)
    return {"lines": lines, "words": words, "text": "\n".join(line["text"] for line in lines)}


def geometry(reference_boxes: list[list[float]], predicted_boxes: list[list[float]]) -> dict:
    if not reference_boxes or not predicted_boxes:
        return {"reference": len(reference_boxes), "predicted": len(predicted_boxes),
                "matched": 0, "mean_iou": 0.0, "recall_iou50": 0.0, "recall_iou80": 0.0}
    matrix = np.array([[iou(left, right) for right in predicted_boxes] for left in reference_boxes])
    rows, columns = linear_sum_assignment(-matrix)
    values = matrix[rows, columns]
    return {"reference": len(reference_boxes), "predicted": len(predicted_boxes), "matched": len(values),
            "mean_iou": float(values.sum() / len(reference_boxes)),
            "recall_iou50": float((values >= .5).sum() / len(reference_boxes)),
            "recall_iou80": float((values >= .8).sum() / len(reference_boxes))}


VIEWS = {"strict_nfc_diplomatic": diplomatic_nfc, "search_v1": search_v1,
         "lexical_alnum": lexical_alnum}


def text_row(reference_text: str, hypothesis_text: str) -> dict:
    output = {}
    for name, view in VIEWS.items():
        left, right = view(reference_text), view(hypothesis_text)
        edits = edit_distance(left, right)
        output[name] = {"characters": len(left), "edits": edits,
                        "cer": edits / len(left) if left else None, "exact": left == right}
    return output


def aggregate(rows: list[dict], ids: set[str]) -> dict:
    chosen = [row for row in rows if row["id"] in ids]
    text = {}
    for view in VIEWS:
        characters = sum(row["text"][view]["characters"] for row in chosen)
        edits = sum(row["text"][view]["edits"] for row in chosen)
        text[view] = {"characters": characters, "edits": edits,
                      "cer": edits / characters if characters else None,
                      "exact_blocks": sum(row["text"][view]["exact"] for row in chosen)}
    result = {"blocks": len(chosen), "text": text}
    for level in ("lines", "native_words", "routed_words"):
        reference_count = sum(row[level]["reference"] for row in chosen)
        result[level] = {"reference": reference_count,
                         "predicted": sum(row[level]["predicted"] for row in chosen),
                         "mean_iou": sum(row[level]["mean_iou"] * row[level]["reference"] for row in chosen) / reference_count,
                         "recall_iou50": sum(row[level]["recall_iou50"] * row[level]["reference"] for row in chosen) / reference_count,
                         "recall_iou80": sum(row[level]["recall_iou80"] * row[level]["reference"] for row in chosen) / reference_count}
    return result


def main() -> None:
    started = time.perf_counter()
    split = json.loads((A45 / "split.json").read_text())
    audit = json.loads((A45 / "audit.json").read_text())
    prediction = json.loads((EXP / "output/predictions.json").read_text())
    if prediction["status"] != "predictions_sealed_before_reference_evaluation":
        raise ValueError("predictions not sealed")
    by_id = {block["id"]: block for block in prediction["blocks"]}
    expected = set(split["selection"]["ids"])
    if set(by_id) != expected:
        raise ValueError("prediction ID mismatch")
    languages = {row["id"]: row["language_prediction"] for row in audit["rows"]}
    rows = []
    for identifier in split["selection"]["ids"]:
        ref, pred = reference(identifier), by_id[identifier]
        predicted_lines = pred["lines"]
        hypothesis_text = "\n".join(line["text"] for line in predicted_lines)
        native_words = [word for line in predicted_lines for word in line["words"]]
        rows.append({"id": identifier, "language_prediction": languages[identifier],
                     "text": text_row(ref["text"], hypothesis_text),
                     "lines": geometry([line["bbox"] for line in ref["lines"]],
                                       [line["bbox"] for line in predicted_lines]),
                     "native_words": geometry([word["bbox"] for word in ref["words"]],
                                              [word["bbox"] for word in native_words]),
                     "routed_words": geometry([word["bbox"] for word in ref["words"]],
                                              [word["routed_bbox"] for word in native_words])})
    all_ids = set(expected)
    french_ids = {identifier for identifier, language in languages.items() if language == "fr"}
    report = {"schema": "bbvlm.bnl-independent-a46-report/1",
              "status": "frozen_independent_evaluation_complete",
              "scope": "24 pre-frozen BnL newspaper blocks; unchanged PERO and A37; zero VLM passes",
              "aggregate": {"all": aggregate(rows, all_ids), "french": aggregate(rows, french_ids)},
              "cost": prediction["cost"] | {"evaluator_seconds": time.perf_counter() - started},
              "word_reference_status": "diagnostic String rectangles; manual word-box adjudication not documented",
              "line_reference_status": "raw BnL pack explicitly intended for text-line segmentation",
              "text_reference_status": "provider double-keyed >=99.95%; not mathematical perfection",
              "normalizations": {"strict_nfc_diplomatic": "NFC/newline only",
                                 "search_v1": "NFKC, casefold, long-s/apostrophes, line dehyphenation, whitespace",
                                 "lexical_alnum": "NFKC+casefold letters/digits only; punctuation/spacing ignored"},
              "geometry_coordinate_adapter": {
                  "reference_unit": "mm10", "image_resolution_ppi": 300,
                  "scale_to_png_pixels": MM10_TO_300PPI_PIXELS,
                  "formula": "300 pixels/inch divided by 254 tenths-mm/inch",
                  "amended_after_initial_unscaled_score": True,
                  "initial_unscaled_report": "output/report-unscaled-invalid.json"},
              "accepted_for_project_completion_gate": False,
              "limitations": ["Blocks are not complete pages, so column OLR/article grouping is out of scope.",
                              "The EU/CZ PERO model is not a French-specific recognizer.",
                              "Existing word rectangles are not certified as perfect word-box truth."],
              "rows": rows}
    (EXP / "output/report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    compact = dict(report); compact.pop("rows")
    print(json.dumps(compact, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
