#!/usr/bin/env python3
"""Record completed consumed-data geometry diagnostic A55."""
from __future__ import annotations

import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[1]
LOOP = ROOT / "experiments/loop"
DIAG = json.loads((LOOP / "bnl-geometry-a55/report.json").read_text())
WIDTH = json.loads((LOOP / "bnl-geometry-a55/width-guard-report.json").read_text())


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    checkpoint_path = LOOP / "CHECKPOINT.json"
    checkpoint = json.loads(checkpoint_path.read_text())
    phases = [
        {"id": "bnl_geometry_a55_diagnose", "complete": True,
         "script": "scripts/diagnose_bnl_geometry_a55.py", "result": "bnl-geometry-a55/report.json"},
        {"id": "bnl_geometry_a55_width_guard", "complete": True,
         "script": "scripts/develop_width_guard_a55.py", "result": "bnl-geometry-a55/width-guard-report.json"},
    ]
    known = {row["id"] for row in checkpoint["phases"]}
    checkpoint["phases"].extend(row for row in phases if row["id"] not in known)
    checkpoint["evidence"]["bnl_geometry_a55"] = {
        "status": "consumed_diagnostic_complete_candidate_rejected",
        "independent": False,
        "aggregate": DIAG["aggregate"],
        "width_guard": {"candidates": WIDTH["candidates"], "selected": WIDTH["selected"]},
        "accepted_for_project_completion_gate": False,
        "limitations": [DIAG["reference_status"], "A54 input was already consumed"],
    }
    note = ("A55 consumed A54 edge diagnostic: A37 improves all-word mean IoU .5807->.6685 but French "
            "horizontal IoU falls .8245->.8077 and three French blocks regress. A preregistered width-cap "
            "grid has no eligible candidate; reject it. BnL word rectangles are not certified perfect GT. "
            "Next freeze a word-geometry corpus with explicit manual control before any new promotion.")
    checkpoint["next_research"] = [note] + [x for x in checkpoint["next_research"] if not x.startswith("A55 consumed")]
    checkpoint["updated_unix"] = time.time()
    checkpoint["status"] = "in_progress"
    write(checkpoint_path, checkpoint)

    protocol_path = LOOP / "protocol.json"
    protocol = json.loads(protocol_path.read_text())
    protocol["bnl_geometry_a55"] = {
        "status": "complete_negative_development",
        "protocol": "bnl-geometry-a55/PROTOCOL.md",
        "width_guard_protocol": "bnl-geometry-a55/WIDTH_GUARD_PROTOCOL.md",
        "report": "bnl-geometry-a55/report.json",
        "width_guard_report": "bnl-geometry-a55/width-guard-report.json",
        "independent": False,
        "selected": None,
        "global_completion": False,
    }
    protocol["status"] = "in_progress"
    write(protocol_path, protocol)


if __name__ == "__main__":
    main()

