#!/usr/bin/env python3
"""Open two frozen A51 pilot pages and prepare reference-blind boundary sheets."""
from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from bbvlm.order import infer_recurrent_column_order
from evaluate_finlam_page_a48 import CLASS_NAMES
from prepare_finlam_boundaries_a50 import context_crop


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/loop/finlam-boundaries-a51"
SOURCE_DIR = EXP / "source"
INPUT_DIR = EXP / "input"
BASE = "https://datasets-server.huggingface.co/rows"
ARTICLE_ROLES = {
    "ILLUSTRATION", "TITLE", "TEXT", "SUBTITLE", "INSIDEHEADING", "CAPTION",
    "AUTHOR", "TABLE", "ILLUSTRATEDTEXT", "TABLECONTENT", "ASIDE",
}


def token_for(row_index: int, a: int, b: int) -> str:
    digest = hashlib.sha256(f"bbvlm-a51-v1:{row_index}:{a}:{b}".encode()).hexdigest().upper()
    return f"V{digest[:6]}"


def fetch_row(index: int, split: dict) -> dict:
    params = urllib.parse.urlencode({
        "dataset": split["source"]["dataset"], "config": split["source"]["config"],
        "split": split["source"]["split"], "offset": index, "length": 1,
    })
    with urllib.request.urlopen(f"{BASE}?{params}", timeout=60) as response:
        payload = json.load(response)
    if payload["rows"][0]["row_idx"] != index:
        raise ValueError("row index mismatch")
    row = payload["rows"][0]["row"]
    if split["source"]["revision"] not in row["page_image"]["src"]:
        raise ValueError("dataset revision mismatch")
    (SOURCE_DIR / f"row-{index}.json").write_text(json.dumps(payload) + "\n")
    return row


def main() -> None:
    split = json.loads((EXP / "split.json").read_text())
    pilot = split["selection"]["row_indices"][:2]
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_candidates = []
    sheet_manifest = []
    private_pages = {}
    font = ImageFont.load_default(size=22)
    for index in pilot:
        row = fetch_row(index, split)
        image_path = INPUT_DIR / f"row-{index}-page.jpg"
        urllib.request.urlretrieve(row["page_image"]["src"], image_path)
        image = Image.open(image_path).convert("RGB")
        width, height = row["page_image"]["width"], row["page_image"]["height"]
        if image.size != (width, height):
            raise ValueError("page image size mismatch")
        regions = []
        for zone, (polygon, class_id) in enumerate(zip(row["zone_polygons"], row["zone_classes"])):
            # Keep sub-pixel extent for very thin Finlam polygons.  Integer
            # rounding collapsed one unopened region to zero width before any
            # model/reference score; the order implementation correctly
            # rejects such invalid boxes.
            xs = [point[0] * width for point in polygon]
            ys = [point[1] * height for point in polygon]
            regions.append({"id": zone, "bbox": [min(xs), min(ys), max(xs), max(ys)],
                            "role": CLASS_NAMES[class_id]})
        proposal = infer_recurrent_column_order(regions, [0, 0, width, height])
        by_id = {region["id"]: region for region in regions}
        candidates = []
        for upper, lower in zip(proposal["ordered_region_ids"], proposal["ordered_region_ids"][1:]):
            upper_region, lower_region = by_id[upper], by_id[lower]
            if upper_region["role"] not in ARTICLE_ROLES or lower_region["role"] not in ARTICLE_ROLES:
                continue
            if lower_region["role"] == "TITLE":
                continue
            a, b = upper_region["bbox"], lower_region["bbox"]
            overlap = max(0, min(a[2], b[2]) - max(a[0], b[0]))
            overlap /= max(1, min(a[2] - a[0], b[2] - b[0]))
            gap = (b[1] - a[3]) / height
            if gap > 0.004 or overlap < 0.25:
                candidates.append({
                    "token": token_for(index, upper, lower), "row_index": index,
                    "upper_zone": upper, "lower_zone": lower,
                    "gap_fraction": gap, "horizontal_overlap_fraction": overlap,
                    "upper_bbox": a, "lower_bbox": b,
                })
        for sheet_number, start in enumerate(range(0, len(candidates), 6), start=1):
            batch = candidates[start:start + 6]
            sheet = Image.new("RGB", (1500, 1850), (232, 232, 232))
            draw = ImageDraw.Draw(sheet)
            for slot, item in enumerate(batch):
                top = slot * 300 + 10
                draw.rectangle([10, top, 1490, top + 285], fill="white", outline=(40, 40, 40), width=2)
                draw.text((25, top + 10), f"{item['token']}  A (candidate predecessor)", fill="black", font=font)
                draw.text((775, top + 10), "B (candidate successor)", fill="black", font=font)
                sheet.paste(context_crop(image, item["upper_bbox"]), (25, top + 38))
                sheet.paste(context_crop(image, item["lower_bbox"]), (775, top + 38))
            filename = f"row-{index}-sheet-{sheet_number:02d}.jpg"
            sheet.save(INPUT_DIR / filename, quality=92, subsampling=0)
            sheet_manifest.append({"row_index": index, "sheet": sheet_number,
                                   "file": filename, "tokens": [x["token"] for x in batch]})
        private_pages[str(index)] = {
            "page_index": row["page_index"], "ordered_region_ids": proposal["ordered_region_ids"],
            "candidates": candidates,
        }
        all_candidates.extend(candidates)

    private = {
        "schema": "bbvlm.finlam-boundaries-a51-private-map/1",
        "status": "first two pages of eight-page frozen A51 split opened for pilot validation",
        "pilot_rows": pilot, "pages": private_pages,
    }
    request = {
        "schema": "bbvlm.finlam-boundaries-a51-blind-request/1",
        "task": "For each opaque token, decide whether B continues the same newspaper article as A.",
        "labels": ["same_article", "new_article", "unclear"],
        "rules": [
            "Use only these supplied sheet images; do not open source rows, private-map.json, reports, code or annotations.",
            "Judge editorial continuity, not mere topical similarity. Ads/notices may start without a formally marked title.",
            "A and B can lie in different physical columns. A column wrap may still be same_article.",
            "Return exactly one decision for every token and never infer meaning from the token string.",
        ],
        "sheets": sheet_manifest, "tokens": [x["token"] for x in all_candidates],
        "expected_output": {"reader": "model name", "decisions": [
            {"token": "opaque id", "label": "same_article|new_article|unclear",
             "confidence": "high|medium|low", "brief_visual_reason": "short evidence"}
        ]},
    }
    (EXP / "private-map.json").write_text(json.dumps(private, indent=2) + "\n")
    (INPUT_DIR / "request.json").write_text(json.dumps(request, indent=2) + "\n")
    print(json.dumps({"pilot_rows": pilot, "candidates": len(all_candidates),
                      "sheets": len(sheet_manifest)}, indent=2))


if __name__ == "__main__":
    main()
