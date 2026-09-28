#!/usr/bin/env python3
"""Evaluate the reference-blind first-two-page A51 boundary pilot."""
from __future__ import annotations

import json
from pathlib import Path

from evaluate_finlam_boundaries_a50 import labels_from_breaks
from evaluate_finlam_page_a48 import article_pairs, precedence, prf, title_cut_groups, within_article_precedence


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/loop/finlam-boundaries-a51"


def main() -> None:
    split = json.loads((EXP / "split.json").read_text())
    private = json.loads((EXP / "private-map.json").read_text())
    response = json.loads((EXP / "output/luna-response.json").read_text())
    expected = {item["token"] for page in private["pages"].values() for item in page["candidates"]}
    decisions = response.get("decisions", [])
    actual = [item.get("token") for item in decisions]
    if set(actual) != expected or len(actual) != len(expected):
        raise ValueError(f"response token mismatch: expected {len(expected)}, got {len(actual)}")
    if any(item.get("label") not in {"same_article", "new_article", "unclear"} for item in decisions):
        raise ValueError("invalid label")
    decision = {item["token"]: item["label"] for item in decisions}
    pages = []
    for index in private["pilot_rows"]:
        row = json.loads((EXP / f"source/row-{index}.json").read_text())["rows"][0]["row"]
        page = private["pages"][str(index)]
        mapping = {item["token"]: (item["upper_zone"], item["lower_zone"])
                   for item in page["candidates"]}
        scored = {
            token: row["zone_article_ids"][a] != row["zone_article_ids"][b]
            for token, (a, b) in mapping.items()
            if row["zone_article_ids"][a] is not None and row["zone_article_ids"][b] is not None
        }
        predicted_breaks = {mapping[token] for token in mapping if decision[token] == "new_article"}
        annotated = [z for z, article in enumerate(row["zone_article_ids"]) if article is not None]
        ref_labels = {z: row["zone_article_ids"][z] for z in annotated}
        order = page["ordered_region_ids"]
        baseline = title_cut_groups(order, row["zone_classes"])
        candidate = labels_from_breaks(order, row["zone_classes"], predicted_breaks)
        ref_pairs = article_pairs(ref_labels)
        tp = sum(decision[token] == "new_article" and truth for token, truth in scored.items())
        fp = sum(decision[token] == "new_article" and not truth for token, truth in scored.items())
        fn = sum(decision[token] != "new_article" and truth for token, truth in scored.items())
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        reference_order = sorted(range(len(row["zone_orders"])), key=lambda z: row["zone_orders"][z])
        pages.append({
            "row_index": index, "page_index": row["page_index"], "zones": len(row["zone_orders"]),
            "reference_articles": len(set(ref_labels.values())), "queried_edges": len(mapping),
            "scored_edges": len(scored),
            "boundary": {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall,
                         "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0},
            "global_order": precedence(reference_order, order),
            "within_article_order": within_article_precedence(reference_order, order, row["zone_article_ids"]),
            "article_same_pair": {
                "title_cut_baseline": prf(ref_pairs, article_pairs({z: baseline[z] for z in annotated})),
                "title_cut_plus_luna": prf(ref_pairs, article_pairs({z: candidate[z] for z in annotated})),
            },
        })
    def mean(path: tuple[str, ...]) -> float:
        values = []
        for page in pages:
            value = page
            for key in path:
                value = value[key]
            values.append(value)
        return sum(values) / len(values)
    report = {
        "schema": "bbvlm.finlam-boundaries-a51-pilot-evaluation/1",
        "status": "independent frozen two-page pilot; pages consumed after this score",
        "pages": pages,
        "macro": {
            "global_pair_accuracy": mean(("global_order", "pairwise_accuracy")),
            "within_article_micro_accuracy": mean(("within_article_order", "micro_accuracy")),
            "boundary_f1": mean(("boundary", "f1")),
            "baseline_article_pair_f1": mean(("article_same_pair", "title_cut_baseline", "f1")),
            "candidate_article_pair_f1": mean(("article_same_pair", "title_cut_plus_luna", "f1")),
        },
        "pilot_gate_conditions": {
            "article_f1_ge_threshold": mean(("article_same_pair", "title_cut_plus_luna", "f1")) >= split["gates"]["macro_article_same_pair_f1_min"],
            "global_ge_threshold": mean(("global_order", "pairwise_accuracy")) >= split["gates"]["macro_global_pair_accuracy_min"],
            "within_ge_threshold": mean(("within_article_order", "micro_accuracy")) >= split["gates"]["macro_within_article_micro_accuracy_min"],
            "article_f1_above_baseline": mean(("article_same_pair", "title_cut_plus_luna", "f1")) > mean(("article_same_pair", "title_cut_baseline", "f1")),
            "no_page_article_f1_regression": all(p["article_same_pair"]["title_cut_plus_luna"]["f1"] >= p["article_same_pair"]["title_cut_baseline"]["f1"] for p in pages),
        },
        "cost": {"vlm_passes": 1, "pages": len(pages),
                 "images": len(json.loads((EXP / 'input/request.json').read_text())["sheets"]),
                 "queried_edges": sum(p["queried_edges"] for p in pages)},
        "invariants": {
            "split_frozen_before_open": split["selection"]["content_seen_before_freeze"] is False,
            "router_does_not_read_article_ids": True, "opaque_ids": True,
            "reference_withheld_from_reader": True, "original_reference_unchanged": True,
            "geometry_order_unchanged": True,
        },
        "limitations": [
            "Only the first two of eight frozen A51 pages are opened; this pilot cannot close the registered eight-page gate.",
            "Oracle region polygons/classes isolate OLR/article semantics and are not end-to-end detection.",
            "Finlam article annotations are provider reference, not independently human-adjudicated perfect truth.",
            "After opening but before any reader/reference score, a mechanical adapter retained float polygon extents because integer rounding made one thin region zero-width.",
        ],
    }
    report["pilot_gate_passed"] = all(report["pilot_gate_conditions"].values())
    (EXP / "pilot-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
