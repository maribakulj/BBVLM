#!/usr/bin/env python3
"""Develop recurrent-column order on consumed A48; never call validation."""
from __future__ import annotations

import json
from pathlib import Path

from bbvlm.order import infer_column_major_order, infer_recurrent_column_order
from evaluate_finlam_page_a48 import (CLASS_NAMES, article_pairs, precedence, prf,
                                      title_cut_groups, within_article_precedence)


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/loop/finlam-page-a48"


def proposal(row: dict, method) -> dict:
    width, height = row["page_image"]["width"], row["page_image"]["height"]
    regions = []
    for zone, (polygon, class_id) in enumerate(zip(row["zone_polygons"], row["zone_classes"])):
        xs, ys = [p[0] * width for p in polygon], [p[1] * height for p in polygon]
        regions.append({"id": zone, "bbox": [min(xs), min(ys), max(xs), max(ys)],
                        "role": CLASS_NAMES[class_id]})
    return method(regions, [0, 0, width, height])


def score(row: dict, predicted: list[int]) -> dict:
    reference = sorted(range(len(row["zone_orders"])), key=lambda zone: row["zone_orders"][zone])
    annotated = [zone for zone, article in enumerate(row["zone_article_ids"]) if article is not None]
    reference_labels = {zone: row["zone_article_ids"][zone] for zone in annotated}
    predicted_groups = title_cut_groups(predicted, row["zone_classes"])
    return {
        "global": precedence(reference, predicted),
        "within_article": within_article_precedence(reference, predicted, row["zone_article_ids"]),
        "article_same_pair": prf(article_pairs(reference_labels), article_pairs(
            {zone: predicted_groups[zone] for zone in annotated})),
    }


def main() -> None:
    pages = []
    for index in (242, 73, 365):
        row = json.loads((EXP / f"source/row-{index}.json").read_text())["rows"][0]["row"]
        old = proposal(row, infer_column_major_order)
        new = proposal(row, infer_recurrent_column_order)
        pages.append({
            "row_index": index,
            "legacy": {"columns": len(old["column_anchors_x"]), **score(row, old["ordered_region_ids"])},
            "recurrent": {"columns": len(new["column_anchors_x"]), **score(row, new["ordered_region_ids"])},
        })
    def mean(path):
        values = []
        for page in pages:
            value = page
            for key in path:
                value = value[key]
            values.append(value)
        return sum(values) / len(values)
    report = {
        "schema": "bbvlm.finlam-recurrent-columns-a48-development/1",
        "status": "development on consumed A48; parameters frozen for unopened A49",
        "pages": pages,
        "macro": {
            "legacy_global_pair_accuracy": mean(["legacy", "global", "pairwise_accuracy"]),
            "recurrent_global_pair_accuracy": mean(["recurrent", "global", "pairwise_accuracy"]),
            "legacy_within_article_micro_accuracy": mean(["legacy", "within_article", "micro_accuracy"]),
            "recurrent_within_article_micro_accuracy": mean(["recurrent", "within_article", "micro_accuracy"]),
            "legacy_article_pair_f1": mean(["legacy", "article_same_pair", "f1"]),
            "recurrent_article_pair_f1": mean(["recurrent", "article_same_pair", "f1"]),
        },
        "frozen_parameters": {
            "body_roles": ["TEXT", "ILLUSTRATEDTEXT"], "narrow_width_ratio": 0.22,
            "fine_cluster_width_fraction": 0.25, "merge_anchor_width_fraction": 0.50,
            "min_support": 3,
        },
        "interpretation": "Recurring left edges fix the legacy single-column collapse. Remaining global error includes issue-logical continuation order unavailable from one page.",
        "accepted_as_validation": False,
    }
    (EXP / "recurrent-columns-development.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
