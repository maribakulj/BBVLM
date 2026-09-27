"""Evaluate one role/filter pass followed by frozen CPU grouping and order."""
from collections import Counter
from pathlib import Path
import itertools
import json
import time

from bbvlm.binding import bind_role_filter_page
from bbvlm.semantic import group_header_units

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/loop/spiritualist-v1/semantic-v2-header-validation"


def pair_set(groups):
    return {tuple(sorted(pair)) for members in groups for pair in itertools.combinations(members,2)}


def bcubed(reference_groups, predicted_groups, items):
    ref_by, pred_by = {}, {}
    for members in reference_groups:
        for rid in members: ref_by[rid] = set(members)
    for members in predicted_groups:
        for rid in members: pred_by[rid] = set(members)
    p = sum(len(ref_by[r]&pred_by[r])/len(pred_by[r]) for r in items)/len(items)
    q = sum(len(ref_by[r]&pred_by[r])/len(ref_by[r]) for r in items)/len(items)
    return p,q,2*p*q/(p+q) if p+q else 0.0


def main():
    request=json.loads((BASE/"input/request.json").read_text());reference=json.loads((BASE/"evaluation/reference.json").read_text())
    binding=json.loads((BASE/"evaluation/token-binding.json").read_text())["token_to_id"]
    response=json.loads((BASE/"input/luna.response.json").read_text());errors=[];bound=None
    if response.get("schema")!="bbvlm.blind-role-filter-response/1" or response.get("page")!=request["page"]: errors.append("unexpected schema or page")
    else:
        try: bound=bind_role_filter_page(response,binding)
        except (KeyError,TypeError,ValueError) as exc: errors.append(str(exc))
    raw_valid=not errors;metrics=None
    if raw_valid:
        rows=reference["regions"];ids={r["id"] for r in rows};by_id={r["id"]:r for r in rows}
        ref_eligible={r["id"] for r in rows if r["reading_order"]>=0};pred_eligible=set(bound["eligible_region_ids"]);tp=len(ref_eligible&pred_eligible)
        ep=tp/len(pred_eligible) if pred_eligible else 0.0;er=tp/len(ref_eligible) if ref_eligible else 1.0;ef=2*ep*er/(ep+er) if ep+er else 0.0
        cfg=request["frozen_cpu_grouping"];oc=cfg["order_config"]
        start=time.perf_counter();proposal=group_header_units(
            [{"id":r["id"],"bbox":r["bbox"]} for r in rows],reference["page_bbox"],bound["roles"],bound["eligible_region_ids"],
            gap_ratio=oc["gap_ratio"],top_exclusion_ratio=oc["top_exclusion_ratio"],max_anchor_width_ratio=oc["max_anchor_width_ratio"],
            merge_overlapping_headers=cfg["merge_overlapping_headers"]);elapsed=time.perf_counter()-start
        reference_groups={}
        for row in rows: reference_groups.setdefault(row["semantic_unit"],[]).append(row["id"])
        predicted_groups=[g["region_ids"] for g in proposal["groups"]];rp,pp=pair_set(reference_groups.values()),pair_set(predicted_groups)
        gtp=len(rp&pp);gp=gtp/len(pp) if pp else (1.0 if not rp else 0.0);gr=gtp/len(rp) if rp else 1.0;gf=2*gp*gr/(gp+gr) if gp+gr else 0.0
        bp,br,bf=bcubed(list(reference_groups.values()),predicted_groups,ids)
        role_correct=sum(bound["roles"][rid]==by_id[rid]["role"] for rid in ids)
        confusion=Counter((by_id[rid]["role"],bound["roles"][rid]) for rid in ids)
        id_to_token={rid:token for token,rid in binding.items()}
        role_mismatches=[{"token":id_to_token[rid],"region_id":rid,"source_id":by_id[rid]["source_id"],
                          "bbox":by_id[rid]["bbox"],"reference_role":by_id[rid]["role"],
                          "predicted_role":bound["roles"][rid],"reference_eligible":rid in ref_eligible,
                          "predicted_eligible":rid in pred_eligible}
                         for rid in sorted(ids) if bound["roles"][rid]!=by_id[rid]["role"]]
        predicted_order=[rid for rid in proposal["order"]["ordered_region_ids"] if rid in pred_eligible];pos={rid:i for i,rid in enumerate(predicted_order)}
        known=[r["id"] for r in sorted(rows,key=lambda r:r["reading_order"]) if r["reading_order"]>=0]
        op=[(a,b) for i,a in enumerate(known) for b in known[i+1:]];correct=sum(a in pos and b in pos and pos[a]<pos[b] for a,b in op)
        metrics={"regions":len(rows),"reference_eligible":len(ref_eligible),"predicted_eligible":len(pred_eligible),"eligibility_true_positive":tp,
                 "eligibility_precision":ep,"eligibility_recall":er,"eligibility_f1":ef,
                 "contamination_region_ids":sorted(pred_eligible-ref_eligible),"missing_eligible_region_ids":sorted(ref_eligible-pred_eligible),
                 "role_correct":role_correct,"role_accuracy":role_correct/len(ids),
                 "role_confusion":[{"reference":a,"predicted":b,"count":n} for (a,b),n in sorted(confusion.items())],
                 "role_mismatches":role_mismatches,
                 "semantic_group_true_positive_pairs":gtp,"semantic_group_predicted_pairs":len(pp),"semantic_group_reference_pairs":len(rp),
                 "semantic_group_pair_precision":gp,"semantic_group_pair_recall":gr,"semantic_group_pair_f1":gf,
                 "semantic_group_false_positive_pairs":len(pp-rp),"semantic_group_false_negative_pairs":len(rp-pp),
                 "semantic_group_bcubed_precision":bp,"semantic_group_bcubed_recall":br,"semantic_group_bcubed_f1":bf,
                 "reference_semantic_units":len(reference_groups),"predicted_semantic_units":len(predicted_groups),
                 "predicted_groups":proposal["groups"],
                 "combined_order_correct_reference_pairs":correct,"combined_order_reference_pairs":len(op),
                 "combined_order_pair_recall":correct/len(op) if op else 1.0,"cpu_order_and_grouping_runtime_seconds":elapsed,
                 "cpu_inferred_columns":len(proposal["order"]["column_anchors_x"]),"uncertain_region_ids":bound["uncertain_region_ids"]}
    gates=request["frozen_gates"]
    passed=bool(raw_valid and metrics and metrics["eligibility_precision"]>=gates["eligibility_precision_min"] and metrics["eligibility_recall"]>=gates["eligibility_recall_min"]
                and metrics["role_accuracy"]>=gates["role_accuracy_min"] and metrics["semantic_group_pair_f1"]>=gates["semantic_group_pair_f1_min"]
                and metrics["combined_order_pair_recall"]>=gates["combined_order_pair_recall_min"])
    result={"schema":"bbvlm.role-filter-plus-cpu-structure-evaluation/1","page":request["page"],"split_role":"frozen_validation_consumed_after_this_evaluation",
            "reader":"gpt-6-luna","passes":{"vlm_role_filter":1,"vlm_grouping":0,"vlm_order":0,"cpu_structure":1},
            "cost_note":"One authorized Luna pass; model latency/token billing unavailable. CPU structure time measured below.",
            "raw_structural_valid":raw_valid,"raw_structural_errors":errors,"repair_attempted":False,"metrics":metrics,
            "frozen_gates":gates,"content_gate_passed":passed,"accepted_for_project_completion_gate":False,
            "reference_warning":request["reference_warning"],"leakage_control":request["leakage_control"],
            "interpretation":"Agreement with provisional corpus labels on one page; no article or ground-truth certification."}
    (BASE/"report.json").write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2))


if __name__ == "__main__": main()
