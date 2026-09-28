#!/usr/bin/env python3
"""Project the frozen A54 comparison into HIPE-OCRepair 0.9.9 metrics."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from bbvlm.hipe_metrics import UPSTREAM_REVISION, cmer
from evaluate_bnl_vlm_a54 import reference_text, validate_and_apply


EXP = ROOT / "experiments/loop/bnl-independent-a54"
OUT = ROOT / "experiments/loop/hipe-projection-a64"


def aggregate(rows: list[dict], system: str) -> dict:
    values = [row[system] for row in rows]
    errors = sum(value["errors"] for value in values)
    denominator = sum(value["denominator"] for value in values)
    return {"blocks": len(values), "errors": errors, "denominator": denominator,
            "cmer_micro": errors / denominator if denominator else 0.0,
            "exact_blocks": sum(value["exact"] for value in values)}


def main() -> None:
    started = time.perf_counter()
    request = json.loads((EXP / "vlm-input/request.json").read_text())
    mapping = json.loads((EXP / "vlm-input/private-map.json").read_text())["mapping"]
    response = json.loads((EXP / "luna-response.json").read_text())
    request_by_id = {row["id"]: row for row in request["items"]}
    answer_by_id = {row["id"]: row for row in response["items"]}
    if set(mapping) != set(request_by_id) or set(mapping) != set(answer_by_id):
        raise ValueError("A54 inventories differ")
    rows = []
    for opaque_id, source_id in mapping.items():
        candidate = request_by_id[opaque_id]["pero_candidate"]
        if hashlib.sha256(candidate.encode()).hexdigest() != request_by_id[opaque_id]["candidate_sha256"]:
            raise ValueError(f"candidate seal failed for {opaque_id}")
        answer = answer_by_id[opaque_id]
        guarded, guard = validate_and_apply(candidate, answer)
        abstaining = candidate if guard.get("uncertain") else guarded
        reference = reference_text(source_id)
        rows.append({"id": opaque_id, "source_id": source_id,
                     "guard_accepted": guard["accepted"], "uncertain": guard.get("uncertain", False),
                     "pero": cmer(reference, candidate), "luna_raw": cmer(reference, answer["text"]),
                     "luna_guarded": cmer(reference, guarded),
                     "luna_guarded_abstain": cmer(reference, abstaining)})
    systems = ("pero", "luna_raw", "luna_guarded", "luna_guarded_abstain")
    summary = {system: aggregate(rows, system) for system in systems}
    for system in systems[1:]:
        comparisons = []
        for row in rows:
            comparisons.append(1 if row[system]["cmer"] < row["pero"]["cmer"] else
                               -1 if row[system]["cmer"] > row["pero"]["cmer"] else 0)
        summary[system]["preference_vs_pero"] = {
            "improved": comparisons.count(1), "tied": comparisons.count(0),
            "degraded": comparisons.count(-1), "macro": sum(comparisons) / len(comparisons)}
    old = json.loads((EXP / "vlm-report.json").read_text())["aggregate"]["all"]
    report = {
        "schema": "bbvlm.hipe-projection-a64/1",
        "status": "completed_frozen_metric_projection",
        "source_evaluation": "A54 frozen independent 16-block comparison, now consumed",
        "upstream": {"repository": "hipe-eval/HIPE-OCRepair-scorer",
                     "revision": UPSTREAM_REVISION, "version": "0.9.9",
                     "implementation_read": "hipe_ocrepair_scorer/ocrepair_eval.py"},
        "summary": summary,
        "existing_views_for_comparison": old,
        "rows": rows,
        "cost": {"new_ocr_vlm_or_detector_forwards": 0,
                 "evaluator_seconds": time.perf_counter() - started},
        "reference_unchanged": True,
        "global_completion": False,
        "limitations": [
            "Metric projection on consumed A54; no new independent generalization evidence.",
            "HIPE normalization is not diplomatic and a zero cMER would not imply exact transcription.",
            "Probable BnL reference errors remain; agreement is not visual adjudication.",
            "No geometry, OLR, metadata or retrieval evidence is added.",
        ],
    }
    OUT.mkdir(exist_ok=True)
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"summary": summary, "cost": report["cost"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
