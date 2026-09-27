"""Evaluate a frozen one-pass semantic proposal plus frozen CPU order."""
from collections import Counter
from pathlib import Path
import json
import time

from bbvlm.binding import bind_semantic_page
from bbvlm.order import infer_column_major_order

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop/spiritualist-v1/semantic-v1-validation"


def pair_set(groups):
    pairs = set()
    for members in groups:
        members = sorted(members)
        pairs.update((a, b) for i, a in enumerate(members) for b in members[i + 1:])
    return pairs


def bcubed(reference_groups, predicted_groups, items):
    ref_by, pred_by = {}, {}
    for members in reference_groups:
        for rid in members: ref_by[rid] = set(members)
    for members in predicted_groups:
        for rid in members: pred_by[rid] = set(members)
    precision = sum(len(ref_by[r] & pred_by[r]) / len(pred_by[r]) for r in items) / len(items)
    recall = sum(len(ref_by[r] & pred_by[r]) / len(ref_by[r]) for r in items) / len(items)
    return precision, recall, 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def main():
    request = json.loads((BASE / "input/request.json").read_text())
    reference = json.loads((BASE / "evaluation/reference.json").read_text())
    binding = json.loads((BASE / "evaluation/token-binding.json").read_text())["token_to_id"]
    response = json.loads((BASE / "luna.response.json").read_text())
    errors, bound = [], None
    if response.get("schema") != "bbvlm.blind-semantic-response/1" or response.get("page") != request["page"]:
        errors.append("unexpected schema or page")
    else:
        try: bound = bind_semantic_page(response, binding)
        except (KeyError, TypeError, ValueError) as exc: errors.append(str(exc))
    raw_valid = not errors
    metrics = None
    if raw_valid:
        rows = reference["regions"]; ids = {r["id"] for r in rows}; by_id = {r["id"]: r for r in rows}
        ref_eligible = {r["id"] for r in rows if r["reading_order"] >= 0}
        pred_eligible = set(bound["eligible_region_ids"])
        tp = len(ref_eligible & pred_eligible)
        ep = tp / len(pred_eligible) if pred_eligible else 0.0
        er = tp / len(ref_eligible) if ref_eligible else 1.0
        ef = 2 * ep * er / (ep + er) if ep + er else 0.0
        reference_groups = {}
        for row in rows: reference_groups.setdefault(row["semantic_unit"], []).append(row["id"])
        predicted_groups = [g["region_ids"] for g in bound["groups"]]
        ref_pairs, pred_pairs = pair_set(reference_groups.values()), pair_set(predicted_groups)
        gtp = len(ref_pairs & pred_pairs)
        gp = gtp / len(pred_pairs) if pred_pairs else (1.0 if not ref_pairs else 0.0)
        gr = gtp / len(ref_pairs) if ref_pairs else 1.0
        gf = 2 * gp * gr / (gp + gr) if gp + gr else 0.0
        bp, br, bf = bcubed(list(reference_groups.values()), predicted_groups, ids)
        role_correct = sum(bound["roles"][rid] == by_id[rid]["role"] for rid in ids)
        confusion = Counter((by_id[rid]["role"], bound["roles"][rid]) for rid in ids)
        config = json.loads((ROOT / "experiments/loop/spiritualist-v1/olr-v3-column/config.json").read_text())
        regions = [{"id": r["id"], "bbox": r["bbox"]} for r in rows]
        start = time.perf_counter()
        order = infer_column_major_order(regions, reference["page_bbox"], gap_ratio=config["gap_ratio"],
                                         top_exclusion_ratio=config["top_exclusion_ratio"],
                                         max_anchor_width_ratio=config["max_anchor_width_ratio"])
        elapsed = time.perf_counter() - start
        predicted_order = [rid for rid in order["ordered_region_ids"] if rid in pred_eligible]
        pos = {rid: i for i, rid in enumerate(predicted_order)}
        known = [r["id"] for r in sorted(rows, key=lambda r: r["reading_order"]) if r["reading_order"] >= 0]
        order_pairs = [(a, b) for i, a in enumerate(known) for b in known[i + 1:]]
        correct = sum(a in pos and b in pos and pos[a] < pos[b] for a, b in order_pairs)
        order_recall = correct / len(order_pairs) if order_pairs else 1.0
        metrics = {
            "regions": len(rows), "reference_eligible": len(ref_eligible), "predicted_eligible": len(pred_eligible),
            "eligibility_true_positive": tp, "eligibility_precision": ep, "eligibility_recall": er, "eligibility_f1": ef,
            "contamination_region_ids": sorted(pred_eligible - ref_eligible),
            "missing_eligible_region_ids": sorted(ref_eligible - pred_eligible),
            "role_correct": role_correct, "role_accuracy": role_correct / len(ids),
            "role_confusion": [{"reference": a, "predicted": b, "count": n} for (a, b), n in sorted(confusion.items())],
            "semantic_group_true_positive_pairs": gtp, "semantic_group_predicted_pairs": len(pred_pairs),
            "semantic_group_reference_pairs": len(ref_pairs), "semantic_group_pair_precision": gp,
            "semantic_group_pair_recall": gr, "semantic_group_pair_f1": gf,
            "semantic_group_false_positive_pairs": len(pred_pairs - ref_pairs),
            "semantic_group_false_negative_pairs": len(ref_pairs - pred_pairs),
            "semantic_group_bcubed_precision": bp, "semantic_group_bcubed_recall": br, "semantic_group_bcubed_f1": bf,
            "reference_semantic_units": len(reference_groups), "predicted_semantic_units": len(predicted_groups),
            "combined_order_correct_reference_pairs": correct, "combined_order_reference_pairs": len(order_pairs),
            "combined_order_pair_recall": order_recall, "cpu_order_runtime_seconds": elapsed,
            "cpu_inferred_columns": len(order["column_anchors_x"]), "uncertain_region_ids": bound["uncertain_region_ids"],
        }
    gates = request["frozen_gates"]
    content_pass = bool(raw_valid and metrics
        and metrics["eligibility_precision"] >= gates["eligibility_precision_min"]
        and metrics["eligibility_recall"] >= gates["eligibility_recall_min"]
        and metrics["role_accuracy"] >= gates["role_accuracy_min"]
        and metrics["semantic_group_pair_f1"] >= gates["semantic_group_pair_f1_min"]
        and metrics["combined_order_pair_recall"] >= gates["combined_order_pair_recall_min"])
    result = {
        "schema": "bbvlm.semantic-plus-cpu-order-evaluation/1", "page": request["page"],
        "split_role": "frozen_validation_consumed_after_this_evaluation", "reader": "gpt-6-luna",
        "passes": {"vlm_semantic": 1, "cpu_geometry_order": 1}, "raw_structural_valid": raw_valid,
        "cost_note": "One authorized Luna pass; model latency and token billing are not exposed to this evaluator. CPU order time is measured below.",
        "raw_structural_errors": errors, "repair_attempted": False, "metrics": metrics,
        "frozen_gates": gates, "content_gate_passed": content_pass,
        "accepted_for_project_completion_gate": False,
        "reference_warning": request["reference_warning"], "leakage_control": request["leakage_control"],
        "interpretation": "Role/SSU agreement is measured against provisional corpus labels. Passing would validate this frozen transport/policy on one page, not establish article truth.",
    }
    (BASE / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
