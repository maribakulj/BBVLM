#!/usr/bin/env python3
"""Post-hoc targeted Sol diagnostic after A27 Luna singleton failure."""
from __future__ import annotations
import json
from pathlib import Path
from lxml import etree as E
import evaluate_bnf_olr_a27 as base

ROOT=Path(__file__).resolve().parents[1];EXP=ROOT/'experiments/loop/bnf-impact-olr-a27'

def main():
    split=json.loads((EXP/'split.json').read_text());mapping=json.loads((EXP/'sealed-map.json').read_text())['token_to_source_id'];reverse={v:k for k,v in mapping.items()}
    pred=json.loads((EXP/'candidate/sol.json').read_text());tree=E.parse(str(EXP/'opened'/split['page']['xml']),E.XMLParser(resolve_entities=False,no_network=True))
    reference=[]
    for group in tree.xpath('//*[local-name()="ReadingOrder"]//*[local-name()="OrderedGroup"]'):
        nodes=sorted(group.xpath('./*[local-name()="RegionRefIndexed"]'),key=lambda x:int(x.get('index')))
        values=[reverse[x.get('regionRef')] for x in nodes if x.get('regionRef') in reverse]
        if values:reference.append(values)
    if not reference:raise ValueError('fail closed: zero ordered streams')
    all_tokens=set(mapping);roles=pred.get('roles',{});streams=[x.get('region_tokens',[]) for x in pred.get('streams',[])];flat=[x for g in streams for x in g]
    content={x for x,v in roles.items() if v in {'TITLE','BODY'}};reference_content={x for g in reference for x in g}
    eligibility=base.prf(reference_content,content);grouping=base.prf(base.pairset(reference),base.pairset(streams));order=base.order_accuracy(reference,streams)
    duplicates=sorted({x for x in flat if flat.count(x)>1});unknown=sorted((set(flat)|set(roles))-all_tokens)
    luna=json.loads((EXP/'output/report.json').read_text());report={'schema':'bbvlm.bnf-impact-olr-a27-sol-escalation/1',
      'status':'post-hoc targeted escalation after Luna structural abstention; not preregistered independent validation',
      'scope':'same opaque visual inputs; Sol denied GT, mapping and Luna output; oracle TextRegion polygons',
      'counts':{'regions':len(all_tokens),'reference_ordered_streams':len(reference),'predicted_streams':len(streams)},
      'candidate':{'eligibility':eligibility,'stream_pair':grouping,'within_stream_order':order,
        'exact_role_coverage':set(roles)==all_tokens,'stream_contract_matches_roles':set(flat)==content,
        'unknown_tokens':unknown,'duplicate_stream_tokens':duplicates,'uncertain_tokens':pred.get('uncertain_tokens',[])},
      'comparison':{'luna_stream_pair_f1':luna['candidate']['stream_pair']['f1'],
        'geometry_oracle_role_stream_pair_f1':luna['geometry_oracle_role_baseline']['stream_pair']['f1'],
        'sol_stream_pair_f1':grouping['f1'],'sol_end_to_end_order_pair_recall':order['end_to_end_recall']},
      'cost':{'new_vlm_tasks':1,'reader':'gpt-6-sol','token_and_billing_cost':'not exposed'},
      'accepted_for_project_completion_gate':False,
      'limitations':['Post-hoc prompt correction after Luna singleton failure.','One page; oracle region polygons.','OrderedGroup is not explicit article truth.','No OCR or word boxes scored.']}
    (EXP/'output/sol-escalation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

