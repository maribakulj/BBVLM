#!/usr/bin/env python3
"""Record the completed Europeana PAGE granularity audit A56."""

from __future__ import annotations

import json
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOOP = ROOT / "experiments/loop"


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    report = json.loads((LOOP / "europeana-word-gt-a56/audit.json").read_text())
    checkpoint_path = LOOP / "CHECKPOINT.json"
    checkpoint = json.loads(checkpoint_path.read_text())
    phase = {
        "id": "europeana_word_gt_a56_audit",
        "complete": True,
        "script": "scripts/audit_europeana_word_gt_a56.py",
        "result": "europeana-word-gt-a56/audit.json",
    }
    if phase["id"] not in {row["id"] for row in checkpoint["phases"]}:
        checkpoint["phases"].append(phase)
    checkpoint["evidence"]["europeana_word_gt_a56"] = {
        "status": "complete_rejected_for_word_and_line_geometry",
        "source": report["source"],
        "files": report["files"],
        "element_totals": report["element_totals"],
        "files_with": report["files_with"],
        "eligibility": report["eligibility"],
        "cost": {"vlm_passes": 0, "ocr_passes": 0, "images_downloaded": 0},
        "accepted_for_project_completion_gate": False,
    }
    note = (
        "A56 audited every PAGE XML in Zenodo 2583866: 2458 TextRegions and region reading order, "
        "but 0 TextLine, 0 Word and 0 Glyph nodes. Reject it for ALTO word/line-box truth without "
        "downloading images; retain only as a possible region/OLR reference after provenance audit. "
        "Next inspect the Claude branch, then audit Chronicling Germany's expert region polygons and "
        "weaker selectively corrected line layer as separate truth grades."
    )
    checkpoint["next_research"] = [note] + [
        item for item in checkpoint["next_research"] if not item.startswith("A56 audited")
    ]
    checkpoint["updated_unix"] = time.time()
    checkpoint["status"] = "in_progress"
    write(checkpoint_path, checkpoint)

    protocol_path = LOOP / "protocol.json"
    protocol = json.loads(protocol_path.read_text())
    protocol["europeana_word_gt_a56"] = {
        "status": "complete_negative_corpus_audit",
        "protocol": "europeana-word-gt-a56/PROTOCOL.md",
        "report": "europeana-word-gt-a56/audit.json",
        "result": "europeana-word-gt-a56/RESULTS.md",
        "word_geometry": False,
        "line_geometry": False,
        "region_geometry": True,
        "global_completion": False,
    }
    protocol["status"] = "in_progress"
    write(protocol_path, protocol)


if __name__ == "__main__":
    main()
