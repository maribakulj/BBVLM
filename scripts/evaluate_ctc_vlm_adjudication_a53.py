#!/usr/bin/env python3
"""Evaluate the frozen A53 response against the held-back SBB derivative."""
from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path

from bbvlm.ocr_conventions import transform
from bbvlm.text_views import retrieval_fold_v1


def lev(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    row = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        nxt = [i]
        for j, cb in enumerate(b, 1):
            nxt.append(min(row[j] + 1, nxt[-1] + 1, row[j - 1] + (ca != cb)))
        row = nxt
    return row[-1]


def view(text: str, profile: str) -> str:
    text = unicodedata.normalize("NFC", text)
    if profile == "strict":
        return text
    if profile == "diplomatic":
        return transform(text, "glyph_decomposition_v1")
    if profile == "retrieval_fold_v1":
        return retrieval_fold_v1(transform(text, "glyph_decomposition_v1"))
    raise ValueError(profile)


def aggregate(refs: dict[str, str], hyps: dict[str, str], profile: str) -> dict:
    rows = []
    for line_id in sorted(refs):
        ref, hyp = view(refs[line_id], profile), view(hyps[line_id], profile)
        rows.append({"id": line_id, "reference": ref, "hypothesis": hyp,
                     "characters": len(ref), "edits": lev(ref, hyp)})
    chars = sum(row["characters"] for row in rows)
    edits = sum(row["edits"] for row in rows)
    return {"characters": chars, "edits": edits, "cer": edits / chars if chars else None,
            "exact_lines": sum(row["edits"] == 0 for row in rows), "lines": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("experiments/loop/ctc-vlm-adjudication-a53"))
    parser.add_argument("--response", default="luna-response-bound.json")
    args = parser.parse_args()
    base = args.root
    private = json.loads((base / "private-evaluation.json").read_text(encoding="utf-8"))
    response = json.loads((base / args.response).read_text(encoding="utf-8"))
    expected = {item["id"]: item for item in private["items"]}
    received: dict[str, dict] = {}
    for item in response.get("items", []):
        line_id = item.get("id")
        if line_id not in expected or line_id in received:
            raise ValueError(f"unknown or duplicate response ID: {line_id!r}")
        if item.get("choice") not in {"A", "B", "NEITHER"}:
            raise ValueError(f"invalid choice for {line_id}")
        if not isinstance(item.get("text"), str) or not item["text"]:
            raise ValueError(f"missing text for {line_id}")
        if item["choice"] in {"A", "B"} and item["text"] != expected[line_id]["options"][item["choice"]]:
            raise ValueError(f"selected option text changed for {line_id}")
        received[line_id] = item
    if set(received) != set(expected):
        raise ValueError(f"response identity mismatch: missing={sorted(set(expected)-set(received))}")

    refs = {line_id: item["reference"] for line_id, item in expected.items()}
    vlm, ctc = {}, {}
    for line_id, item in expected.items():
        by_source = {source: item["options"][label] for label, source in item["provenance"].items()}
        vlm[line_id], ctc[line_id] = by_source["vlm"], by_source["ctc"]
    adjudicated = {line_id: item["text"] for line_id, item in received.items()}

    scores = {}
    for name, hypotheses in (("vlm", vlm), ("ctc", ctc), ("luna_adjudicated", adjudicated)):
        scores[name] = {profile: aggregate(refs, hypotheses, profile)
                        for profile in ("strict", "diplomatic", "retrieval_fold_v1")}

    line_decisions = []
    exact_candidate_regressions = 0
    selected_reference_winner = 0
    ctc_margin_predicts_reference_winner = 0
    comparable_margins = 0
    for line_id, item in expected.items():
        ref = view(item["reference"], "diplomatic")
        edits = {label: lev(ref, view(text, "diplomatic")) for label, text in item["options"].items()}
        best = min(edits.values())
        chosen = received[line_id]["choice"]
        chosen_edits = lev(ref, view(received[line_id]["text"], "diplomatic"))
        if chosen_edits == best:
            selected_reference_winner += 1
        if best == 0 and chosen_edits > 0:
            exact_candidate_regressions += 1
        costs = item["ctc_viterbi_nll_per_frame"]
        finite = {label: value for label, value in costs.items() if value is not None}
        margin_pick = min(finite, key=finite.get) if len(finite) == 2 else None
        if margin_pick:
            comparable_margins += 1
            if edits[margin_pick] == best:
                ctc_margin_predicts_reference_winner += 1
        line_decisions.append({"id": line_id, "choice": chosen, "uncertain": bool(received[line_id].get("uncertain")),
                               "reference_edits_by_option": edits, "chosen_edits": chosen_edits,
                               "ctc_viterbi_nll_per_frame": costs, "ctc_margin_pick": margin_pick})

    strict_best = min(scores["vlm"]["strict"]["cer"], scores["ctc"]["strict"]["cer"])
    report = {
        "schema": "bbvlm.ctc-vlm-adjudication-report/1",
        "experiment_class": "consumed_development_diagnostic",
        "independent": False,
        "reader": response.get("reader"),
        "transport": {"raw_response": "luna-response.json", "scored_response": args.response,
                      "repair": "same reader copied frozen selected-option text into empty A/B fields; choices unchanged"},
        "cost": {"new_vlm_passes": 1, "images_sent": len(expected), "layout_reruns": 0,
                 "recognizer_reruns": 0, "ctc_logits": "cached A23"},
        "scores": scores,
        "selection": {"lines": len(expected), "reference_winner_or_tie": selected_reference_winner,
                      "exact_candidate_regressions": exact_candidate_regressions,
                      "neither": sum(item["choice"] == "NEITHER" for item in received.values()),
                      "uncertain": sum(bool(item.get("uncertain")) for item in received.values())},
        "ctc_margin_diagnostic": {"comparable_lines": comparable_margins,
                                  "reference_winner_or_tie": ctc_margin_predicts_reference_winner},
        "frozen_development_gate": {
            "noninferior_to_best_complete_strict": scores["luna_adjudicated"]["strict"]["cer"] <= strict_best,
            "no_exact_candidate_regression": exact_candidate_regressions == 0,
            "passed": scores["luna_adjudicated"]["strict"]["cer"] <= strict_best and exact_candidate_regressions == 0,
        },
        "line_decisions": line_decisions,
        "truth_warning": "SBB derivative is immutable but not perfect truth; A22/A23 lines are consumed.",
    }
    (base / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name in ("vlm", "ctc", "luna_adjudicated"):
        vals = scores[name]
        print(name, *(f"{profile}={100*vals[profile]['cer']:.3f}%({vals[profile]['edits']})" for profile in vals))
    print(json.dumps(report["selection"], ensure_ascii=False))
    print(json.dumps(report["frozen_development_gate"], ensure_ascii=False))


if __name__ == "__main__":
    main()
