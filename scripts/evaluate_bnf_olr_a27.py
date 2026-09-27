#!/usr/bin/env python3
"""Evaluate blind A27 VLM stream grouping/order against sealed PAGE groups."""
from __future__ import annotations
import hashlib,itertools,json,time
from pathlib import Path
import numpy as np
from lxml import etree as E
from bbvlm.semantic import group_header_units

ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/'experiments/loop/bnf-impact-olr-a27';A26=ROOT/'experiments/loop/bnf-impact-a26'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def points(node):
    raw=node.get('points')
    if raw:return np.asarray([[float(a),float(b)] for a,b in (v.split(',') for v in raw.split())])
    return np.asarray([[float(x.get('x')),float(x.get('y'))] for x in node.xpath('./*[local-name()="Point"]')])
def pairset(groups):return {tuple(sorted(p)) for g in groups for p in itertools.combinations(g,2)}
def prf(reference,prediction):
    tp=len(reference&prediction);p=tp/len(prediction) if prediction else 0.;r=tp/len(reference) if reference else 0.
    return {'true_positive':tp,'predicted':len(prediction),'reference':len(reference),'precision':p,'recall':r,'f1':2*p*r/(p+r) if p+r else 0.}
def order_accuracy(reference_groups,predicted_groups):
    predicted_order={token:(gi,pi) for gi,g in enumerate(predicted_groups) for pi,token in enumerate(g)}
    correct=total=covered=0
    for group in reference_groups:
        for a,b in itertools.combinations(group,2):
            total+=1
            if a in predicted_order and b in predicted_order and predicted_order[a][0]==predicted_order[b][0]:
                covered+=1;correct+=predicted_order[a][1]<predicted_order[b][1]
    return {'correct':correct,'covered_reference_pairs':covered,'reference_pairs':total,
      'accuracy_on_covered':correct/covered if covered else 0.,'end_to_end_recall':correct/total if total else 0.}

def main():
    started=time.perf_counter();split=json.loads((EXP/'split.json').read_text());opened=json.loads((EXP/'opened.json').read_text())
    checks={'protocol':EXP/'PROTOCOL.md','prompt':EXP/'VLM_PROMPT.md','preparer':ROOT/'scripts/prepare_bnf_olr_a27.py',
      'evaluator':ROOT/'scripts/evaluate_bnf_olr_a27.py','order_core':ROOT/'src/bbvlm/order.py',
      'semantic_core':ROOT/'src/bbvlm/semantic.py','archive_manifest':A26/'source/archive-manifest.json'}
    for key,path in checks.items():
        if sha(path)!=split['sealed_sha256'][key]:raise ValueError(f'sealed file changed: {key}')
    pred=json.loads((EXP/'candidate/luna.json').read_text());mapping=json.loads((EXP/'sealed-map.json').read_text())['token_to_source_id'];reverse={v:k for k,v in mapping.items()}
    tree=E.parse(str(EXP/'opened'/split['page']['xml']),E.XMLParser(resolve_entities=False,no_network=True));page=tree.xpath('//*[local-name()="Page"]')[0]
    regions=[];types={}
    for node in tree.xpath('//*[local-name()="TextRegion"]'):
        coords=node.xpath('./*[local-name()="Coords"]')
        if not coords or node.get('id') not in reverse:continue
        poly=points(coords[0]);rid=reverse[node.get('id')];regions.append({'id':rid,'bbox':[float(poly[:,0].min()),float(poly[:,1].min()),float(poly[:,0].max()),float(poly[:,1].max())]});types[rid]=node.get('type')
    reference=[]
    for group in tree.xpath('//*[local-name()="ReadingOrder"]//*[local-name()="OrderedGroup"]'):
        indexed=sorted(group.xpath('./*[local-name()="RegionRefIndexed"]'),key=lambda x:int(x.get('index')))
        values=[reverse[x.get('regionRef')] for x in indexed if x.get('regionRef') in reverse]
        if values:reference.append(values)
    if not regions or not reference:raise ValueError('fail closed: zero reference regions or ordered groups')
    all_tokens=set(mapping);roles=pred.get('roles',{});streams=[x.get('region_tokens',[]) for x in pred.get('streams',[])]
    flat=[x for g in streams for x in g];valid_roles={'TITLE','BODY','NON_ARTICLE'}
    exact_roles=set(roles)==all_tokens and set(roles.values())<=valid_roles
    duplicates=sorted({x for x in flat if flat.count(x)>1});unknown=sorted((set(flat)|set(roles))-all_tokens)
    candidate_content={x for x,v in roles.items() if v in {'TITLE','BODY'}};reference_content={x for g in reference for x in g}
    eligibility=prf(reference_content,candidate_content);grouping=prf(pairset(reference),pairset(streams));order=order_accuracy(reference,streams)
    oracle_roles={x:('HEADER' if types[x]=='heading' else 'TEXT' if types[x]=='paragraph' else 'OTHER') for x in all_tokens}
    baseline=group_header_units(regions,[0,0,float(page.get('imageWidth')),float(page.get('imageHeight'))],oracle_roles,reference_content,
      gap_ratio=.06,top_exclusion_ratio=.055,max_anchor_width_ratio=.55,min_anchor_width_ratio=.08,assign_by_overlap=True,merge_overlapping_headers=True)
    baseline_streams=[g['region_ids'] for g in baseline['groups'] if g['kind']=='ARTICLE']
    baseline_grouping=prf(pairset(reference),pairset(baseline_streams));baseline_order=order_accuracy(reference,baseline_streams)
    gate_conditions={'exact_role_coverage':exact_roles,'no_unknown_tokens':not unknown,'no_duplicate_stream_tokens':not duplicates,
      'stream_contract_matches_roles':set(flat)==candidate_content,'eligibility_f1_ge_098':eligibility['f1']>=.98,
      'stream_pair_f1_ge_090':grouping['f1']>=.90,'within_stream_order_accuracy_ge_098':order['accuracy_on_covered']>=.98,
      'stream_pair_f1_strictly_better_geometry_oracle_roles':grouping['f1']>baseline_grouping['f1']}
    report={'schema':'bbvlm.bnf-impact-olr-a27-report/1','page':split['page']['page'],
      'scope':'conditional on oracle BnF TextRegion polygons; one blind gpt-6-luna visual pass',
      'counts':{'regions':len(regions),'reference_ordered_streams':len(reference),'reference_content_regions':len(reference_content),'predicted_streams':len(streams)},
      'candidate':{'eligibility':eligibility,'stream_pair':grouping,'within_stream_order':order,'uncertain_tokens':pred.get('uncertain_tokens',[]),
        'unknown_tokens':unknown,'duplicate_stream_tokens':duplicates},
      'geometry_oracle_role_baseline':{'stream_pair':baseline_grouping,'within_stream_order':baseline_order,'predicted_streams':len(baseline_streams),
        'warning':'optimistic baseline uses reference PAGE region roles but never reference stream IDs/order'},
      'gate_conditions':gate_conditions,'conditional_gate_passed':all(gate_conditions.values()),
      'cost':{'new_vlm_tasks':1,'primary_reader':pred.get('reader'),'evaluator_seconds':time.perf_counter()-started},
      'reference_status':'official BnF manually produced region/order evidence; OrderedGroup is not an explicit article ID and is not independently adjudicated perfect truth',
      'accepted_for_project_completion_gate':False,
      'limitations':['Oracle TextRegion polygons; not end-to-end region detection.','One validation page only.','PAGE OrderedGroup is not explicit article truth.','No word boxes or OCR scored.','Reference is external manual GT, not a perfect-truth certificate.'],
      'invariants':{'sealed_before_open':True,'nonempty_reference_fail_closed':True,'opaque_tokens':True,'reader_denied_reference_xml_and_mapping':True,
        'opened_files_sha256_verified':all(sha(EXP/'opened'/f['name'])==f['sha256'] for f in opened['files'])}}
    (EXP/'output').mkdir(parents=True,exist_ok=True);(EXP/'output/report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
