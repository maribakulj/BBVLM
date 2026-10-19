#!/usr/bin/env python
"""Diagnostic CER par région ; géométrie de référence réservée à l'évaluation.

Ce score spatial complète le CER page entière sans le remplacer : il retire
les permutations entre régions mais pénalise omissions et ajouts dans chacune.
"""
import argparse
import json
from pathlib import Path
import sys

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from evaluation import hipe_ocrepair_2026, lev, _points
from page_reference_text import load_page_reference
from page_text_evaluation import markdown_text
from page_anchors import save_json, sha256


def geometric_order(lines):
    """Regrouper les cellules d'une même rangée malgré le décalage des boîtes."""
    rows = []
    for line in sorted(lines, key=lambda r: ((r['bbox'][1]+r['bbox'][3])/2, r['bbox'][0])):
        box = line['bbox']
        if rows:
            previous = rows[-1][0]['bbox']
            overlap = max(0, min(previous[3], box[3])-max(previous[1], box[1]))
            same_row = overlap >= .5*min(previous[3]-previous[1], box[3]-box[1])
        else:
            same_row = False
        if same_row:
            rows[-1].append(line)
        else:
            rows.append([line])
    return [line for row in rows for line in sorted(row, key=lambda r: r['bbox'][0])]


def evaluate(manifest_path, directory, baseline=None):
    directory = Path(directory)
    regions = json.loads((directory / 'regions.json').read_text())
    matches = [p for p in json.loads(Path(manifest_path).read_text())['pages']
               if p['image_sha256'] == regions['image_sha256']]
    if len(matches) != 1:
        raise ValueError('Référence indépendante unique requise')
    page = matches[0]
    if sha256(page['reference']) != page['reference_sha256']:
        raise ValueError('Référence modifiée')
    rows, audit = load_page_reference(page['reference'])
    root = etree.parse(page['reference'])
    coords = {el.get('id'): _points(el) for el in root.findall('.//{*}TextLine')}
    grouped = {r['id']: [] for r in regions['regions']}
    unassigned = []
    for row in rows:
        box = coords.get(row['id'])
        if box is None:
            unassigned.append(row)
            continue
        x = (box[0]+box[2])/2
        y = (box[1]+box[3])/2
        candidates = [r for r in regions['regions'] if r['bbox'][0] <= x < r['bbox'][2]
                      and r['bbox'][1] <= y < r['bbox'][3]]
        if len(candidates) != 1:
            unassigned.append(row)
        else:
            grouped[candidates[0]['id']].append({**row, 'bbox': box})
    scores = []
    spatial_reference = []
    for r in regions['regions']:
        reference = geometric_order(grouped[r['id']])
        spatial_reference.extend(reference)
        path = directory / r['id'] / 'vt.gemini.md'
        if not path.exists():
            continue
        metadata = json.loads(path.with_name('vt-provenance.json').read_text())
        if metadata['artifact_sha256'] != sha256(path) or metadata['image_sha256'] != r['image_sha256']:
            raise ValueError('Transcription de région modifiée')
        ref = hipe_ocrepair_2026('\n'.join(row['text'] for row in reference))
        text, _ = markdown_text(path.read_text())
        hyp = hipe_ocrepair_2026(text)
        errors = lev(ref, hyp)
        from rapidfuzz.distance import Levenshtein
        operations = Levenshtein.editops(ref, hyp)
        # Diagnostic des opérations seulement ; ne pas qualifier une édition
        # de faute Gemini sans vérification visuelle de la référence.
        space_insertions = sum(op.tag == 'insert' and hyp[op.dest_pos] == ' ' for op in operations)
        space_deletions = sum(op.tag == 'delete' and ref[op.src_pos] == ' ' for op in operations)
        scores.append(dict(id=r['id'], errors=errors, reference_characters=len(ref),
                           prediction_characters=len(hyp), cer=errors/len(ref) if ref else None,
                           space_insertions=space_insertions, space_deletions=space_deletions,
                           reference_lines=len(reference), markdown_sha256=sha256(path)))
    denominator = sum(r['reference_characters'] for r in scores)
    report = dict(metric='HIPE_normalized_CER_separate_source_regions_geometric_line_order',
                  status='diagnostic_not_whole_page_CER', regions=scores,
                  completed=len(scores), total=len(regions['regions']),
                  errors=sum(r['errors'] for r in scores), reference_characters=denominator,
                  cer=sum(r['errors'] for r in scores)/denominator if denominator else None,
                  unassigned_reference_lines=[r['id'] for r in unassigned],
                  reference_sha256=page['reference_sha256'], reference_audit=audit,
                  reference_order='vertical_rows_with_at_least_half_height_overlap_then_left_to_right',
                  caveat='Reference line order inside tables may differ from transcription serialization')
    report['regions_without_reference_text']=[dict(id=r['id'],prediction_characters=r['prediction_characters'])
                                              for r in scores if not r['reference_characters'] and r['prediction_characters']]
    covered=[r for r in scores if r['reference_characters']]
    covered_denominator=sum(r['reference_characters'] for r in covered)
    report['conditional_regions_with_reference']=dict(
        status='conditional_diagnostic_not_whole_page_CER',regions=[r['id'] for r in covered],
        errors=sum(r['errors'] for r in covered),reference_characters=covered_denominator,
        cer=sum(r['errors'] for r in covered)/covered_denominator if covered_denominator else None)
    if not unassigned and len(scores) == len(regions['regions']) and (directory / 'vt.gemini.md').exists():
        # Même ordre spatial, établi une fois et appliqué aux deux sorties.
        # Aucun mot ni aucune ligne de référence n'est retiré ou corrigé.
        assert len(spatial_reference) == len(rows)
        ref = hipe_ocrepair_2026('\n'.join(row['text'] for row in spatial_reference))
        comparison = {}
        inputs = {'regions': directory / 'vt.gemini.md'}
        if baseline is not None:
            inputs['whole_page_baseline'] = Path(baseline) / 'vt.gemini.md'
        for name, path in inputs.items():
            metadata = json.loads(path.with_name('vt-provenance.json').read_text())
            if metadata['image_sha256'] != regions['image_sha256'] or metadata['artifact_sha256'] != sha256(path):
                raise ValueError('Comparaison entre sources incompatibles')
            text, _ = markdown_text(path.read_text())
            hyp = hipe_ocrepair_2026(text)
            errors = lev(ref, hyp)
            comparison[name] = dict(errors=errors, reference_characters=len(ref),
                                     prediction_characters=len(hyp), cer=errors/len(ref),
                                     markdown_sha256=sha256(path))
        report['whole_page_same_spatial_reference_order'] = comparison
    save_json(directory / 'cer-regions-diagnostic.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest')
    parser.add_argument('directory')
    parser.add_argument('--baseline')
    args = parser.parse_args()
    report = evaluate(args.manifest, args.directory, args.baseline)
    print(json.dumps({k: v for k, v in report.items() if k not in ('reference_audit',)}, ensure_ascii=False, indent=2))
