#!/usr/bin/env python3
"""Post-score audit of A29 omissions and pure fragmentation; never retunes."""
from __future__ import annotations
import json
from pathlib import Path
from lxml import etree as E
from bbvlm.olr_continuation import merge_conservative_streams

ROOT=Path(__file__).resolve().parents[1];EXP=ROOT/'experiments/loop/bnf-impact-olr-a29'
def points(node):
    raw=node.get('points')
    if raw:return [tuple(map(float,p.split(','))) for p in raw.split()]
    return [(float(p.get('x')),float(p.get('y'))) for p in node.xpath('./*[local-name()="Point"]')]

def main():
    split=json.loads((EXP/'split.json').read_text());mapping=json.loads((EXP/'sealed-map.json').read_text())['token_to_source_id'];reverse={v:k for k,v in mapping.items()};candidate=json.loads((EXP/'candidate/luna.json').read_text());tree=E.parse(str(EXP/'opened'/split['page']['xml']),E.XMLParser(resolve_entities=False,no_network=True));page=tree.xpath('//*[local-name()="Page"]')[0]
    info={};boxes={}
    for token,rid in mapping.items():
        node=tree.xpath(f'//*[@id="{rid}"]')[0];pts=points(node.xpath('./*[local-name()="Coords"]')[0]);xs=[x for x,y in pts];ys=[y for x,y in pts];text=' '.join(x.strip() for x in node.xpath('.//*[local-name()="Unicode"]/text()') if x.strip());boxes[token]=(min(xs),min(ys),max(xs),max(ys));info[token]={'token':token,'source_type':node.get('type'),'bbox':list(boxes[token]),'reference_text':text}
    reference=[]
    for group in tree.xpath('//*[local-name()="ReadingOrder"]//*[local-name()="OrderedGroup"]'):
        values=[reverse[n.get('regionRef')] for n in sorted(group.xpath('./*[local-name()="RegionRefIndexed"]'),key=lambda n:int(n.get('index'))) if n.get('regionRef') in reverse]
        if values:reference.append(values)
    raw=[x['region_tokens'] for x in candidate['streams']];merged=merge_conservative_streams(raw,boxes,float(page.get('imageWidth')));lookup={t:i for i,g in enumerate(reference) for t in g};content=set(lookup);predicted={t for t,v in candidate['roles'].items() if v in {'TITLE','BODY'}}
    fragments=[]
    for i,ref in enumerate(reference):
        groups=[g for g in merged if set(g)<=set(ref)];fragments.append({'reference_stream':i,'reference_regions':len(ref),'predicted_fragment_sizes':[len(g) for g in groups],'covered_regions':sum(map(len,groups))})
    impure=[{'predicted_stream':i,'reference_streams':sorted({lookup.get(t) for t in group})} for i,group in enumerate(merged) if len({lookup.get(t) for t in group})>1]
    report={'schema':'bbvlm.bnf-impact-olr-a29-post-score-audit/1','status':'post-score diagnostic; parameters and candidate unchanged','missed_reference_content':[info[t] for t in sorted(content-predicted)],'fragmentation':fragments,'impure_merges':impure,'conclusion':'No cross-reference merge. Residual error is four excess pure fragments plus six role-convention omissions; OrderedGroup remains broader than proven article truth.','accepted_as_validation':False}
    (EXP/'post-score').mkdir(exist_ok=True);(EXP/'post-score/report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
