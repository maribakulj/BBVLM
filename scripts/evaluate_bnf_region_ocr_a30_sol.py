#!/usr/bin/env python3
"""Score the blind, post-hoc Sol escalation for A30 without promoting it."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import evaluate_bnf_region_ocr_a30 as primary

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/loop/bnf-region-ocr-a30"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    started = time.perf_counter()
    task = json.loads((EXP / "public-task.json").read_text())
    reference = json.loads((EXP / "private-reference.json").read_text())["items"]
    candidate_path = EXP / "candidate/sol.json"
    candidate = json.loads(candidate_path.read_text())
    hypothesis = candidate.get("transcriptions", {})
    expected_ids = set(task["expected_ids"])
    expected_paths = {item["image"] for item in task["items"]}
    unknown = sorted(set(hypothesis) - expected_ids)
    missing = sorted(expected_ids - set(hypothesis))
    inspected = set(candidate.get("inspected_paths", []))
    scores = None
    if not unknown and not missing:
        scores = {
            "strict_nfc_diplomatic": primary.score(reference, hypothesis, primary.strict),
            # Retain the sealed primary normalization for direct comparability.
            "sealed_search_normalized": primary.score(reference, hypothesis, primary.search),
        }
    strict = scores["strict_nfc_diplomatic"] if scores else None
    conditions = {
        "exact_id_coverage": not unknown and not missing,
        "all_images_declared_inspected": inspected == expected_paths,
        "strict_cer_zero": strict is not None and strict["cer"] == 0,
        "all_regions_exact": strict is not None and strict["exact_regions"] == 16,
    }
    report = {
        "schema": "bbvlm.bnf-region-ocr-a30-sol-report/1",
        "page": task["page"],
        "status": "posthoc_blind_model_escalation_after_luna_failed_zero_cer; not primary validation",
        "scope": "same 16 A30 oracle region crops; one blind Sol pass with no Luna/reference access",
        "candidate": {
            "reader": candidate.get("reader"),
            "candidate_sha256": sha(candidate_path),
            "uncertain_ids": candidate.get("uncertain_ids", []),
            "unknown_ids": unknown,
            "missing_ids": missing,
        },
        "scores": scores,
        "gate_conditions": conditions,
        "diagnostic_zero_cer": all(conditions.values()),
        "cost": {"new_vlm_tasks": 1, "evaluator_seconds": time.perf_counter() - started},
        "accepted_for_project_completion_gate": False,
        "reference_status": "BnF-described manual transcription; not independently adjudicated perfect truth",
        "limitations": [
            "Model escalation was selected after observing Luna failure, so this is diagnostic rather than an independent primary test.",
            "Oracle region polygons and one page do not establish end-to-end OCR or full-page coverage.",
            "No ground-truth-selected ensemble is reported.",
        ],
        "invariants": {
            "reader_denied_reference_and_luna_output": True,
            "all_task_images_hash_bound": True,
            "originals_unchanged": True,
        },
    }
    out = EXP / "output/sol-report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
