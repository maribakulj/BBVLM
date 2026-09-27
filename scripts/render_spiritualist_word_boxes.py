"""Render a diagnostic crop of distributed Spiritualist word boxes."""
from pathlib import Path
import sys

import cv2
from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
page_id = sys.argv[1] if len(sys.argv) > 1 else "0009"
image_path = ROOT / f"corpora/spiritualist/companion/Spiritualist_Images/{page_id}.png"
xml_path = next((ROOT / "corpora/spiritualist/alto_xml/ocr_gt_labelled").glob(f"{page_id}_*.xml"))
out = ROOT / f"experiments/loop/spiritualist-v1/{page_id}-word-box-audit.png"
ns = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}
tree = E.parse(str(xml_path))
line = next(node for node in tree.findall(".//a:TextLine", ns) if len(node.findall("a:String", ns)) >= 8)
image = cv2.imread(str(image_path))
x = int(float(line.get("HPOS")))
y = int(float(line.get("VPOS")))
w = int(float(line.get("WIDTH")))
h = int(float(line.get("HEIGHT")))
pad = 20
for word in line.findall("a:String", ns):
    wx = int(float(word.get("HPOS")))
    wy = int(float(word.get("VPOS")))
    ww = int(float(word.get("WIDTH")))
    wh = int(float(word.get("HEIGHT")))
    cv2.rectangle(image, (wx, wy), (wx + ww, wy + wh), (0, 0, 255), 2)
cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
x0, y0 = max(0, x - pad), max(0, y - pad)
x1, y1 = min(image.shape[1], x + w + pad), min(image.shape[0], y + h + pad)
crop = image[y0:y1, x0:x1]
cv2.imwrite(str(out), crop)
print(out)
print(line.get("ID"), [w.get("CONTENT") for w in line.findall("a:String", ns)])
