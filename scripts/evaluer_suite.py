#!/usr/bin/env python
"""Évaluation hors production ; manifeste privé, aucune référence vers Gemini."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from evaluation import load_reference,score,match_boxes,exported_annotations,olr_detection,article_pairwise


def score_olr(reference_path, annotations, olr, axel):
    sys.path.insert(0,str(Path(axel)/'src'))
    from axel.olr.page import load_page
    from axel.olr.evaluate import OlrOutput,score_page
    from axel.olr.metrics import Box
    from export_training import polygon
    gt=load_page(Path(reference_path))
    types={'text':'texte','heading':'titre','caption':'legende','advert':'annonce',
           'table':'tableau','illustration':'illustration','separator':'separator','other':'other'}
    boxes=[Box(tuple(tuple(p) for p in polygon(b['bbox'])),types[b['type']],1.) for b in olr['blocks']]
    # Ces mesures Axel n'utilisent jamais des régions de référence en entrée
    # du système : seulement ici, au moment de la notation des sorties figées.
    supplemental=score_page(gt,OlrOutput(boxes,[b['article_id'] for b in olr['blocks']]))
    lines=gt.lines()
    def bbox(poly):
        return [min(p[0] for p in poly),min(p[1] for p in poly),
                max(p[0] for p in poly),max(p[1] for p in poly)]
    detections=olr_detection([dict(id=b.id,type=b.type,bbox=bbox(b.polygon)) for b in gt.blocks]+
                            [dict(id=r.id,type='separator',bbox=bbox(r.polygon)) for r in gt.separators],
                            [dict(id=b['id'],type=types[b['type']],bbox=b['bbox'],uncertain=b['uncertain']) for b in olr['blocks']])
    matches=match_boxes([bbox(ln.polygon) for ln in lines],[a['bbox'] for a in annotations])
    p2g={annotations[p]['id']:r for r,p,_ in matches}
    declared=[lid for b in olr['blocks'] for lid in b['line_ids']]
    sequence=[p2g[lid] for lid in declared if lid in p2g]
    total=len(sequence)*(len(sequence)-1)//2
    inversions=sum(a>b for i,a in enumerate(sequence) for b in sequence[i+1:])
    articles={a['id']:a for a in olr['articles']}
    pred_articles={lines[p2g[lid]].id if lid in p2g else 'unmatched_production:'+lid:b['article_id']
                   for b in olr['blocks'] for lid in b['line_ids']
                   if not b['uncertain'] and b['article_id'] is not None and not articles[b['article_id']]['uncertain']}
    gt_articles={ln.id:ln.article for ln in lines if ln.article}
    strict=dict(line_detection_coverage=len(matches)/len(lines) if lines else 0,
                matched_lines=len(matches),reference_lines=len(lines),inversions=inversions,
                line_kendall=1-2*inversions/total if total else None,
                articles_pairwise=article_pairwise(gt_articles,pred_articles),
                article_line_coverage=sum(lid in pred_articles for lid in gt_articles)/len(gt_articles) if gt_articles else 0,
                unresolved_blocks=sum(b['uncertain'] for b in olr['blocks']))
    strict['layout']=detections
    return dict(strict=strict,axel_supplemental=supplemental,
                note='Axel line order within one block is diagnostic; strict order uses only predicted line IDs.')


def evaluate(manifest,outputs,split,axel,reference_dpi=None):
    manifest=json.loads(Path(manifest).read_text());results=[]
    for row in manifest['pages']:
        if row['split'] != split:
            continue
        record={k:row[k] for k in ('id','family','split')}
        out=Path(outputs)/row['id']
        for key in ('image','reference'):
            if hashlib.sha256(Path(row[key]).read_bytes()).hexdigest() != row[key+'_sha256']:
                raise ValueError('Données modifiées : '+row[key])
        if not (out/'annotations.json').exists():
            record.update(status='missing_production_output',criteria_met=False)
            results.append(record);continue
        annotations=json.loads((out/'annotations.json').read_text())
        metrics=score(load_reference(row['reference'],dpi=reference_dpi),exported_annotations(annotations,out))
        metrics['human_text_reference']=row['human_text']
        if not row['human_text']:
            metrics['text_status']='diagnostic_only_nonhuman_reference'
        if row['olr_gold'] and (out/'olr.json').exists():
            metrics['olr']=score_olr(row['reference'],annotations,json.loads((out/'olr.json').read_text()),axel)
        else:
            metrics['olr_status']='missing_output' if row['olr_gold'] else 'no_typed_article_reference'
        (out/'independent-scores.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2,allow_nan=False))
        record.update(status='measured',criteria_met=False,
                      cer_convention=metrics['text']['convention_v1']['cer'] if row['human_text'] else None,
                      coverage=metrics['text']['convention_v1']['coverage'],
                      word_coverage=metrics['geometry']['coverage'],
                      missing_checks=['complete_word_geometry_reference_and_extreme_errors','all_OLR_types_and_articles','whole_suite_thresholds'])
        results.append(record)
    report=dict(split=split,pages=len(results),measured=sum(r['status']=='measured' for r in results),
                missing=sum(r['status']!='measured' for r in results),rows=results,
                criteria_met=False,protocol_sha256=manifest['protocol_sha256'])
    return report


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('manifest');ap.add_argument('outputs');ap.add_argument('report')
    ap.add_argument('--split',choices=('dev','reserved'),required=True);ap.add_argument('--axel',default=str(Path.home()/'axel'))
    ap.add_argument('--reference-dpi',type=float,help='Documented source DPI for physical ALTO units, never fit from word boxes')
    args=ap.parse_args();report=evaluate(args.manifest,args.outputs,args.split,args.axel,args.reference_dpi)
    Path(args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(dict(pages=report['pages'],measured=report['measured'],missing=report['missing'],criteria_met=False)))
