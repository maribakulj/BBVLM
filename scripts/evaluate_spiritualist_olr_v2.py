"""Strict evaluation of the frozen two-page visual-token OLR experiment."""
from pathlib import Path
from collections import Counter
import json

from bbvlm.binding import bind_olr_page

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop/spiritualist-v1/olr-v2-validation"


def pair_set(groups):
    pairs = set()
    for members in groups:
        members = sorted(members)
        pairs.update((a, b) for i, a in enumerate(members) for b in members[i + 1:])
    return pairs


def score_page(page, bound, rows, gates):
    expected = {row["id"] for row in rows}
    by_id = {row["id"]: row for row in rows}
    known = sorted((r for r in rows if r["reading_order"] >= 0), key=lambda r: r["reading_order"])
    known_ids = [r["id"] for r in known]
    positions = {rid: i for i, rid in enumerate(bound["ordered_region_ids"]) if rid in set(known_ids)}
    order_pairs = [(a, b) for i, a in enumerate(known_ids) for b in known_ids[i + 1:]]
    correct_pairs = sum(positions[a] < positions[b] for a, b in order_pairs)
    reference_groups = {}
    for row in rows:
        reference_groups.setdefault(row["semantic_unit"], []).append(row["id"])
    ref_pairs = pair_set(reference_groups.values())
    pred_pairs = pair_set(group["region_ids"] for group in bound["groups"])
    tp = len(ref_pairs & pred_pairs)
    precision = tp / len(pred_pairs) if pred_pairs else (1.0 if not ref_pairs else 0.0)
    recall = tp / len(ref_pairs) if ref_pairs else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    role_correct = sum(bound["roles"][rid] == by_id[rid]["role"] for rid in expected)
    order_accuracy = correct_pairs / len(order_pairs) if order_pairs else None
    role_accuracy = role_correct / len(expected)
    confusion = Counter((by_id[rid]["role"], bound["roles"][rid]) for rid in expected)
    return {
        "page": page,
        "regions": len(rows),
        "known_order_regions": len(known_ids),
        "unknown_or_unordered_regions": len(rows) - len(known_ids),
        "reading_order_correct_pairs": correct_pairs,
        "reading_order_pairs": len(order_pairs),
        "reading_order_pair_accuracy_known_subset": order_accuracy,
        "semantic_group_true_positive_pairs": tp,
        "semantic_group_predicted_pairs": len(pred_pairs),
        "semantic_group_reference_pairs": len(ref_pairs),
        "semantic_group_pair_precision": precision,
        "semantic_group_pair_recall": recall,
        "semantic_group_pair_f1": f1,
        "reference_semantic_units": len(reference_groups),
        "predicted_semantic_units": len(bound["groups"]),
        "role_correct": role_correct,
        "roles": len(expected),
        "role_accuracy": role_accuracy,
        "role_confusion": [{"reference": a, "predicted": b, "count": n} for (a, b), n in sorted(confusion.items())],
        "uncertain_region_ids": bound["uncertain_region_ids"],
        "page_gate_passed": bool(
            order_accuracy is not None
            and order_accuracy >= gates["reading_order_pair_accuracy_each_page_min"]
            and f1 >= gates["semantic_group_pair_f1_each_page_min"]
            and role_accuracy >= gates["role_accuracy_each_page_min"]
        ),
    }


def main():
    request = json.loads((BASE / "input/request.json").read_text())
    reference = json.loads((BASE / "evaluation/reference.json").read_text())
    bindings = json.loads((BASE / "evaluation/token-binding.json").read_text())["pages"]
    response = json.loads((BASE / "luna.response.json").read_text())
    expected_pages = [p["page"] for p in request["pages"]]
    response_pages = response.get("pages")
    structural_errors = []
    bound = {}
    if response.get("schema") != "bbvlm.blind-olr-response/2":
        structural_errors.append("unexpected response schema")
    if not isinstance(response_pages, list) or [p.get("page") for p in response_pages] != expected_pages:
        structural_errors.append("pages must occur exactly once in requested order")
    else:
        for item in response_pages:
            try:
                bound[item["page"]] = bind_olr_page(item, bindings[item["page"]])
            except (KeyError, TypeError, ValueError) as exc:
                structural_errors.append(f"{item.get('page')}: {exc}")
    raw_valid = not structural_errors
    pages = []
    if raw_valid:
        pages = [score_page(p, bound[p], reference["pages"][p], request["frozen_gates"]) for p in expected_pages]
    aggregate = None
    if pages:
        correct = sum(p["reading_order_correct_pairs"] for p in pages)
        order_n = sum(p["reading_order_pairs"] for p in pages)
        tp = sum(p["semantic_group_true_positive_pairs"] for p in pages)
        pred_n = sum(p["semantic_group_predicted_pairs"] for p in pages)
        ref_n = sum(p["semantic_group_reference_pairs"] for p in pages)
        gp = tp / pred_n if pred_n else (1.0 if not ref_n else 0.0)
        gr = tp / ref_n if ref_n else 1.0
        aggregate = {
            "reading_order_pair_accuracy_micro": correct / order_n if order_n else None,
            "semantic_group_pair_precision_micro": gp,
            "semantic_group_pair_recall_micro": gr,
            "semantic_group_pair_f1_micro": 2 * gp * gr / (gp + gr) if gp + gr else 0.0,
            "role_accuracy_micro": sum(p["role_correct"] for p in pages) / sum(p["roles"] for p in pages),
        }
    result = {
        "schema": "bbvlm.blind-olr-evaluation/2",
        "split_role": "frozen_validation_consumed_after_this_evaluation",
        "reader": "gpt-6-luna",
        "passes": 1,
        "transport": "short_random_visual_tokens_strictly_bound_to_stable_ids_after_response",
        "raw_structural_valid": raw_valid,
        "raw_structural_errors": structural_errors,
        "repair_attempted": False,
        "pages": pages,
        "aggregate": aggregate,
        "frozen_gates": request["frozen_gates"],
        "content_gate_passed": raw_valid and all(p["page_gate_passed"] for p in pages),
        "accepted_for_project_completion_gate": False,
        "reference_warning": request["reference_warning"],
        "leakage_control": request["leakage_control"],
        "binding_control": request["binding_control"],
    }
    (BASE / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
