#!/usr/bin/env python3
"""Score the frozen continuation rule on consumed A27 development data."""
from __future__ import annotations
import json
from pathlib import Path
from lxml import etree as E
from bbvlm.olr_continuation import merge_conservative_streams
import evaluate_bnf_olr_a27 as metrics

ROOT=Path(__file__).resolve().parents[1]
A27=ROOT/'experiments/loop/bnf-impact-olr-a27'
OUT=ROOT/'experiments/loop/bnf-impact-olr-a29/development-report.json'

def points(node):
    raw=node.get('points')
    if raw:return [tuple(map(float,p.split(','))) for p in raw.split()]
    return [(float(p.get('x')),float(p.get('y'))) for p in node.xpath('./*[local-name()="Point"]')]

def main():
    split=json.loads((A27/'split.json').read_text()); mapping=json.loads((A27/'sealed-map.json').read_text())['token_to_source_id']; reverse={v:k for k,v in mapping.items()}
    tree=E.parse(str(A27/'opened'/split['page']['xml']),E.XMLParser(resolve_entities=False,no_network=True)); page=tree.xpath('//*[local-name()="Page"]')[0]; width=float(page.get('imageWidth'))
    boxes={}
    for token,rid in mapping.items():
        node=tree.xpath(f'//*[@id="{rid}"]')[0]; pts=points(node.xpath('./*[local-name()="Coords"]')[0]); xs=[p[0] for p in pts];ys=[p[1] for p in pts];boxes[token]=(min(xs),min(ys),max(xs),max(ys))
    reference=[]
    for group in tree.xpath('//*[local-name()="ReadingOrder"]//*[local-name()="OrderedGroup"]'):
        nodes=sorted(group.xpath('./*[local-name()="RegionRefIndexed"]'),key=lambda x:int(x.get('index'))); values=[reverse[x.get('regionRef')] for x in nodes if x.get('regionRef') in reverse]
        if values:reference.append(values)
    raw=[x['region_tokens'] for x in json.loads((A27/'candidate/sol.json').read_text())['streams']]
    merged=merge_conservative_streams(raw,boxes,width)
    report={'schema':'bbvlm.olr-continuation-a29-development/1','status':'development_on_consumed_a27',
      'parameters':{'max_gap_width_ratio':0.007,'min_horizontal_overlap':0.60},
      'counts':{'reference_streams':len(reference),'raw_streams':len(raw),'merged_streams':len(merged)},
      'raw':{'stream_pair':metrics.prf(metrics.pairset(reference),metrics.pairset(raw)),'order':metrics.order_accuracy(reference,raw)},
      'merged':{'stream_pair':metrics.prf(metrics.pairset(reference),metrics.pairset(merged)),'order':metrics.order_accuracy(reference,merged)},
      'accepted_as_validation':False}
    OUT.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
