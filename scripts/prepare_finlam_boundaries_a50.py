#!/usr/bin/env python3
"""Prepare a blind visual packet for ambiguous article boundaries on A49.

This is a consumed-data development experiment.  Geometry keeps ownership of
physical column order; the VLM only sees transitions that a cheap geometric
router cannot safely classify as same-article versus new-article.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from bbvlm.order import infer_recurrent_column_order
from evaluate_finlam_page_a48 import CLASS_NAMES


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments/loop/finlam-page-a49/source/row-186.json"
EXP = ROOT / "experiments/loop/finlam-boundaries-a50"
PAGE = EXP / "input/page-186.jpg"

GAP_FRACTION = 0.004
OVERLAP_FRACTION = 0.25
SALT = "bbvlm-a50-consumed-development-v1"


def token_for(a: int, b: int) -> str:
    digest = hashlib.sha256(f"{SALT}:{a}:{b}".encode()).hexdigest().upper()
    return f"K{digest[:5]}"


def bbox(polygon: list[list[float]], width: int, height: int) -> list[int]:
    xs = [round(point[0] * width) for point in polygon]
    ys = [round(point[1] * height) for point in polygon]
    return [min(xs), min(ys), max(xs), max(ys)]


def context_crop(image: Image.Image, box: list[int]) -> Image.Image:
    x0, y0, x1, y1 = box
    region_w = max(1, x1 - x0)
    region_h = max(1, y1 - y0)
    margin_x = max(22, round(region_w * 0.16))
    margin_y = max(35, min(150, round(region_h * 0.45)))
    crop_box = (
        max(0, x0 - margin_x), max(0, y0 - margin_y),
        min(image.width, x1 + margin_x), min(image.height, y1 + margin_y),
    )
    crop = image.crop(crop_box).convert("RGB")
    draw = ImageDraw.Draw(crop)
    draw.rectangle(
        [x0 - crop_box[0], y0 - crop_box[1], x1 - crop_box[0], y1 - crop_box[1]],
        outline=(215, 28, 28), width=4,
    )
    crop.thumbnail((690, 245), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (700, 255), "white")
    canvas.paste(crop, ((700 - crop.width) // 2, (255 - crop.height) // 2))
    return canvas


def main() -> None:
    payload = json.loads(SOURCE.read_text())
    row = payload["rows"][0]["row"]
    width, height = row["page_image"]["width"], row["page_image"]["height"]
    image = Image.open(PAGE).convert("RGB")
    if image.size != (width, height):
        raise ValueError(f"image size {image.size} != annotation size {(width, height)}")

    regions = []
    for zone, (polygon, class_id) in enumerate(zip(row["zone_polygons"], row["zone_classes"])):
        regions.append({"id": zone, "bbox": bbox(polygon, width, height),
                        "role": CLASS_NAMES[class_id]})
    proposal = infer_recurrent_column_order(regions, [0, 0, width, height])
    by_id = {region["id"]: region for region in regions}
    candidates = []
    for upper, lower in zip(proposal["ordered_region_ids"], proposal["ordered_region_ids"][1:]):
        if row["zone_article_ids"][upper] is None or row["zone_article_ids"][lower] is None:
            continue
        if row["zone_classes"][lower] == 6:  # visible TITLE already supplies the cheap cut
            continue
        a, b = by_id[upper]["bbox"], by_id[lower]["bbox"]
        overlap = max(0, min(a[2], b[2]) - max(a[0], b[0]))
        overlap /= max(1, min(a[2] - a[0], b[2] - b[0]))
        gap = (b[1] - a[3]) / height
        if gap > GAP_FRACTION or overlap < OVERLAP_FRACTION:
            candidates.append({
                "token": token_for(upper, lower), "upper_zone": upper, "lower_zone": lower,
                "gap_fraction": gap, "horizontal_overlap_fraction": overlap,
                "upper_bbox": a, "lower_bbox": b,
            })

    sheets = []
    font = ImageFont.load_default(size=22)
    for sheet_index, start in enumerate(range(0, len(candidates), 6), start=1):
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
        path = EXP / f"input/sheet-{sheet_index:02d}.jpg"
        sheet.save(path, quality=92, subsampling=0)
        sheets.append({"sheet": sheet_index, "file": path.name,
                       "tokens": [item["token"] for item in batch]})

    private = {
        "schema": "bbvlm.finlam-boundaries-a50-private-map/1",
        "selection_bias": "Consumed A49 row 186 chosen as a development stress page (40 articles, 23 without TITLE).",
        "router": {"gap_fraction_gt": GAP_FRACTION,
                   "horizontal_overlap_fraction_lt": OVERLAP_FRACTION},
        "ordered_region_ids": proposal["ordered_region_ids"],
        "candidates": candidates,
    }
    request = {
        "schema": "bbvlm.finlam-boundaries-a50-blind-request/1",
        "task": "For each opaque token, decide whether B continues the same newspaper article as A.",
        "labels": ["same_article", "new_article", "unclear"],
        "rules": [
            "Use only the supplied sheet images; do not open source rows, private-map.json, reports, or reference annotations.",
            "Judge editorial continuity, not mere topical similarity. Ads/notices may start without a formally marked title.",
            "A and B can lie in different physical columns. A column wrap may still be same_article.",
            "Return exactly one decision for every token and never infer meaning from the token string.",
        ],
        "sheets": sheets,
        "tokens": [item["token"] for item in candidates],
        "expected_output": {
            "reader": "model name", "decisions": [
                {"token": "opaque id", "label": "same_article|new_article|unclear",
                 "confidence": "high|medium|low", "brief_visual_reason": "short evidence"}
            ],
        },
    }
    (EXP / "private-map.json").write_text(json.dumps(private, indent=2) + "\n")
    (EXP / "input/request.json").write_text(json.dumps(request, indent=2) + "\n")
    print(json.dumps({"candidates": len(candidates), "sheets": len(sheets),
                      "request": str(EXP / 'input/request.json')}, indent=2))


if __name__ == "__main__":
    main()
