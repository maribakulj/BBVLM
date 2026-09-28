#!/usr/bin/env python3
"""Mechanically record the completed A54 experiment in checkpoint/protocol JSON."""
from __future__ import annotations

import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[1]
LOOP = ROOT / "experiments/loop"
REPORT = json.loads((LOOP / "bnl-independent-a54/vlm-report.json").read_text())
BASELINE = json.loads((LOOP / "bnl-independent-a54/output/report.json").read_text())


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    checkpoint_path = LOOP / "CHECKPOINT.json"
    checkpoint = json.loads(checkpoint_path.read_text())
    phase_rows = [
        {"id": "bnl_independent_a54_freeze", "complete": True, "script": None,
         "result": "bnl-independent-a54/split.json"},
        {"id": "bnl_independent_a54_infer", "complete": True,
         "script": "scripts/run_bnl_independent_a54.py", "result": "bnl-independent-a54/output/predictions.json"},
        {"id": "bnl_independent_a54_prepare", "complete": True,
         "script": "scripts/prepare_bnl_vlm_a54.py", "result": "bnl-independent-a54/vlm-input/request.json"},
        {"id": "bnl_independent_a54_evaluate", "complete": True,
         "script": "scripts/evaluate_bnl_vlm_a54.py", "result": "bnl-independent-a54/vlm-report.json"},
    ]
    known = {row["id"] for row in checkpoint["phases"]}
    checkpoint["phases"].extend(row for row in phase_rows if row["id"] not in known)
    checkpoint["evidence"]["bnl_guarded_vlm_a54"] = {
        "status": "predeclared_local_gates_passed_global_project_gates_open",
        "independent": True,
        "sample": REPORT["sample"],
        "aggregate": REPORT["aggregate"],
        "predeclared_gates": REPORT["predeclared_gates"],
        "guard_summary": REPORT["guard_summary"],
        "geometry": BASELINE["aggregate"],
        "cost": REPORT["cost"] | BASELINE["cost"],
        "accepted_for_project_completion_gate": False,
        "limitations": REPORT["interpretation_limits"],
    }
    note = ("A54 independent 16-block result: one blind image+PERO Luna pass with a frozen localized-edit guard "
            "reduces search_v1 CER .9330%->.6831% and lexical CER .5288%->.3110%, with zero regression among "
            "already exact PERO blocks; both local gates pass. It is not zero (82 search edits, 30 lexical edits), "
            "two non-exact blocks worsen, and routed word IoU80 is .3354 overall/.1581 French. Keep the VLM for "
            "guarded text/semantics, not coordinates. Develop geometry only on consumed A54, then freeze new data; "
            "all seven global gates remain false.")
    checkpoint["next_research"] = [note] + [item for item in checkpoint["next_research"] if not item.startswith("A54 independent")]
    checkpoint["updated_unix"] = time.time()
    checkpoint["status"] = "in_progress"
    write(checkpoint_path, checkpoint)

    protocol_path = LOOP / "protocol.json"
    protocol = json.loads(protocol_path.read_text())
    protocol["bnl_guarded_vlm_a54"] = {
        "status": "complete_local_gates_passed",
        "split": "bnl-independent-a54/split.json",
        "protocol": "bnl-independent-a54/PROTOCOL.md",
        "report": "bnl-independent-a54/vlm-report.json",
        "frozen_sample": 16,
        "excludes_a45": True,
        "reader": "gpt-6-luna",
        "passes": 1,
        "primary_gate": REPORT["predeclared_gates"]["guarded_search_v1"],
        "secondary_gate": REPORT["predeclared_gates"]["guarded_lexical_alnum"],
        "global_completion": False,
    }
    protocol["status"] = "in_progress"
    write(protocol_path, protocol)


if __name__ == "__main__":
    main()
