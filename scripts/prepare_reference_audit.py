"""Prepare a fixed, blind audit sample from the three word-annotated pages.

Selection uses page and geometry only. Distributed text and PERO hypotheses are
written outside the reader input directory and are not exposed to the VLM.
"""
from pathlib import Path
import hashlib
import json
import random

from lxml import etree as E
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop/reference-audit-v1"
INPUT = BASE / "input"
HIDDEN = BASE / "evaluation"
INPUT.mkdir(parents=True, exist_ok=True)
HIDDEN.mkdir(parents=True, exist_ok=True)

rng = random.Random(20260927)
manifest = {
    "schema": "bbvlm.reference-audit-request/1",
    "selection": "15 uniformly sampled non-empty TextLines per page; fixed seed 20260927; no text or OCR difficulty used",
    "convention": "literal diplomatic transcription; preserve punctuation, accents, apostrophe shape and printed end-of-line hyphen; never repair from language context",
    "requested_line_ids": [],
    "lines": [],
}
reference = []

for page_id in ["0253902-001", "0401692-003", "752234-003"]:
    run = json.loads((ROOT / "experiments/loop/cache" / page_id / "run.json").read_text())
    xml_path = ROOT / run["source_xml"]
    image_path = ROOT / run["image"]
    tree = E.parse(str(xml_path))
    candidates = []
    for line in tree.findall(".//{*}TextLine"):
        text = line.findtext("{*}TextEquiv/{*}Unicode", default="")
        coords = line.find("{*}Coords")
        if not text.strip() or coords is None:
            continue
        pts = [tuple(map(float, p.split(","))) for p in coords.get("points").split()]
        box = [min(p[0] for p in pts), min(p[1] for p in pts),
               max(p[0] for p in pts), max(p[1] for p in pts)]
        candidates.append((line.get("id"), text, box))
    chosen = rng.sample(candidates, 15)
    image = Image.open(image_path).convert("RGB")
    crops = []
    items = []
    for source_id, text, box in chosen:
        audit_id = "A" + hashlib.sha256(f"{page_id}:{source_id}".encode()).hexdigest()[:11]
        x0, y0, x1, y1 = box
        expanded = [max(0, int(x0) - 10), max(0, int(y0) - 5),
                    min(image.width, int(x1) + 10), min(image.height, int(y1) + 5)]
        crop = image.crop(expanded)
        crops.append(crop)
        item = {"id": audit_id, "page_alias": "P" + hashlib.sha256(page_id.encode()).hexdigest()[:7],
                "bbox": [int(v) for v in box]}
        items.append(item)
        manifest["requested_line_ids"].append(audit_id)
        reference.append({"id": audit_id, "page": page_id, "source_line_id": source_id,
                          "distributed_text": text, "bbox": box,
                          "xml_sha256": run["xml_sha256"], "image_sha256": run["image_sha256"]})
    for sheet_index, start in enumerate(range(0, 15, 5), 1):
        batch = crops[start:start + 5]
        rows = items[start:start + 5]
        width = max(c.width for c in batch) + 180
        height = sum(c.height + 34 for c in batch) + 15
        sheet = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(sheet)
        y = 8
        filename = f"{page_id}-sheet-{sheet_index}.png"
        for item, crop in zip(rows, batch):
            draw.text((5, y + 4), item["id"], fill="blue")
            sheet.paste(crop, (170, y))
            item["sheet"] = filename
            y += crop.height + 34
        sheet.save(INPUT / filename)
    manifest["lines"].extend(items)

(INPUT / "request.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
(HIDDEN / "distributed-reference.json").write_text(json.dumps(reference, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lines": len(reference), "pages": 3, "input": str(INPUT)}))
