"""Evaluate the blind one-pass OLR/SSU development pilot."""
from pathlib import Path
from collections import Counter
import json

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop/spiritualist-v1/olr-0009"
VALID_ROLES = {"MASTHEAD", "HEADER", "TEXT", "ADVERT", "OTHER", "UNKNOWN"}


def edit_distance(a, b):
    row = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        nxt = [i]
        for j, cb in enumerate(b, 1):
            nxt.append(min(nxt[-1] + 1, row[j] + 1, row[j-1] + (ca != cb)))
        row = nxt
    return row[-1]


def pair_set(groups):
    pairs = set()
    for members in groups:
        members = sorted(members)
        pairs.update((a, b) for i, a in enumerate(members) for b in members[i+1:])
    return pairs


def main():
    request = json.loads((BASE / "input/request.json").read_text())
    reference = json.loads((BASE / "evaluation/reference.json").read_text())
    response = json.loads((BASE / "luna.response.json").read_text())
    expected = set(request["region_ids"])
    ordered = response.get("ordered_region_ids", [])
    roles = response.get("roles", {})
    predicted_groups = response.get("groups", [])
    grouped = [rid for group in predicted_groups for rid in group.get("region_ids", [])]
    errors = []
    if len(ordered) != len(set(ordered)) or set(ordered) != expected:
        errors.append("ordered_region_ids must cover every opaque ID exactly once")
    if len(grouped) != len(set(grouped)) or set(grouped) != expected:
        errors.append("groups must cover every opaque ID exactly once")
    if set(roles) != expected or any(role not in VALID_ROLES for role in roles.values()):
        errors.append("roles must cover every opaque ID with a controlled value")
    structural_valid = not errors
    diagnostic_repair = None
    if errors:
        seen = set(ordered) | set(grouped) | set(roles)
        unknown = seen - expected
        missing = expected - seen
        if len(unknown) == len(missing) == 1:
            wrong, right = next(iter(unknown)), next(iter(missing))
            if edit_distance(wrong, right) == 1:
                diagnostic_repair = {wrong: right}
                ordered = [right if rid == wrong else rid for rid in ordered]
                grouped = [right if rid == wrong else rid for rid in grouped]
                roles[right] = roles.pop(wrong)
                for group in predicted_groups:
                    group["region_ids"] = [right if rid == wrong else rid for rid in group.get("region_ids", [])]
        if diagnostic_repair is None:
            raise ValueError("; ".join(errors))

    rows = reference["rows"]
    by_id = {row["id"]: row for row in rows}
    known = sorted((row for row in rows if row["reading_order"] >= 0), key=lambda row: row["reading_order"])
    known_ids = [row["id"] for row in known]
    predicted_known = [rid for rid in ordered if rid in set(known_ids)]
    position = {rid: i for i, rid in enumerate(predicted_known)}
    order_pairs = [(a, b) for i, a in enumerate(known_ids) for b in known_ids[i+1:]]
    correct_pairs = sum(position[a] < position[b] for a, b in order_pairs)

    reference_groups = {}
    for row in rows:
        reference_groups.setdefault(row["semantic_unit"], []).append(row["id"])
    ref_pairs = pair_set(reference_groups.values())
    pred_pairs = pair_set(group.get("region_ids", []) for group in predicted_groups)
    tp = len(ref_pairs & pred_pairs)
    precision = tp / len(pred_pairs) if pred_pairs else (1.0 if not ref_pairs else 0.0)
    recall = tp / len(ref_pairs) if ref_pairs else 1.0
    pair_f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    role_correct = sum(roles[rid] == by_id[rid]["role"] for rid in expected)
    confusion = Counter((by_id[rid]["role"], roles[rid]) for rid in expected)
    result = {
        "schema": "bbvlm.blind-olr-evaluation/1",
        "page": request["page"],
        "split_role": "development",
        "reader": "gpt-6-luna",
        "passes": 1,
        "raw_structural_valid": structural_valid,
        "raw_structural_errors": errors,
        "diagnostic_id_repair": diagnostic_repair,
        "diagnostic_scores_accepted_for_gate": False if diagnostic_repair else True,
        "known_order_regions": len(known_ids),
        "unknown_or_unordered_regions": len(rows) - len(known_ids),
        "reading_order_pair_accuracy_known_subset": correct_pairs / len(order_pairs) if order_pairs else None,
        "reading_order_correct_pairs": correct_pairs,
        "reading_order_pairs": len(order_pairs),
        "semantic_group_pair_precision": precision,
        "semantic_group_pair_recall": recall,
        "semantic_group_pair_f1": pair_f1,
        "reference_semantic_units": len(reference_groups),
        "predicted_semantic_units": len(predicted_groups),
        "role_accuracy": role_correct / len(expected),
        "role_correct": role_correct,
        "roles": len(expected),
        "role_confusion": [{"reference": a, "predicted": b, "count": n} for (a, b), n in sorted(confusion.items())],
        "uncertain_region_ids": response.get("uncertain_region_ids", []),
        "reference_warning": "Agreement is measured against manually enriched distributed SSU/role/order labels on one development page. Negative source orders are excluded from order scoring; labels are not independent adjudication.",
        "leakage_control": request["leakage_control"],
    }
    (BASE / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
