#!/usr/bin/env python3
"""Verify the local HIPE character alignment against jiwer on frozen A54 pairs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "vendor/a64"))

import jiwer

from bbvlm.hipe_metrics import UPSTREAM_REVISION, alignment_counts, hipe_normalize
from evaluate_bnl_vlm_a54 import reference_text, validate_and_apply


EXP = ROOT / "experiments/loop/bnl-independent-a54"
OUT = ROOT / "experiments/loop/hipe-projection-a64"


def main() -> None:
    request = json.loads((EXP / "vlm-input/request.json").read_text())
    mapping = json.loads((EXP / "vlm-input/private-map.json").read_text())["mapping"]
    response = json.loads((EXP / "luna-response.json").read_text())
    request_by_id = {row["id"]: row for row in request["items"]}
    answer_by_id = {row["id"]: row for row in response["items"]}
    comparisons = []
    for opaque_id, source_id in mapping.items():
        candidate = request_by_id[opaque_id]["pero_candidate"]
        if hashlib.sha256(candidate.encode()).hexdigest() != request_by_id[opaque_id]["candidate_sha256"]:
            raise ValueError(f"candidate seal failed for {opaque_id}")
        answer = answer_by_id[opaque_id]
        guarded, guard = validate_and_apply(candidate, answer)
        hypotheses = {
            "pero": candidate,
            "luna_raw": answer["text"],
            "luna_guarded": guarded,
            "luna_guarded_abstain": candidate if guard.get("uncertain") else guarded,
        }
        reference = hipe_normalize(reference_text(source_id))
        for system, text in hypotheses.items():
            hypothesis = hipe_normalize(text)
            local = alignment_counts(reference, hypothesis)
            official = jiwer.process_characters(reference, hypothesis)
            upstream = {
                "hits": official.hits,
                "substitutions": official.substitutions,
                "deletions": official.deletions,
                "insertions": official.insertions,
            }
            comparisons.append({"id": opaque_id, "system": system,
                                "local": local, "jiwer": upstream,
                                "match": local == upstream})
    mismatches = [row for row in comparisons if not row["match"]]
    report = {
        "schema": "bbvlm.hipe-alignment-verification-a64/1",
        "upstream_scorer_revision": UPSTREAM_REVISION,
        "jiwer_version": getattr(jiwer, "__version__", "unknown"),
        "comparison_count": len(comparisons),
        "all_counts_match": not mismatches,
        "mismatches": mismatches,
        "scope": "All four frozen A54 systems over all 16 blocks after exact HIPE normalization",
        "scientific_gate": False,
    }
    OUT.mkdir(exist_ok=True)
    (OUT / "implementation-verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if mismatches:
        raise SystemExit("local alignment counts differ from jiwer")


if __name__ == "__main__":
    main()
