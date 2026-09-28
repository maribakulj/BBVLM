#!/usr/bin/env python3
"""Audit the frozen BnL A45 sample without changing its membership."""
from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET

import cv2
import langid


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop/bnl-independent-a45"
NS = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}


def rectangle(node: ET.Element) -> tuple[int, int, int, int]:
    x = int(node.attrib["HPOS"])
    y = int(node.attrib["VPOS"])
    return x, y, x + int(node.attrib["WIDTH"]), y + int(node.attrib["HEIGHT"])


def main() -> None:
    split = json.loads((BASE / "split.json").read_text())
    langid.set_languages(["fr", "de", "lb"])
    rows = []
    for identifier in split["selection"]["ids"]:
        image = cv2.imread(str(BASE / "source" / f"{identifier}.png"))
        if image is None:
            raise ValueError(f"missing image {identifier}")
        height, width = image.shape[:2]
        root = ET.parse(BASE / "source" / f"{identifier}.xml").getroot()
        lines = root.findall(".//a:TextLine", NS)
        words = root.findall(".//a:String", NS)
        text = "\n".join(" ".join(word.attrib.get("CONTENT", "") for word in line.findall("a:String", NS))
                         for line in lines)
        language, score = langid.classify(text)
        line_boxes = [rectangle(line) for line in lines]
        word_boxes = [rectangle(word) for word in words]
        invalid_lines = [box for box in line_boxes if box[0] < 0 or box[1] < 0 or box[2] > width or box[3] > height]
        invalid_words = [box for box in word_boxes if box[0] < 0 or box[1] < 0 or box[2] > width or box[3] > height]
        line_membership_failures = 0
        for line in lines:
            line_box = rectangle(line)
            for word in line.findall("a:String", NS):
                word_box = rectangle(word)
                if not (line_box[0] <= word_box[0] and line_box[1] <= word_box[1]
                        and line_box[2] >= word_box[2] and line_box[3] >= word_box[3]):
                    line_membership_failures += 1
        rows.append({"id": identifier, "image": {"width": width, "height": height},
                     "measurement_unit": root.findtext("a:Description/a:MeasurementUnit", namespaces=NS),
                     "lines": len(lines), "words": len(words), "characters": len(text),
                     "language_prediction": language, "language_score": score,
                     "invalid_line_boxes": len(invalid_lines), "invalid_word_boxes": len(invalid_words),
                     "word_not_contained_by_parent_line": line_membership_failures,
                     "reference_text": text})
    by_language = {}
    for row in rows:
        language = row["language_prediction"]
        by_language.setdefault(language, {"blocks": 0, "lines": 0, "words": 0, "characters": 0})
        for key in ("lines", "words", "characters"):
            by_language[language][key] += row[key]
        by_language[language]["blocks"] += 1
    report = {
        "schema": "bbvlm.bnl-independent-a45-audit/1",
        "status": "frozen_sample_opened_after_split",
        "sample_size": len(rows),
        "totals": {key: sum(row[key] for row in rows) for key in ("lines", "words", "characters")},
        "by_predicted_language": by_language,
        "geometry_checks": {
            "invalid_line_boxes": sum(row["invalid_line_boxes"] for row in rows),
            "invalid_word_boxes": sum(row["invalid_word_boxes"] for row in rows),
            "word_not_contained_by_parent_line": sum(row["word_not_contained_by_parent_line"] for row in rows),
        },
        "interpretation": {
            "ocr_reference": "usable independent double-keyed diplomatic transcription; exact error ceiling is nonzero (provider states >=99.95%)",
            "line_geometry": "provider explicitly recommends raw blocks for text-line segmentation; coordinates align to supplied crops",
            "word_geometry": "ALTO word rectangles exist but the provider does not explicitly claim manual word-box adjudication; do not call them perfect word GT",
            "language": "automatic restricted-set prediction used only to describe the frozen sample, never to alter membership",
        },
        "rows": rows,
    }
    (BASE / "audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    compact = dict(report)
    compact.pop("rows")
    print(json.dumps(compact, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
