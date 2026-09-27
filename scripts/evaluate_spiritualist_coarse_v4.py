"""Evaluate coarse VLM roles plus frozen CPU fine-role/order/grouping."""
from collections import Counter,defaultdict
from pathlib import Path
import itertools,json,time

from bbvlm.binding import bind_coarse_faceted_page
from bbvlm.semantic import group_header_units,refine_stream_roles_by_height

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/"experiments/loop/spiritualist-v1/semantic-v4-coarse-validation"


def pairs(groups):return {tuple(sorted(p)) for g in groups for p in itertools.combinations(g,2)}


def bcubed(reference,predicted,items):
    rb,pb={},{}
    for g in reference:
        for r in g:rb[r]=set(g)
    for g in predicted:
        for r in g:pb[r]=set(g)
    p=sum(len(rb[r]&pb[r])/len(pb[r]) for r in items)/len(items);q=sum(len(rb[r]&pb[r])/len(rb[r]) for r in items)/len(items)
    return p,q,2*p*q/(p+q) if p+q else 0.0


def reference_coarse(role):
    if role in {"HEADER","TEXT"}:return "STREAM"
    return role if role in {"MASTHEAD","OTHER"} else "UNKNOWN"


def main():
    request=json.loads((BASE/"input/request.json").read_text());profile=request["frozen_profile"]
    reference=json.loads((BASE/"evaluation/reference.json").read_text());binding=json.loads((BASE/"evaluation/token-binding.json").read_text())["token_to_id"]
    response=json.loads((BASE/"input/luna.response.json").read_text());errors=[];bound=None
    if response.get("schema")!="bbvlm.blind-coarse-faceted-response/1" or response.get("page")!=request["page"]:errors.append("unexpected schema or page")
    else:
        try:bound=bind_coarse_faceted_page(response,binding)
        except (KeyError,TypeError,ValueError) as exc:errors.append(str(exc))
    raw_valid=not errors;metrics=None
    if raw_valid:
        rows=reference["regions"];ids={r["id"] for r in rows};by_id={r["id"]:r for r in rows};id_to_token={rid:t for t,rid in binding.items()}
        regions=[{"id":r["id"],"bbox":r["bbox"]} for r in rows]
        coarse=bound["coarse_roles"];pred_eligible={rid for rid,role in coarse.items() if role=="STREAM"}
        roles=refine_stream_roles_by_height(regions,reference["page_bbox"],coarse,
          max_header_height_page_ratio=profile["height_config"]["max_header_height_page_ratio"])
        ref_eligible={r["id"] for r in rows if r["reading_order"]>=0};tp=len(ref_eligible&pred_eligible)
        ep=tp/len(pred_eligible) if pred_eligible else 0.;er=tp/len(ref_eligible) if ref_eligible else 1.;ef=2*ep*er/(ep+er) if ep+er else 0.
        cfg=json.loads((ROOT/"experiments/loop/spiritualist-v1/semantic-v2-header/config.json").read_text());oc=cfg["order_config"]
        if profile.get("order_config"):
            oc=json.loads((ROOT/"experiments/loop/spiritualist-v1"/profile["order_config"]["source"]).read_text())
        order_extra={k:oc[k] for k in ("min_anchor_width_ratio","assign_by_overlap") if k in oc}
        start=time.perf_counter();proposal=group_header_units(regions,reference["page_bbox"],roles,sorted(pred_eligible),
          gap_ratio=oc["gap_ratio"],top_exclusion_ratio=oc["top_exclusion_ratio"],max_anchor_width_ratio=oc["max_anchor_width_ratio"],
          merge_overlapping_headers=cfg["merge_overlapping_headers"],**order_extra);elapsed=time.perf_counter()-start
        rg=defaultdict(list)
        for row in rows:rg[row["semantic_unit"]].append(row["id"])
        pg=[g["region_ids"] for g in proposal["groups"]];rp,pp=pairs(rg.values()),pairs(pg);gtp=len(rp&pp)
        gp=gtp/len(pp) if pp else (1. if not rp else 0.);gr=gtp/len(rp) if rp else 1.;gf=2*gp*gr/(gp+gr) if gp+gr else 0.;bp,br,bf=bcubed(rg.values(),pg,ids)
        coarse_correct=sum(coarse[rid]==reference_coarse(by_id[rid]["physical_role"]) for rid in ids)
        fine_correct=sum(roles[rid]==by_id[rid]["physical_role"] for rid in ids)
        coarse_confusion=Counter((reference_coarse(by_id[rid]["physical_role"]),coarse[rid]) for rid in ids)
        fine_confusion=Counter((by_id[rid]["physical_role"],roles[rid]) for rid in ids)
        mismatches=[{"token":id_to_token[rid],"region_id":rid,"source_id":by_id[rid]["source_id"],"bbox":by_id[rid]["bbox"],
          "reference_role":by_id[rid]["physical_role"],"reference_coarse_role":reference_coarse(by_id[rid]["physical_role"]),
          "predicted_coarse_role":coarse[rid],"predicted_fine_role":roles[rid]} for rid in sorted(ids)
          if roles[rid]!=by_id[rid]["physical_role"] or coarse[rid]!=reference_coarse(by_id[rid]["physical_role"])]
        ordered=[rid for rid in proposal["order"]["ordered_region_ids"] if rid in pred_eligible];pos={rid:i for i,rid in enumerate(ordered)}
        known=[r["id"] for r in sorted(rows,key=lambda r:r["reading_order"]) if r["reading_order"]>=0];op=[(a,b) for i,a in enumerate(known) for b in known[i+1:]]
        correct=sum(a in pos and b in pos and pos[a]<pos[b] for a,b in op)
        unit_genres=[]
        for i,g in enumerate(proposal["groups"],1):
            votes=Counter(bound["editorial_genres"][rid] for rid in g["region_ids"]);labels=sorted(votes)
            unit_genres.append({"unit":f"U{i}","region_ids":g["region_ids"],"genre_labels":labels,
                                "proposed_genre":labels[0] if len(labels)==1 else "UNKNOWN","needs_review":len(labels)!=1})
        metrics={"regions":len(rows),"reference_eligible":len(ref_eligible),"predicted_eligible":len(pred_eligible),"eligibility_true_positive":tp,
          "eligibility_precision":ep,"eligibility_recall":er,"eligibility_f1":ef,"contamination_region_ids":sorted(pred_eligible-ref_eligible),
          "missing_eligible_region_ids":sorted(ref_eligible-pred_eligible),"coarse_role_correct":coarse_correct,"coarse_role_accuracy":coarse_correct/len(ids),
          "coarse_role_confusion":[{"reference":a,"predicted":b,"count":n} for (a,b),n in sorted(coarse_confusion.items())],
          "fine_physical_role_correct":fine_correct,"fine_physical_role_accuracy":fine_correct/len(ids),
          "fine_physical_role_confusion":[{"reference":a,"predicted":b,"count":n} for (a,b),n in sorted(fine_confusion.items())],
          "role_mismatches":mismatches,"semantic_group_pair_precision":gp,"semantic_group_pair_recall":gr,"semantic_group_pair_f1":gf,
          "semantic_group_false_positive_pairs":len(pp-rp),"semantic_group_false_negative_pairs":len(rp-pp),
          "semantic_group_bcubed_precision":bp,"semantic_group_bcubed_recall":br,"semantic_group_bcubed_f1":bf,
          "reference_semantic_units":len(rg),"predicted_semantic_units":len(pg),"combined_order_correct_reference_pairs":correct,
          "combined_order_reference_pairs":len(op),"combined_order_pair_recall":correct/len(op) if op else 1.,"cpu_runtime_seconds":elapsed,
          "cpu_inferred_columns":len(proposal["order"]["column_anchors_x"]),"editorial_genre_counts":dict(sorted(Counter(bound["editorial_genres"].values()).items())),
          "editorial_unit_proposals":unit_genres,"uncertain_coarse_region_ids":bound["uncertain_coarse_region_ids"],
          "uncertain_genre_region_ids":bound["uncertain_genre_region_ids"]}
    gates=profile["frozen_gates"]
    passed=bool(raw_valid and metrics and metrics["eligibility_precision"]>=gates["eligibility_precision_min"] and metrics["eligibility_recall"]>=gates["eligibility_recall_min"]
      and metrics["coarse_role_accuracy"]>=gates["coarse_role_accuracy_min"] and metrics["fine_physical_role_accuracy"]>=gates["fine_physical_role_accuracy_min"]
      and metrics["semantic_group_pair_f1"]>=gates["semantic_group_pair_f1_min"] and metrics["combined_order_pair_recall"]>=gates["combined_order_pair_recall_min"])
    result={"schema":"bbvlm.coarse-role-plus-cpu-structure-evaluation/1","page":request["page"],"split_role":"frozen_validation_consumed_after_this_evaluation",
      "reader":"gpt-6-luna","passes":{"vlm_coarse_roles_and_genre":1,"vlm_order":0,"vlm_grouping":0,"cpu_structure":1},
      "raw_structural_valid":raw_valid,"raw_structural_errors":errors,"repair_attempted":False,"metrics":metrics,"frozen_gates":gates,
      "content_gate_passed":passed,"editorial_genre_scored":False,"editorial_genre_status":"proposals_with_provenance_only",
      "accepted_for_project_completion_gate":False,"reference_warning":request["reference_warning"],"leakage_control":request["leakage_control"],
      "cost_note":"One authorized Luna pass; token billing unavailable. CPU runtime measured.",
      "interpretation":"Agreement with provisional coarse/fine physical role, order and SSU labels on one page; genre is not ground truth."}
    (BASE/"report.json").write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2))


if __name__=="__main__":main()
