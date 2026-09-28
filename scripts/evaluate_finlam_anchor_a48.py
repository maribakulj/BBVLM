#!/usr/bin/env python3
"""Score the single blind A48 Luna anchor/metadata pass."""
from __future__ import annotations

import json
from pathlib import Path

from bbvlm.metrics import edit_distance
from bbvlm.order import infer_recurrent_column_order
from bbvlm.text_views import diplomatic_nfc, lexical_alnum, retrieval_fold_v1, search_v1
from evaluate_finlam_page_a48 import CLASS_NAMES, precedence


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/loop/finlam-page-a48"
EXPECTED_ROLE = {
    0: "masthead", 1: "masthead", 2: "article_title", 6: "article_title",
    8: "subheading", 9: "subheading",
}


def score_text(pairs: list[tuple[str, str]], normalizer) -> dict:
    rows = []
    for reference, hypothesis in pairs:
        a, b = normalizer(reference), normalizer(hypothesis)
        rows.append((len(a), edit_distance(a, b), a == b))
    chars = sum(x[0] for x in rows)
    edits = sum(x[1] for x in rows)
    return {"characters": chars, "edits": edits, "cer": edits / chars if chars else None,
            "exact": sum(x[2] for x in rows), "items": len(rows)}


def main() -> None:
    row = json.loads((EXP / "source/row-365.json").read_text())["rows"][0]["row"]
    mapping = json.loads((EXP / "anchor-vlm/sealed-map.json").read_text())["token_to_zone"]
    candidate = json.loads((EXP / "anchor-vlm/reader/candidate-luna.json").read_text())
    expected_tokens = set(mapping)
    if set(candidate.get("roles", {})) != expected_tokens:
        raise ValueError("roles must cover exactly the sealed token set")
    if set(candidate["roles"].values()) - {"masthead", "article_title", "subheading", "other"}:
        raise ValueError("unknown role")
    flattened = [token for group in candidate.get("ordered_article_groups", []) for token in group.get("tokens", [])]
    if len(flattened) != len(set(flattened)) or set(flattened) - expected_tokens:
        raise ValueError("article group tokens must be unique known tokens")
    if any(candidate["roles"][token] not in {"article_title", "subheading"} for token in flattened):
        raise ValueError("group token has ineligible predicted role")
    metadata_evidence = [token for item in candidate["metadata"].values() for token in item["evidence_tokens"]]
    if set(metadata_evidence) - expected_tokens:
        raise ValueError("metadata cites an unknown token")

    role_correct = sum(candidate["roles"][token] == EXPECTED_ROLE[row["zone_classes"][zone]]
                       for token, zone in mapping.items())
    confusion = {}
    for token, zone in mapping.items():
        key = f"{CLASS_NAMES[row['zone_classes'][zone]]}->{candidate['roles'][token]}"
        confusion[key] = confusion.get(key, 0) + 1

    all_articles = {article for article in row["zone_article_ids"] if article is not None}
    anchor_articles = {row["zone_article_ids"][zone] for zone in mapping.values()
                       if row["zone_article_ids"][zone] is not None}
    predicted_article_sequence = []
    impure_groups = []
    text_pairs = []
    for group_index, group in enumerate(candidate["ordered_article_groups"]):
        zones = [mapping[token] for token in group["tokens"]]
        articles = {row["zone_article_ids"][zone] for zone in zones
                    if row["zone_article_ids"][zone] is not None}
        if len(articles) == 1:
            article = next(iter(articles))
            if article not in predicted_article_sequence:
                predicted_article_sequence.append(article)
        else:
            impure_groups.append({"group": group_index, "reference_articles": sorted(articles)})
        reference = " ".join(row["zone_texts"][zone] for zone in sorted(zones, key=lambda z: row["zone_orders"][z]))
        text_pairs.append((reference, group["headline"]))
    reference_sequence = sorted(anchor_articles, key=lambda article: min(
        order for order, value in zip(row["zone_orders"], row["zone_article_ids"]) if value == article))
    covered_reference = [article for article in reference_sequence if article in predicted_article_sequence]
    article_order = precedence(covered_reference, predicted_article_sequence)

    width, height = row["page_image"]["width"], row["page_image"]["height"]
    regions = []
    for zone, (polygon, class_id) in enumerate(zip(row["zone_polygons"], row["zone_classes"])):
        xs, ys = [p[0] * width for p in polygon], [p[1] * height for p in polygon]
        regions.append({"id": zone, "bbox": [min(xs), min(ys), max(xs), max(ys)],
                        "role": CLASS_NAMES[class_id]})
    column_proposal = infer_recurrent_column_order(regions, [0, 0, width, height])

    report = {
        "schema": "bbvlm.finlam-anchor-a48-evaluation/1",
        "status": "post-score exploratory VLM pass on consumed A48 page",
        "reader": candidate.get("reader"),
        "scope": "one full-page original plus one opaque 33-anchor overlay; oracle candidate anchors; no body transcription",
        "integrity": {
            "exact_role_token_coverage": True,
            "unknown_or_duplicate_group_tokens": False,
            "impure_reference_article_groups": impure_groups,
            "uncertain_tokens": candidate.get("uncertain_tokens", []),
        },
        "dataset_label_projection": {
            "correct": role_correct, "denominator": len(mapping),
            "accuracy": role_correct / len(mapping), "confusion": dict(sorted(confusion.items())),
            "warning": "Finlam TITLE/SUBTITLE encode typographic hierarchy, while Luna used editorial main-title/subheading semantics; disagreement is not automatically visual error.",
        },
        "article_anchors": {
            "reference_page_articles": len(all_articles),
            "reference_articles_with_candidate_anchor": len(anchor_articles),
            "predicted_groups": len(candidate["ordered_article_groups"]),
            "covered_reference_anchor_articles": len(set(predicted_article_sequence) & anchor_articles),
            "coverage_of_anchor_articles": len(set(predicted_article_sequence) & anchor_articles) / len(anchor_articles),
            "coverage_of_all_page_articles": len(set(predicted_article_sequence) & all_articles) / len(all_articles),
            "reference_articles_split_across_groups": len(predicted_article_sequence) < len(candidate["ordered_article_groups"]),
            "order_on_covered_articles": article_order,
        },
        "headline_provider_agreement": {
            "strict_diplomatic_nfc": score_text(text_pairs, diplomatic_nfc),
            "search_v1": score_text(text_pairs, search_v1),
            "lexical_alnum": score_text(text_pairs, lexical_alnum),
            "retrieval_fold_v1": score_text(text_pairs, retrieval_fold_v1),
            "warning": "Finlam zone_texts are OCR-extracted provider text, not independently adjudicated ground truth.",
        },
        "columns": {
            "luna_count": candidate["columns"]["count"],
            "luna_bands": candidate["columns"]["x_bands_normalized"],
            "recurrent_geometry_count": len(column_proposal["column_anchors_x"]),
            "recurrent_geometry_anchors_normalized": [x / width for x in column_proposal["column_anchors_x"]],
            "count_agreement": candidate["columns"]["count"] == len(column_proposal["column_anchors_x"]),
        },
        "metadata": candidate["metadata"],
        "continued_or_anchorless_articles": candidate.get("continued_or_anchorless_articles", []),
        "cost": {"vlm_passes": 1, "images": 2, "anchor_tokens": len(mapping), "reader_escalations": 0},
        "decision": (
            "Keep recurrent geometry for physical column/order recovery; use one compact VLM anchor pass for headline transcription, "
            "editorial semantics and issue metadata. Do not ask the VLM to replace cheap order or word localization."
        ),
        "limitations": [
            "Consumed exploratory page; not independent validation.",
            "Oracle semantic classes selected the 33 candidate anchor boxes.",
            "No body OCR, word boxes, predicted detector boxes, neighboring-page continuation context, or human-adjudicated metadata truth.",
        ],
    }
    (EXP / "anchor-vlm/report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
