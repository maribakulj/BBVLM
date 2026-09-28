#!/usr/bin/env python3
"""Render consumed A54 word boxes for A55 visual diagnosis."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET

import cv2


ROOT = Path(__file__).resolve().parents[1]
A54 = ROOT / "experiments/loop/bnl-independent-a54"
OUT = ROOT / "experiments/loop/bnl-geometry-a55/overlays"
NS = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}
SCALE = 300.0 / 254.0


def rect(node):
    x, y = float(node.attrib["HPOS"]), float(node.attrib["VPOS"])
    w, h = float(node.attrib["WIDTH"]), float(node.attrib["HEIGHT"])
    return [round(SCALE*v) for v in (x, y, x+w, y+h)]


def draw(image, bbox, color, thickness):
    x0, y0, x1, y1 = map(round, bbox)
    cv2.rectangle(image, (x0, y0), (x1-1, y1-1), color, thickness)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pred = json.loads((A54 / "output/predictions.json").read_text())
    for block in pred["blocks"]:
        identifier = block["id"]
        image = cv2.imread(str(A54 / "source" / f"{identifier}.png"))
        root = ET.parse(A54 / "source" / f"{identifier}.xml").getroot()
        for word in root.findall(".//a:String", NS):
            draw(image, rect(word), (0, 200, 0), 1)
        for line in block["lines"]:
            for word in line["words"]:
                draw(image, word["bbox"], (255, 0, 0), 1)
                draw(image, word["refined_bbox"], (0, 0, 255), 1)
        cv2.imwrite(str(OUT / f"{identifier}.png"), image)


if __name__ == "__main__":
    main()

