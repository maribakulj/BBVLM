#!/usr/bin/env python3
"""Evaluate A29 raw and CPU-merged one-pass Luna streams."""
from __future__ import annotations
import hashlib,json,time
from pathlib import Path
import numpy as np
from lxml import etree as E
from bbvlm.olr_continuation import merge_conservative_streams
from bbvlm.semantic import group_header_units
import evaluate_bnf_olr_a27 as metrics

ROOT=Path(__file__).resolve().parents[1];EXP=ROOT/'experiments/loop/bnf-impact-olr-a29';A26=ROOT/'experiments/loop/bnf-impact-a26'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def points(node):
    raw=node.get('points')
    if raw:return np.asarray([[float(a),float(b)] for a,b in (v.split(',') for v in raw.split())])
    return np.asarray([[float(x.get('x')),float(x.get('y'))] for x in node.xpath('./*[local-name()="Point"]')])

def main():
    started=time.perf_counter();split=json.loads((EXP/'split.json').read_text());opened=json.loads((EXP/'opened.json').read_text())
    checks={'protocol':EXP/'PROTOCOL.md','prompt':EXP/'VLM_PROMPT.md','preparer':ROOT/'scripts/prepare_bnf_olr_a29.py','evaluator':ROOT/'scripts/evaluate_bnf_olr_a29.py','merger':ROOT/'src/bbvlm/olr_continuation.py','development':EXP/'development-report.json','archive_manifest':A26/'source/archive-manifest.json'}
    for key,path in checks.items():
        if sha(path)!=split['sealed_sha256'][key]:raise ValueError(f'sealed file changed: {key}')
    pred=json.loads((EXP/'candidate/luna.json').read_text());mapping=json.loads((EXP/'sealed-map.json').read_text())['token_to_source_id'];reverse={v:k for k,v in mapping.items()};tree=E.parse(str(EXP/'opened'/split['page']['xml']),E.XMLParser(resolve_entities=False,no_network=True));page=tree.xpath('//*[local-name()="Page"]')[0];width=float(page.get('imageWidth'));height=float(page.get('imageHeight'))
    regions=[];boxes={};types={}
    for node in tree.xpath('//*[local-name()="TextRegion"]'):
        if node.get('id') not in reverse:continue
        coords=node.xpath('./*[local-name()="Coords"]')
        if not coords:continue
        poly=points(coords[0]);token=reverse[node.get('id')];box=(float(poly[:,0].min()),float(poly[:,1].min()),float(poly[:,0].max()),float(poly[:,1].max()));boxes[token]=box;regions.append({'id':token,'bbox':list(box)});types[token]=node.get('type')
    reference=[]
    for group in tree.xpath('//*[local-name()="ReadingOrder"]//*[local-name()="OrderedGroup"]'):
        indexed=sorted(group.xpath('./*[local-name()="RegionRefIndexed"]'),key=lambda x:int(x.get('index')));values=[reverse[x.get('regionRef')] for x in indexed if x.get('regionRef') in reverse]
        if values:reference.append(values)
    if not regions or not reference:raise ValueError('fail closed: zero reference regions or ordered groups')
    all_tokens=set(mapping);roles=pred.get('roles',{});raw=[x.get('region_tokens',[]) for x in pred.get('streams',[])];flat=[x for g in raw for x in g];candidate_content={x for x,v in roles.items() if v in {'TITLE','BODY'}};reference_content={x for g in reference for x in g};merged=merge_conservative_streams(raw,boxes,width)
    unknown=sorted((set(flat)|set(roles))-all_tokens);duplicates=sorted({x for x in flat if flat.count(x)>1});eligibility=metrics.prf(reference_content,candidate_content)
    def scored(groups):return {'stream_pair':metrics.prf(metrics.pairset(reference),metrics.pairset(groups)),'within_stream_order':metrics.order_accuracy(reference,groups),'streams':len(groups)}
    raw_score=scored(raw);merged_score=scored(merged)
    oracle_roles={x:('HEADER' if types[x]=='heading' else 'TEXT' if types[x]=='paragraph' else 'OTHER') for x in all_tokens};baseline=group_header_units(regions,[0,0,width,height],oracle_roles,reference_content,gap_ratio=.06,top_exclusion_ratio=.055,max_anchor_width_ratio=.55,min_anchor_width_ratio=.08,assign_by_overlap=True,merge_overlapping_headers=True);baseline_score=scored([g['region_ids'] for g in baseline['groups'] if g['kind']=='ARTICLE'])
    conditions={'exact_role_coverage':set(roles)==all_tokens and set(roles.values())<={'TITLE','BODY','OTHER'},'no_unknown_tokens':not unknown,'no_duplicate_stream_tokens':not duplicates,'stream_contract_matches_roles':set(flat)==candidate_content,'eligibility_f1_ge_098':eligibility['f1']>=.98,'merged_stream_pair_f1_ge_090':merged_score['stream_pair']['f1']>=.90,'merged_order_recall_ge_090':merged_score['within_stream_order']['end_to_end_recall']>=.90,'merged_strictly_better_raw':merged_score['stream_pair']['f1']>raw_score['stream_pair']['f1'],'merged_strictly_better_geometry':merged_score['stream_pair']['f1']>baseline_score['stream_pair']['f1']}
    report={'schema':'bbvlm.bnf-impact-olr-a29-report/1','page':split['page']['page'],'scope':'oracle BnF TextRegion polygons; one blind Luna visual pass plus frozen CPU continuation merger','counts':{'regions':len(regions),'reference_streams':len(reference),'reference_content_regions':len(reference_content)},'eligibility':eligibility,'raw_vlm':raw_score,'merged':merged_score,'geometry_oracle_role_baseline':baseline_score,'candidate_integrity':{'unknown_tokens':unknown,'duplicate_stream_tokens':duplicates,'uncertain_tokens':pred.get('uncertain_tokens',[])},'gate_conditions':conditions,'conditional_gate_passed':all(conditions.values()),'cost':{'new_vlm_tasks':1,'reader':pred.get('reader'),'cpu_merger_seconds_included_in_evaluator':time.perf_counter()-started},'accepted_for_project_completion_gate':False,'reference_status':'official BnF manually produced region/order evidence; OrderedGroup is not explicit article ID or perfect-truth certificate','limitations':['One page and oracle region polygons.','No OCR or word boxes scored.','OrderedGroup semantics may be broader than articles.'],'invariants':{'sealed_before_open':True,'nonempty_reference_fail_closed':True,'reader_denied_xml_mapping_and_a27':True,'opened_files_sha256_verified':all(sha(EXP/'opened'/f['name'])==f['sha256'] for f in opened['files'])}}
    (EXP/'output').mkdir(parents=True,exist_ok=True);(EXP/'output/report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
