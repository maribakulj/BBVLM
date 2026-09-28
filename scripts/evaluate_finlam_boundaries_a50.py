#!/usr/bin/env python3
"""Score blind A50 boundary decisions without replacing the immutable labels."""
from __future__ import annotations

import json
from pathlib import Path

from evaluate_finlam_page_a48 import CLASS_NAMES, article_pairs, prf, title_cut_groups


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/loop/finlam-boundaries-a50"
SOURCE = ROOT / "experiments/loop/finlam-page-a49/source/row-186.json"


def labels_from_breaks(order: list[int], classes: list[int], extra_breaks: set[tuple[int, int]]) -> dict[int, int]:
    group = 0
    out = {}
    previous_title = False
    previous = None
    for zone in order:
        is_title = classes[zone] == 6
        if out and ((is_title and not previous_title) or (previous, zone) in extra_breaks):
            group += 1
        out[zone] = group
        previous_title = is_title
        previous = zone
    return out


def main() -> None:
    private = json.loads((EXP / "private-map.json").read_text())
    response = json.loads((EXP / "output/luna-response.json").read_text())
    row = json.loads(SOURCE.read_text())["rows"][0]["row"]
    expected = {item["token"] for item in private["candidates"]}
    decisions = response.get("decisions", [])
    actual = [item.get("token") for item in decisions]
    if set(actual) != expected or len(actual) != len(expected):
        raise ValueError(f"response token mismatch: expected {len(expected)}, got {len(actual)}")
    allowed = {"same_article", "new_article", "unclear"}
    if any(item.get("label") not in allowed for item in decisions):
        raise ValueError("invalid decision label")
    decision = {item["token"]: item["label"] for item in decisions}
    mapping = {item["token"]: (item["upper_zone"], item["lower_zone"])
               for item in private["candidates"]}
    truth = {token: row["zone_article_ids"][a] != row["zone_article_ids"][b]
             for token, (a, b) in mapping.items()}
    predicted_new = {mapping[token] for token, label in decision.items() if label == "new_article"}

    annotated = [zone for zone, article in enumerate(row["zone_article_ids"]) if article is not None]
    ref_labels = {zone: row["zone_article_ids"][zone] for zone in annotated}
    order = private["ordered_region_ids"]
    baseline = title_cut_groups(order, row["zone_classes"])
    candidate = labels_from_breaks(order, row["zone_classes"], predicted_new)
    ref_pairs = article_pairs(ref_labels)
    baseline_score = prf(ref_pairs, article_pairs({z: baseline[z] for z in annotated}))
    candidate_score = prf(ref_pairs, article_pairs({z: candidate[z] for z in annotated}))

    tp = sum(decision[token] == "new_article" and is_new for token, is_new in truth.items())
    fp = sum(decision[token] == "new_article" and not is_new for token, is_new in truth.items())
    fn = sum(decision[token] != "new_article" and is_new for token, is_new in truth.items())
    tn = sum(decision[token] == "same_article" and not is_new for token, is_new in truth.items())
    unclear = sum(label == "unclear" for label in decision.values())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    report = {
        "schema": "bbvlm.finlam-boundaries-a50-evaluation/1",
        "status": "blind Luna development pass on consumed A49 stress page",
        "scope": "oracle Finlam region polygons/classes; recurrent geometry; VLM only on routed article-boundary crops",
        "page": {"row_index": 186, "zones": len(row["zone_orders"]),
                 "reference_articles": len(set(ref_labels.values())),
                 "articles_without_title": 23},
        "router": {
            **private["router"], "queried_edges": len(expected),
            "reference_new_article_edges_queried": sum(truth.values()),
        },
        "blind_boundary_classification": {
            "true_positive": tp, "false_positive": fp, "false_negative": fn,
            "true_negative": tn, "unclear": unclear, "precision": precision,
            "recall": recall,
            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        },
        "post_score_error_audit": {
            "false_positive_tokens": sorted(token for token, is_new in truth.items()
                                            if decision[token] == "new_article" and not is_new),
            "false_negative_tokens": sorted(token for token, is_new in truth.items()
                                            if decision[token] != "new_article" and is_new),
            "note": "Opaque IDs are retained for visual reinspection; no label or decision is rewritten.",
        },
        "article_same_pair": {"title_cut_baseline": baseline_score,
                              "title_cut_plus_luna": candidate_score},
        "cost": {"vlm_passes": 1, "images": len(json.loads((EXP / 'input/request.json').read_text())["sheets"]),
                 "queried_edges": len(expected), "layout_vlm_passes": 0, "ocr_vlm_passes": 0},
        "invariants": {
            "opaque_ids": True, "reference_withheld_from_reader": True,
            "geometry_order_unchanged": True, "unclear_is_conservative_continue": True,
            "original_reference_unchanged": True,
        },
        "limitations": [
            "Consumed-data development only; no completion-gate evidence.",
            "Oracle block polygons/classes isolate semantic article separation and are not end-to-end detection.",
            "The router was developed on the same six A49 pages and must be frozen before new validation.",
            "A50 preparation used reference article presence only to omit unannotated edges; A51 removes this leakage before independent scoring.",
        ],
    }
    (EXP / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
