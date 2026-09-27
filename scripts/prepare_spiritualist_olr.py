"""Prepare a blind, non-sequential-ID OLR/SSU pilot on a development page."""
from pathlib import Path
import hashlib
import json

import cv2
import numpy as np
from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
PAGE = "0009"
SEED = "bbvlm-olr-2026092702"
XML = ROOT / "corpora/spiritualist/alto_xml/ocr_gt_labelled/0009_p009.xml"
IMAGE = ROOT / "corpora/spiritualist/companion/Spiritualist_Images/0009.png"
OUT = ROOT / "experiments/loop/spiritualist-v1/olr-0009"
NS = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}


def blind_id(source_id):
    return "R" + hashlib.sha256(f"{SEED}|{source_id}".encode()).hexdigest()[:10]


def main():
    (OUT / "input").mkdir(parents=True, exist_ok=True)
    (OUT / "evaluation").mkdir(parents=True, exist_ok=True)
    tree = E.parse(str(XML))
    blocks = tree.findall(".//a:TextBlock", NS)
    image = cv2.imread(str(IMAGE))
    overlay = image.copy()
    rows = []
    for block in blocks:
        source_id = block.get("ID")
        rid = blind_id(source_id)
        polygon = block.find("a:Shape/a:Polygon", NS)
        if polygon is not None:
            pts = np.array([[int(float(v)) for v in p.split(",")] for p in polygon.get("POINTS").split()], np.int32)
        else:
            x, y = int(block.get("HPOS")), int(block.get("VPOS"))
            w, h = int(block.get("WIDTH")), int(block.get("HEIGHT"))
            pts = np.array([[x, y], [x+w, y], [x+w, y+h], [x, y+h]], np.int32)
        color_seed = hashlib.sha256(rid.encode()).digest()
        color = tuple(int(80 + value % 176) for value in color_seed[:3])
        cv2.polylines(overlay, [pts], True, color, 6, cv2.LINE_AA)
        x, y = pts[:, 0].min(), pts[:, 1].min()
        cv2.rectangle(overlay, (x, max(0, y-42)), (x+245, y+5), (255, 255, 255), -1)
        cv2.putText(overlay, rid, (x+4, max(32, y-8)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3, cv2.LINE_AA)
        rows.append({
            "id": rid,
            "source_id": source_id,
            "reading_order": int(block.get("READING_ORDER")),
            "semantic_unit": block.get("SSU_ID"),
            "role": block.get("BLOCK_TYPE"),
        })
    cv2.imwrite(str(OUT / "input/page-original.png"), image)
    cv2.imwrite(str(OUT / "input/page-regions-blind.png"), overlay)
    request = {
        "schema": "bbvlm.blind-olr-request/1",
        "page": PAGE,
        "region_ids": sorted(row["id"] for row in rows),
        "images": ["page-original.png", "page-regions-blind.png"],
        "instruction": "Infer reading order and semantic grouping only from the images. IDs are opaque. Return every ID exactly once in ordered_region_ids. Group regions that belong to one narrative/semantic unit; do not assume each region is an article. Assign each region one role from MASTHEAD, HEADER, TEXT, ADVERT, OTHER, UNKNOWN. Flag uncertainty explicitly.",
        "response_schema": {
            "ordered_region_ids": ["opaque ID, each exactly once"],
            "groups": [{"id": "G1", "region_ids": ["opaque IDs"], "label": "short neutral description", "uncertain": False}],
            "roles": {"opaque ID": "MASTHEAD|HEADER|TEXT|ADVERT|OTHER|UNKNOWN"},
            "uncertain_region_ids": [],
            "notes": "short string",
        },
        "leakage_control": "IDs are fixed hashes of source IDs; neither sequence, reading order, SSU nor text is present in the request JSON.",
    }
    reference = {"schema": "bbvlm.blind-olr-reference/1", "page": PAGE, "rows": rows}
    (OUT / "input/request.json").write_text(json.dumps(request, indent=2) + "\n")
    (OUT / "evaluation/reference.json").write_text(json.dumps(reference, indent=2) + "\n")
    print(json.dumps({"regions": len(rows), "input": str(OUT / "input"), "reference": str(OUT / "evaluation/reference.json")}, indent=2))


if __name__ == "__main__":
    main()
