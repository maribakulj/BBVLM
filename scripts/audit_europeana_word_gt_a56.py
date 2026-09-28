#!/usr/bin/env python3
"""Audit PAGE XML granularity/provenance in Zenodo record 2583866."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


EXPECTED_MD5 = "02598a36eb09d50ccb6276f87d81be6c"


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def text_value(element: ET.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    value = element.text.strip()
    return value or None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw = args.archive.read_bytes()
    md5 = hashlib.md5(raw).hexdigest()  # nosec B324: dataset identity, not security
    sha256 = hashlib.sha256(raw).hexdigest()
    element_totals: Counter[str] = Counter()
    per_file: list[dict[str, object]] = []
    namespaces: Counter[str] = Counter()
    creators: Counter[str] = Counter()
    last_changes: Counter[str] = Counter()

    with zipfile.ZipFile(args.archive) as archive:
        xml_names = sorted(n for n in archive.namelist() if n.lower().endswith(".xml"))
        for name in xml_names:
            root = ET.fromstring(archive.read(name))
            counts = Counter(local(node.tag) for node in root.iter())
            element_totals.update(counts)
            namespace = root.tag.split("}", 1)[0].lstrip("{") if "}" in root.tag else ""
            namespaces[namespace] += 1
            metadata = next((n for n in root.iter() if local(n.tag) == "Metadata"), None)
            metadata_children = list(metadata) if metadata is not None else []
            creator = next((n for n in metadata_children if local(n.tag) == "Creator"), None)
            changed = next((n for n in metadata_children if local(n.tag) == "LastChange"), None)
            creators[text_value(creator) or "<missing>"] += 1
            last_changes[text_value(changed) or "<missing>"] += 1
            page = next((n for n in root.iter() if local(n.tag) == "Page"), None)
            per_file.append(
                {
                    "name": name,
                    "counts": dict(sorted(counts.items())),
                    "image_filename": page.get("imageFilename") if page is not None else None,
                    "image_width": int(page.get("imageWidth", "0")) if page is not None else None,
                    "image_height": int(page.get("imageHeight", "0")) if page is not None else None,
                }
            )

    word_files = sum(int(item["counts"].get("Word", 0) > 0) for item in per_file)
    line_files = sum(int(item["counts"].get("TextLine", 0) > 0) for item in per_file)
    glyph_files = sum(int(item["counts"].get("Glyph", 0) > 0) for item in per_file)
    region_files = sum(int(item["counts"].get("TextRegion", 0) > 0) for item in per_file)
    report = {
        "source": {
            "record": "https://doi.org/10.5281/zenodo.2583866",
            "archive": str(args.archive),
            "bytes": len(raw),
            "md5": md5,
            "expected_md5": EXPECTED_MD5,
            "md5_matches": md5 == EXPECTED_MD5,
            "sha256": sha256,
        },
        "files": len(per_file),
        "namespaces": dict(namespaces),
        "creators": dict(creators),
        "last_changes": dict(last_changes),
        "element_totals": dict(sorted(element_totals.items())),
        "files_with": {
            "TextRegion": region_files,
            "TextLine": line_files,
            "Word": word_files,
            "Glyph": glyph_files,
        },
        "eligibility": {
            "word_geometry": word_files == len(per_file) and len(per_file) > 0,
            "line_geometry": line_files == len(per_file) and len(per_file) > 0,
            "region_geometry": region_files == len(per_file) and len(per_file) > 0,
            "manual_or_adjudicated_geometry_provenance": False,
            "note": (
                "The XML producer string is descriptive, not evidence of manual geometry. "
                "Manual/adjudicated provenance must be established from release documentation."
            ),
        },
        "per_file": per_file,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("files", "creators", "element_totals", "files_with", "eligibility")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
