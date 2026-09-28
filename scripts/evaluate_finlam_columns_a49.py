#!/usr/bin/env python3
"""Independent A49 validation of the frozen recurrent-column candidate."""
from __future__ import annotations

import json
import time
from pathlib import Path

from bbvlm.order import infer_column_major_order, infer_recurrent_column_order
from evaluate_finlam_page_a48 import (CLASS_NAMES, article_pairs, precedence, prf,
                                      title_cut_groups, within_article_precedence)


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/loop/finlam-page-a49"


def make_regions(row: dict) -> list[dict]:
    width, height = row["page_image"]["width"], row["page_image"]["height"]
    regions = []
    for zone, (polygon, class_id) in enumerate(zip(row["zone_polygons"], row["zone_classes"])):
        xs, ys = [p[0] * width for p in polygon], [p[1] * height for p in polygon]
        regions.append({"id": zone, "bbox": [min(xs), min(ys), max(xs), max(ys)],
                        "role": CLASS_NAMES[class_id]})
    return regions


def score(row: dict, predicted: list[int]) -> dict:
    reference = sorted(range(len(row["zone_orders"])), key=lambda zone: row["zone_orders"][zone])
    annotated = [zone for zone, article in enumerate(row["zone_article_ids"]) if article is not None]
    ref_labels = {zone: row["zone_article_ids"][zone] for zone in annotated}
    cut = title_cut_groups(predicted, row["zone_classes"])
    return {
        "global_order": precedence(reference, predicted),
        "within_article_order": within_article_precedence(reference, predicted, row["zone_article_ids"]),
        "article_same_pair": prf(article_pairs(ref_labels), article_pairs({zone: cut[zone] for zone in annotated})),
    }


def main() -> None:
    split = json.loads((EXP / "split.json").read_text())
    pages = []
    started = time.perf_counter()
    for index in split["selection"]["row_indices"]:
        payload = json.loads((EXP / f"source/row-{index}.json").read_text())
        if payload["rows"][0]["row_idx"] != index:
            raise ValueError("row index mismatch")
        row = payload["rows"][0]["row"]
        if split["source"]["revision"] not in row["page_image"]["src"]:
            raise ValueError("dataset revision mismatch")
        lengths = [len(row[key]) for key in ("zone_orders", "zone_polygons", "zone_classes",
                                               "zone_article_ids", "zone_section_ids")]
        if len(set(lengths)) != 1 or not lengths[0]:
            raise ValueError("empty or nonparallel annotation arrays")
        regions = make_regions(row)
        page_bbox = [0, 0, row["page_image"]["width"], row["page_image"]["height"]]
        legacy = infer_column_major_order(regions, page_bbox)
        candidate = infer_recurrent_column_order(regions, page_bbox)
        pages.append({
            "row_index": index, "page_index": row["page_index"], "zones": lengths[0],
            "reference_articles": len({a for a in row["zone_article_ids"] if a is not None}),
            "articles_without_title": sum(
                not any(row["zone_classes"][z] == 6 for z, value in enumerate(row["zone_article_ids"]) if value == article)
                for article in {a for a in row["zone_article_ids"] if a is not None}),
            "largest_reference_order_gap": max((b - a for a, b in zip(
                sorted(row["zone_orders"]), sorted(row["zone_orders"])[1:])), default=0),
            "legacy": {"columns": len(legacy["column_anchors_x"]), **score(row, legacy["ordered_region_ids"])},
            "candidate": {"columns": len(candidate["column_anchors_x"]), **score(row, candidate["ordered_region_ids"])},
        })

    def mean(method: str, key: str, metric: str) -> float:
        return sum(p[method][key][metric] for p in pages) / len(pages)
    macro = {
        method: {
            "global_pair_accuracy": mean(method, "global_order", "pairwise_accuracy"),
            "within_article_micro_accuracy": mean(method, "within_article_order", "micro_accuracy"),
            "article_same_pair_f1": mean(method, "article_same_pair", "f1"),
        } for method in ("legacy", "candidate")
    }
    gates = split["gates"]
    conditions = {
        "within_article_ge_threshold": macro["candidate"]["within_article_micro_accuracy"] >= gates["macro_within_article_order_micro_accuracy_min"],
        "global_ge_threshold": macro["candidate"]["global_pair_accuracy"] >= gates["macro_global_pair_accuracy_min"],
        "article_f1_ge_threshold": macro["candidate"]["article_same_pair_f1"] >= gates["macro_article_same_pair_f1_min"],
        "strictly_better_all_three": all(macro["candidate"][key] > macro["legacy"][key] for key in macro["candidate"]),
    }
    report = {
        "schema": "bbvlm.finlam-recurrent-columns-a49-validation/1",
        "status": "independent frozen validation; six pages consumed after this score",
        "scope": "oracle Finlam boxes/classes; frozen geometry/order/article logic; no VLM and no OCR",
        "pages": pages,
        "macro": macro,
        "gate_conditions": conditions,
        "conditional_gate_passed": all(conditions.values()),
        "cost": {"vlm_passes": 0, "cpu_seconds": time.perf_counter() - started},
        "invariants": {"unopened_hash_split": True, "pinned_revision_verified": True,
                       "frozen_parameters": split["frozen_candidate"]["parameters"], "no_retuning": True},
        "limitations": [
            "Oracle region boxes and classes; does not measure YOLO/PERO detection.",
            "Issue-logical continuation order can require adjacent-page context unavailable to geometry.",
            "Six pages are enough to reject this gate but not certify perfect OLR.",
        ],
    }
    (EXP / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
