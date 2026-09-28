#!/usr/bin/env python3
"""Prepare blind, exact-input OCR views for A52.

The two pages were already consumed by Claude O02, so this is a development
replication, never an independent validation.  References are deliberately not
copied into the public task directory.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/loop/crossbranch-ocr-a52"
PAGES = {
    "A52-P01": ROOT
    / "experiments/loop/french-word-gt-a28/source/data/borrdisc_689809840/"
    "OCR-D-IMG/OCR-D-IMG_00000019.tif",
    "A52-P02": ROOT
    / "experiments/loop/word-transfer-a34/source/data/drabnota_771639139/"
    "OCR-D-IMG/OCR-D-IMG_00000389.tif",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def prepare_one(opaque_id: str, source: Path) -> dict:
    target = OUT / "input" / opaque_id
    target.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as raw:
        img = raw.convert("RGB")
    width, height = img.size

    page = img.copy()
    page.thumbnail((1350, 1350), Image.Resampling.LANCZOS)
    page_path = target / "view_0_page_1350.png"
    page.save(page_path)

    # Claude's O02/O04 geometry: 600-pixel source bands, 120-pixel overlap.
    bands = []
    y0, index = 0, 1
    while True:
        y1 = min(height, y0 + 600)
        crop = img.crop((0, y0, width, y1))
        band_path = target / f"view_{index}_band.png"
        crop.save(band_path)

        margin = int(width * 0.12 / 2)
        halves = {
            "left": (0, 0, width // 2 + margin, crop.height),
            "right": (width // 2 - margin, 0, width, crop.height),
        }
        zoom_paths = []
        for side, box in halves.items():
            half = crop.crop(box)
            half = half.resize(
                (round(half.width * 1.6), round(half.height * 1.6)),
                Image.Resampling.BICUBIC,
            )
            zoom_path = target / f"zoom_{index}_{side}_x1.6.png"
            half.save(zoom_path)
            zoom_paths.append(str(zoom_path.relative_to(ROOT)))
        bands.append(
            {
                "index": index,
                "source_y": [y0, y1],
                "band": str(band_path.relative_to(ROOT)),
                "zoom": zoom_paths,
            }
        )
        if y1 == height:
            break
        y0 = y1 - 120
        index += 1

    return {
        "opaque_id": opaque_id,
        "source_sha256": sha256(source),
        "source_size": [width, height],
        "page_view": str(page_path.relative_to(ROOT)),
        "bands": bands,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "bbvlm.a52-task/1",
        "status": "development_cross_branch_replication",
        "blind": True,
        "consumed_elsewhere": True,
        "views": "whole page max 1350 + 600px bands/120px overlap + half-band x1.6",
        "pages": [prepare_one(k, v) for k, v in PAGES.items()],
    }
    (OUT / "public-task.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
