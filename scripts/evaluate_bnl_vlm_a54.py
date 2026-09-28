#!/usr/bin/env python3
"""Open A54 references and score PERO, Luna, and deterministic guard variants."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from bbvlm.metrics import edit_distance
from bbvlm.text_views import diplomatic_nfc, lexical_alnum, search_v1


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/loop/bnl-independent-a54"
NS = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}
VIEWS = {"strict_nfc_diplomatic": diplomatic_nfc, "search_v1": search_v1,
         "lexical_alnum": lexical_alnum}


def reference_text(identifier: str) -> str:
    root = ET.parse(EXP / "source" / f"{identifier}.xml").getroot()
    return "\n".join(" ".join(word.attrib.get("CONTENT", "") for word in line.findall("a:String", NS))
                     for line in root.findall(".//a:TextLine", NS))


def measures(reference: str, hypothesis: str) -> dict:
    out = {}
    for name, transform in VIEWS.items():
        left, right = transform(reference), transform(hypothesis)
        edits = edit_distance(left, right)
        out[name] = {"characters": len(left), "edits": edits,
                     "cer": edits / len(left) if left else None, "exact": left == right}
    return out


def validate_and_apply(candidate: str, answer: dict) -> tuple[str, dict]:
    text = answer.get("text")
    decision = answer.get("decision")
    edits = answer.get("edits")
    reasons = []
    if not isinstance(text, str):
        return candidate, {"accepted": False, "reasons": ["text_not_string"]}
    if decision not in {"keep", "edit"} or not isinstance(edits, list):
        return candidate, {"accepted": False, "reasons": ["invalid_decision_or_edits"]}
    reconstructed = candidate
    for index, edit in enumerate(edits):
        if not isinstance(edit, dict):
            reasons.append(f"edit_{index}_not_object"); continue
        before, after, reason = edit.get("before"), edit.get("after"), edit.get("visual_reason")
        if not all(isinstance(value, str) for value in (before, after, reason)) or not before or not reason.strip():
            reasons.append(f"edit_{index}_invalid_fields"); continue
        occurrences = reconstructed.count(before)
        if occurrences != 1:
            reasons.append(f"edit_{index}_before_occurrences_{occurrences}"); continue
        reconstructed = reconstructed.replace(before, after, 1)
    if decision == "keep" and edits:
        reasons.append("keep_has_edits")
    if decision == "edit" and not edits:
        reasons.append("edit_has_no_edits")
    if search_v1(reconstructed) != search_v1(text):
        reasons.append("declared_edits_do_not_reconstruct_search_text")
    accepted = not reasons
    return (text if accepted else candidate), {"accepted": accepted, "reasons": reasons,
                                                "declared_edits": len(edits),
                                                "uncertain": bool(answer.get("uncertain"))}


def aggregate(rows: list[dict], system: str, ids: set[str]) -> dict:
    chosen = [row for row in rows if row["source_id"] in ids]
    result = {}
    for view in VIEWS:
        characters = sum(row[system][view]["characters"] for row in chosen)
        edits = sum(row[system][view]["edits"] for row in chosen)
        result[view] = {"characters": characters, "edits": edits,
                        "cer": edits / characters if characters else None,
                        "exact_blocks": sum(row[system][view]["exact"] for row in chosen)}
    return {"blocks": len(chosen), "text": result}


def gate(rows: list[dict], candidate: str, challenger: str, view: str) -> dict:
    candidate_edits = sum(row[candidate][view]["edits"] for row in rows)
    challenger_edits = sum(row[challenger][view]["edits"] for row in rows)
    exact_ids = [row["opaque_id"] for row in rows if row[candidate][view]["exact"]]
    regressions = [row["opaque_id"] for row in rows
                   if row[candidate][view]["exact"] and not row[challenger][view]["exact"]]
    return {"candidate_edits": candidate_edits, "challenger_edits": challenger_edits,
            "aggregate_improved": challenger_edits < candidate_edits,
            "candidate_exact_blocks": exact_ids, "exact_block_regressions": regressions,
            "passed": challenger_edits < candidate_edits and not regressions}


def main() -> None:
    request = json.loads((EXP / "vlm-input/request.json").read_text())
    mapping = json.loads((EXP / "vlm-input/private-map.json").read_text())["mapping"]
    response = json.loads((EXP / "luna-response.json").read_text())
    answers = {row["id"]: row for row in response.get("items", [])}
    expected = set(mapping)
    if set(answers) != expected or len(response.get("items", [])) != len(expected):
        raise ValueError("Luna response IDs are not a unique exact match")
    request_by_id = {row["id"]: row for row in request["items"]}
    rows = []
    for opaque_id, source_id in mapping.items():
        candidate = request_by_id[opaque_id]["pero_candidate"]
        if hashlib.sha256(candidate.encode()).hexdigest() != request_by_id[opaque_id]["candidate_sha256"]:
            raise ValueError(f"candidate seal failed for {opaque_id}")
        guarded, guard = validate_and_apply(candidate, answers[opaque_id])
        abstaining = candidate if guard.get("uncertain") else guarded
        reference = reference_text(source_id)
        rows.append({"opaque_id": opaque_id, "source_id": source_id, "guard": guard,
                     "pero": measures(reference, candidate),
                     "luna_raw": measures(reference, answers[opaque_id]["text"]),
                     "luna_guarded": measures(reference, guarded),
                     "luna_guarded_abstain": measures(reference, abstaining)})
    audit = json.loads((EXP / "audit.json").read_text())
    languages = {row["id"]: row["language_prediction"] for row in audit["rows"]}
    all_ids = set(mapping.values())
    french_ids = {identifier for identifier in all_ids if languages[identifier] == "fr"}
    systems = ["pero", "luna_raw", "luna_guarded", "luna_guarded_abstain"]
    report = {
        "schema": "bbvlm.bnl-independent-a54-vlm-report/1",
        "status": "frozen_independent_evaluation_complete",
        "sample": {"all_blocks": len(all_ids), "french_blocks": len(french_ids)},
        "aggregate": {stratum: {system: aggregate(rows, system, ids) for system in systems}
                      for stratum, ids in (("all", all_ids), ("french", french_ids))},
        "predeclared_gates": {
            "guarded_search_v1": gate(rows, "pero", "luna_guarded", "search_v1"),
            "guarded_lexical_alnum": gate(rows, "pero", "luna_guarded", "lexical_alnum")},
        "diagnostic_gates": {
            "raw_search_v1": gate(rows, "pero", "luna_raw", "search_v1"),
            "uncertainty_abstain_search_v1": gate(rows, "pero", "luna_guarded_abstain", "search_v1")},
        "guard_summary": {"accepted_blocks": sum(row["guard"]["accepted"] for row in rows),
                          "rejected_blocks": sum(not row["guard"]["accepted"] for row in rows),
                          "uncertain_blocks": sum(row["guard"].get("uncertain", False) for row in rows)},
        "cost": {"new_vlm_passes": 1, "vlm_items_in_single_pass": len(rows),
                 "pero_recognizer_forwards": sum(block["predicted_lines"] for block in
                                                 json.loads((EXP / "output/predictions.json").read_text())["blocks"])},
        "reference_status": "provider says double-keyed >=99.95%; immutable original XML retained; not perfect truth",
        "interpretation_limits": [
            "This block sample cannot validate page columns, article grouping, metadata, or full-page OLR.",
            "Prompted uncertainty is diagnostic: recent evidence finds it poorly calibrated for OCR.",
            "A gate pass would validate this frozen correction protocol, not certify universal 0% CER."
        ],
        "rows": rows,
    }
    output = EXP / "vlm-report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    compact = dict(report); compact.pop("rows")
    print(json.dumps(compact, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
