#!/usr/bin/env python
"""Notation privée des sorties de segmentation figées, jamais en production."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from evaluation import load_reference,segmentation


def evaluate(manifest, outputs, split,reference_dpi=None):
    manifest=json.loads(Path(manifest).read_text());records=[]
    for row in manifest['pages']:
        if row['split']!=split:continue
        if hashlib.sha256(Path(row['reference']).read_bytes()).hexdigest()!=row['reference_sha256']:
            raise ValueError('Référence modifiée : '+row['id'])
        ref=load_reference(row['reference'],dpi=reference_dpi);out=Path(outputs)/row['id']
        record=dict(id=row['id'],reference_lines=len(ref),criteria_met=False,variants={})
        for variant,name in [('detector','segmentation.json'),('ink','segmentation-ink.json')]:
            if not (out/name).exists():
                record['variants'][variant]=dict(status='missing',recall=0,criteria_met=False);continue
            predicted=json.loads((out/name).read_text())
            record['variants'][variant]={str(t):segmentation(ref,predicted,t) for t in (.5,.75)}
        records.append(record)
    return dict(split=split,rows=records,protocol_sha256=manifest['protocol_sha256'],criteria_met=False,reference_dpi=reference_dpi)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('manifest');ap.add_argument('outputs');ap.add_argument('report')
    ap.add_argument('--split',choices=('dev','reserved'),required=True);ap.add_argument('--reference-dpi',type=float);args=ap.parse_args()
    report=evaluate(args.manifest,args.outputs,args.split,args.reference_dpi)
    Path(args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps([dict(id=r['id'],variants={v:{t:{k:s[k] for k in ('matched','predicted','recall','f1')}
          for t,s in metrics.items()} if 'status' not in metrics else metrics for v,metrics in r['variants'].items()}) for r in report['rows']]))
