#!/usr/bin/env python3
"""Post-score A30 convention/reference audit; never edits truth or candidates."""
from __future__ import annotations

import difflib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from bbvlm.metrics import edit_distance

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/loop/bnf-region-ocr-a30"


def strict(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in unicodedata.normalize("NFC", text).strip().split("\n"))


def retrieval(text: str) -> str:
    """Search view: unify dash code points before joining line-end hyphenation."""
    text = unicodedata.normalize("NFKC", strict(text)).lower()
    text = text.replace("’", "'").replace("‘", "'")
    text = re.sub("[\\u2010\\u2011\\u2012\\u2013\\u2014\\u2212]", "-", text)
    text = re.sub(r"-\n(?=\w)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def score(reference: dict, hypothesis: dict, view) -> dict:
    rows = []
    for token in sorted(reference):
        ref = view(reference[token]["reference"])
        hyp = view(hypothesis[token])
        edits = edit_distance(ref, hyp)
        rows.append({"id": token, "characters": len(ref), "edits": edits, "exact": ref == hyp})
    chars = sum(row["characters"] for row in rows)
    edits = sum(row["edits"] for row in rows)
    return {
        "characters": chars,
        "edits": edits,
        "cer": edits / chars,
        "exact_regions": sum(row["exact"] for row in rows),
        "per_region": rows,
    }


def substitutions(reference: dict, hypothesis: dict) -> Counter:
    counts = Counter()
    for token in sorted(reference):
        ref = strict(reference[token]["reference"])
        hyp = strict(hypothesis[token])
        for tag, i0, i1, j0, j1 in difflib.SequenceMatcher(None, ref, hyp).get_opcodes():
            if tag == "replace" and i1 - i0 == 1 and j1 - j0 == 1:
                counts[f"U+{ord(ref[i0]):04X}->{f'U+{ord(hyp[j0]):04X}'}"] += 1
    return counts


def candidate_audit(name: str, reference: dict, candidate_path: Path) -> dict:
    candidate = json.loads(candidate_path.read_text())
    hypothesis = candidate["transcriptions"]
    return {
        "reader": candidate.get("reader"),
        "corrected_retrieval_view": score(reference, hypothesis, retrieval),
        "single_codepoint_substitutions": dict(substitutions(reference, hypothesis).most_common()),
        "reference_replacement_character_ids": [
            token for token, item in reference.items() if "\ufffd" in item["reference"]
        ],
    }


def main() -> None:
    reference = json.loads((EXP / "private-reference.json").read_text())["items"]
    candidates = {"luna": candidate_audit("luna", reference, EXP / "candidate/luna.json")}
    sol = EXP / "candidate/sol.json"
    if sol.exists():
        candidates["sol"] = candidate_audit("sol", reference, sol)
    report = {
        "schema": "bbvlm.bnf-region-ocr-a30-post-score-audit/1",
        "status": "diagnostic_after_scoring; sealed strict metric, references and candidates unchanged",
        "candidates": candidates,
        "reference_flags": {
            "replacement_character": ["T003"],
            "visual_adjudication_needed": ["T006", "T007", "T008", "T014"],
            "reason": "Manual transcription is a strong reference, not axiomatic truth; flags are hypotheses and are not corrections.",
        },
        "interpretation": [
            "The primary strict score remains the sealed score and includes Unicode hyphen-codepoint disagreements.",
            "The corrected retrieval view maps dash variants before joining line-end hyphenation; it is a post-score diagnostic only.",
            "Neither model agreement nor a lower normalized CER adjudicates disputed source/reference readings.",
        ],
    }
    out = EXP / "post-score"
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
