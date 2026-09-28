#!/usr/bin/env python3
"""Prepare a blind, one-pass VLM anchor packet for consumed A48 page 365."""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/loop/finlam-page-a48"
ROW_INDEX = 365
ANCHOR_CLASSES = {0, 1, 2, 6, 8, 9}


def token(zone: int) -> str:
    digest = hashlib.sha256(f"BBVLM-A48-anchor:{zone}".encode()).hexdigest().upper()
    return f"Q{digest[:4]}"


def main() -> None:
    row = json.loads((EXP / f"source/row-{ROW_INDEX}.json").read_text())["rows"][0]["row"]
    image = Image.open(EXP / f"source/page-{ROW_INDEX}.jpg").convert("RGB")
    width, height = image.size
    chosen = [i for i, value in enumerate(row["zone_classes"]) if value in ANCHOR_CLASSES]
    mapping = {token(i): i for i in chosen}
    reverse = {zone: opaque for opaque, zone in mapping.items()}

    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.load_default(size=18)
    for zone in chosen:
        points = [(round(x * width), round(y * height)) for x, y in row["zone_polygons"][zone]]
        xs, ys = [p[0] for p in points], [p[1] for p in points]
        box = [min(xs), min(ys), max(xs), max(ys)]
        opaque = reverse[zone]
        draw.rectangle(box, outline=(230, 0, 0), width=3)
        label_box = draw.textbbox((box[0], box[1]), opaque, font=font, stroke_width=2)
        draw.rectangle(label_box, fill=(255, 255, 210))
        draw.text((box[0], box[1]), opaque, fill=(120, 0, 0), font=font, stroke_width=1,
                  stroke_fill=(255, 255, 255))
    reader = EXP / "anchor-vlm/reader"
    reader.mkdir(parents=True, exist_ok=True)
    overlay.save(reader / "page-overlay.jpg", quality=94)
    image.save(reader / "page-original.jpg", quality=94)

    opaque_tokens = list(mapping)
    random.Random("BBVLM-A48-anchor-shuffle").shuffle(opaque_tokens)
    request = {
        "schema": "bbvlm.finlam-anchor-request/1",
        "page": "opaque-page-A48",
        "inputs": ["page-original.jpg", "page-overlay.jpg"],
        "opaque_tokens_shuffled": opaque_tokens,
        "task": (
            "Inspect both images. Red rectangles mark only candidate heading/header zones; token names encode no order or role. "
            "Return strict JSON only. Classify every token exactly once as masthead, article_title, subheading, or other. "
            "Group multiple heading tokens belonging to one article. Put article groups in visual page reading order. "
            "Transcribe each grouped headline diplomatically from the image. Estimate the physical column count and x-bands. "
            "Extract visible issue metadata, attaching evidence tokens when one exists. Do not invent unreadable values."
        ),
        "response_contract": {
            "reader": "gpt-6-luna",
            "roles": {"TOKEN": "masthead|article_title|subheading|other"},
            "ordered_article_groups": [{"tokens": ["TOKEN"], "headline": "exact visible text"}],
            "columns": {"count": "integer", "x_bands_normalized": [[0.0, 1.0]]},
            "metadata": {
                "newspaper_title": {"value": "string|null", "evidence_tokens": ["TOKEN"]},
                "issue_date": {"value": "string|null", "evidence_tokens": ["TOKEN"]},
                "edition": {"value": "string|null", "evidence_tokens": ["TOKEN"]},
                "price": {"value": "string|null", "evidence_tokens": ["TOKEN"]},
                "issue_number": {"value": "string|null", "evidence_tokens": ["TOKEN"]}
            },
            "continued_or_anchorless_articles": [{"description": "visible evidence", "x_band": [0.0, 1.0]}],
            "uncertain_tokens": ["TOKEN"]
        },
        "prohibitions": [
            "Do not inspect any file outside this reader directory.",
            "Do not infer roles or order from token spelling or request-array order.",
            "Do not use or seek reference JSON, source IDs, article IDs, class IDs, or earlier model answers."
        ]
    }
    (reader / "request.json").write_text(json.dumps(request, indent=2, ensure_ascii=False) + "\n")
    sealed = {
        "schema": "bbvlm.finlam-anchor-sealed-map/1",
        "row_index": ROW_INDEX,
        "token_to_zone": mapping,
        "chosen_rule": "classes HEADER-TITLE, HEADER-TEXT, SECTION-TITLE, TITLE, SUBTITLE, INSIDEHEADING",
        "note": "Not available to the visual reader; A48 is consumed exploratory data after the CPU transfer score."
    }
    (EXP / "anchor-vlm/sealed-map.json").write_text(json.dumps(sealed, indent=2) + "\n")
    print(json.dumps({"tokens": len(mapping), "reader": str(reader)}, indent=2))


if __name__ == "__main__":
    main()
