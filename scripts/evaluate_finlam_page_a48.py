#!/usr/bin/env python3
"""A48: frozen transfer of BBVLM geometry and the published title-cut rule.

The three Finlam test rows were fixed before their content was opened.  This
evaluator uses the existing BBVLM column-order parameters unchanged.  Layout
boxes and classes are oracle inputs, so this isolates order/article reasoning;
it is not an end-to-end detector score.
"""
from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path

from bbvlm.order import infer_column_major_order


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/loop/finlam-page-a48"
CLASS_NAMES = [
    "HEADER-TITLE", "HEADER-TEXT", "SECTION-TITLE", "ILLUSTRATION",
    "ADVERTISEMENT", "ANNOUNCEMENT", "TITLE", "TEXT", "SUBTITLE",
    "INSIDEHEADING", "CAPTION", "AUTHOR", "TABLE", "ILLUSTRATEDTEXT",
    "TABLECONTENT", "ASIDE",
]
ORDER_CONFIG = {
    "gap_ratio": 0.14,
    "top_exclusion_ratio": 0.055,
    "max_anchor_width_ratio": 0.55,
}


def prf(reference: set[tuple[int, int]], predicted: set[tuple[int, int]]) -> dict:
    tp = len(reference & predicted)
    precision = tp / len(predicted) if predicted else 0.0
    recall = tp / len(reference) if reference else 0.0
    return {
        "true_positive": tp,
        "reference": len(reference),
        "predicted": len(predicted),
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
    }


def precedence(reference: list[int], predicted: list[int]) -> dict:
    pos = {value: index for index, value in enumerate(predicted)}
    pairs = [(a, b) for index, a in enumerate(reference) for b in reference[index + 1:]]
    adjacent = list(zip(reference, reference[1:]))
    correct = sum(pos.get(a, 10**9) < pos.get(b, -1) for a, b in pairs)
    edge_correct = sum(pos.get(a, 10**9) < pos.get(b, -1) for a, b in adjacent)
    return {
        "pairwise_correct": correct,
        "pairwise_denominator": len(pairs),
        "pairwise_accuracy": correct / len(pairs) if pairs else 1.0,
        "reference_adjacent_correct": edge_correct,
        "reference_adjacent_denominator": len(adjacent),
        "reference_adjacent_accuracy": edge_correct / len(adjacent) if adjacent else 1.0,
    }


def within_article_precedence(reference_order: list[int], predicted_order: list[int],
                              article_ids: list[int | None]) -> dict:
    """Micro/macro precedence restricted to blocks of the same article."""
    predicted_position = {zone: index for index, zone in enumerate(predicted_order)}
    by_article: dict[int, list[int]] = {}
    for zone in reference_order:
        article = article_ids[zone]
        if article is not None:
            by_article.setdefault(article, []).append(zone)
    rows = []
    total_correct = total_pairs = 0
    for article, zones in by_article.items():
        pairs = [(a, b) for index, a in enumerate(zones) for b in zones[index + 1:]]
        correct = sum(predicted_position[a] < predicted_position[b] for a, b in pairs)
        total_correct += correct
        total_pairs += len(pairs)
        rows.append({"article": article, "zones": len(zones), "pairs": len(pairs),
                     "correct": correct, "accuracy": correct / len(pairs) if pairs else 1.0})
    return {
        "micro_correct": total_correct,
        "micro_denominator": total_pairs,
        "micro_accuracy": total_correct / total_pairs if total_pairs else 1.0,
        "macro_accuracy": sum(row["accuracy"] for row in rows) / len(rows) if rows else 1.0,
        "articles": rows,
    }


def title_cut_groups(order: list[int], classes: list[int]) -> dict[int, int]:
    """Paper-faithful optimistic cut: a run of TITLE zones opens one article."""
    group = -1
    previous_title = False
    out = {}
    for zone in order:
        is_title = classes[zone] == 6
        if is_title and not previous_title:
            group += 1
        if group < 0:
            group = 0
        out[zone] = group
        previous_title = is_title
    return out


def article_pairs(labels: dict[int, object]) -> set[tuple[int, int]]:
    zones = sorted(labels)
    return {
        (a, b) for index, a in enumerate(zones) for b in zones[index + 1:]
        if labels[a] == labels[b]
    }


def load_row(index: int) -> dict:
    payload = json.loads((EXP / f"source/row-{index}.json").read_text())
    if payload["rows"][0]["row_idx"] != index:
        raise ValueError(f"row index mismatch for {index}")
    return payload["rows"][0]["row"]


def evaluate_page(index: int) -> dict:
    row = load_row(index)
    lengths = {key: len(row[key]) for key in (
        "zone_orders", "zone_polygons", "zone_classes", "zone_texts",
        "zone_article_ids", "zone_section_ids",
    )}
    if len(set(lengths.values())) != 1 or not next(iter(lengths.values())):
        raise ValueError(f"non-parallel or empty row arrays: {lengths}")
    count = lengths["zone_orders"]
    if len(set(row["zone_orders"])) != count:
        raise ValueError("reference zone order is not a strict permutation")

    width, height = row["page_image"]["width"], row["page_image"]["height"]
    regions = []
    for zone, polygon in enumerate(row["zone_polygons"]):
        xs = [point[0] * width for point in polygon]
        ys = [point[1] * height for point in polygon]
        regions.append({"id": zone, "bbox": [min(xs), min(ys), max(xs), max(ys)]})
    started = time.perf_counter()
    proposal = infer_column_major_order(regions, [0, 0, width, height], **ORDER_CONFIG)
    runtime = time.perf_counter() - started
    predicted_order = proposal["ordered_region_ids"]
    reference_order = sorted(range(count), key=lambda zone: row["zone_orders"][zone])

    annotated = [zone for zone in range(count) if row["zone_article_ids"][zone] is not None]
    reference_labels = {zone: row["zone_article_ids"][zone] for zone in annotated}
    oracle_cut = title_cut_groups(reference_order, row["zone_classes"])
    geometry_cut = title_cut_groups(predicted_order, row["zone_classes"])
    oracle_labels = {zone: oracle_cut[zone] for zone in annotated}
    geometry_labels = {zone: geometry_cut[zone] for zone in annotated}
    ref_pairs = article_pairs(reference_labels)

    return {
        "row_index": index,
        "page_arkindex_id": row["page_arkindex_id"],
        "page_index": row["page_index"],
        "image": {"width": width, "height": height},
        "counts": {
            "zones": count,
            "annotated_article_zones": len(annotated),
            "reference_articles": len(set(reference_labels.values())),
            "reference_sections": len({x for x in row["zone_section_ids"] if x is not None}),
            "classes": dict(sorted(Counter(CLASS_NAMES[x] for x in row["zone_classes"]).items())),
            "inferred_columns": len(proposal["column_anchors_x"]),
        },
        "reading_order": precedence(reference_order, predicted_order),
        "within_article_reading_order": within_article_precedence(
            reference_order, predicted_order, row["zone_article_ids"]),
        "reference_convention_audit": {
            "articles_without_title_zone": sum(
                not any(row["zone_classes"][zone] == 6 for zone in annotated
                        if row["zone_article_ids"][zone] == article)
                for article in set(reference_labels.values())
            ),
            "order_span": [min(row["zone_orders"]), max(row["zone_orders"])],
            "largest_forward_order_gap": max(
                (b - a for a, b in zip(
                    sorted(row["zone_orders"]), sorted(row["zone_orders"])[1:])), default=0),
            "warning": "zone_orders are issue-logical: continued articles can precede the page masthead; page-only visual order is not the whole target",
        },
        "article_same_pair": {
            "oracle_order_plus_title_cut": prf(ref_pairs, article_pairs(oracle_labels)),
            "bbvlm_order_plus_title_cut": prf(ref_pairs, article_pairs(geometry_labels)),
        },
        "cpu_runtime_seconds": runtime,
    }


def macro(pages: list[dict], path: list[str]) -> float:
    values = []
    for page in pages:
        value = page
        for key in path:
            value = value[key]
        values.append(value)
    return sum(values) / len(values)


def main() -> None:
    split = json.loads((EXP / "split.json").read_text())
    pages = [evaluate_page(index) for index in split["selection"]["row_indices"]]
    report = {
        "schema": "bbvlm.finlam-page-a48-evaluation/1",
        "status": "independent frozen transfer; pages consumed after this score",
        "source_revision": split["source"]["revision"],
        "scope": "oracle Finlam region polygons/classes; frozen BBVLM geometry order; published title-cut article rule",
        "pages": pages,
        "macro": {
            "reading_order_pairwise_accuracy": macro(pages, ["reading_order", "pairwise_accuracy"]),
            "reading_order_adjacent_accuracy": macro(pages, ["reading_order", "reference_adjacent_accuracy"]),
            "within_article_order_micro_accuracy": macro(pages, ["within_article_reading_order", "micro_accuracy"]),
            "within_article_order_macro_accuracy": macro(pages, ["within_article_reading_order", "macro_accuracy"]),
            "oracle_order_title_cut_article_pair_f1": macro(pages, ["article_same_pair", "oracle_order_plus_title_cut", "f1"]),
            "bbvlm_order_title_cut_article_pair_f1": macro(pages, ["article_same_pair", "bbvlm_order_plus_title_cut", "f1"]),
        },
        "cost": {"vlm_passes": 0, "cpu_seconds": sum(p["cpu_runtime_seconds"] for p in pages)},
        "invariants": {
            "split_frozen_before_content_open": split["selection"]["content_seen_before_freeze"] is False,
            "dataset_revision_pinned": True,
            "parameters_reused_without_a48_tuning": True,
            "reference_arrays_parallel_and_nonempty": True,
        },
        "limitations": [
            "Oracle block polygons and semantic classes: not an end-to-end detection result.",
            "Finlam zone_texts are OCR-extracted provider data, not certified transcription truth; OCR is not scored.",
            "Three frozen pages are a transfer diagnostic, not a global completion gate.",
            "Title cutting follows the paper description but does not reproduce unreleased implementation details.",
        ],
    }
    (EXP / "cpu-baseline-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
