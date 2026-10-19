#!/usr/bin/env python
"""Audit de la règle de mesure ; ne change ni la sélection ni les critères."""
from pathlib import Path
from collections import Counter
import argparse,json,sys
from PIL import Image
from lxml import etree
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from evaluation import load_reference


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('manifest');ap.add_argument('output');ap.add_argument('--reference-dpi',type=float);args=ap.parse_args()
    result=[]
    for row in json.loads(Path(args.manifest).read_text())['pages']:
        ref=load_reference(row['reference'],dpi=args.reference_dpi);root=etree.parse(row['reference'])
        entry={k:row[k] for k in ('id','family','split','human_text','olr_gold')}
        entry.update(image_size=list(Image.open(row['image']).size),reference_lines=len(ref),
                     reference_characters=sum(len(l['text']) for l in ref),
                     word_geometry_lines=sum(bool(l['words']) for l in ref),
                     actual_word_boxes=sum(len(l['words']) for l in ref),
                     word_annotation_granularity=dict(Counter(l.get('word_annotation_granularity','word') for l in ref)),
                     caveat='Annotation completeness outside referenced lines is unproven; do not erase unmatched predictions or declare invented text without image audit.')
        result.append(entry)
    Path(args.output).write_text(json.dumps(dict(pages=result,selection_unchanged=True,criteria_unchanged=True),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(pages=len(result),human_text_pages=sum(r['human_text'] for r in result),
                         word_geometry_pages=sum(r['actual_word_boxes']>0 for r in result),
                         olr_pages=sum(r['olr_gold'] for r in result))))
