#!/usr/bin/env python
"""Références privées exclusivement dans ce processus de notation."""
from pathlib import Path
import argparse
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from page_text_evaluation import evaluate

if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('manifest');ap.add_argument('outputs');ap.add_argument('report')
    ap.add_argument('--split',choices=('dev','reserved'),required=True)
    ap.add_argument('--reference-dpi',type=float)
    args=ap.parse_args()
    report=evaluate(args.manifest,args.outputs,args.split,args.reference_dpi)
    Path(args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(dict(pages=report['pages'],measured=report['measured'],missing=report['missing'],criteria_met=False)))
