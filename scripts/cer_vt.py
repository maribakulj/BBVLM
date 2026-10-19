#!/usr/bin/env python
"""CER « vérité terrain » (normalisation cer_vt : profil HIPE/ICDAR + s long, ligatures).

Trois mesures, toutes avec omissions et ajouts comptés :
- ``page_xml_order`` : page entière, référence dans l'ordre du XML ;
- ``page_spatial_order`` : page entière, référence rangée région par région (plan
  automatique de la transcription) puis par rangées géométriques — même ordre que
  la transcription régionale ;
- ``regions`` : détail par région (texte de la région d'après les offsets ``parts``).
La référence ne sert qu'ici ; elle n'entre dans aucune étape de production.
"""
import argparse
import json
from pathlib import Path
import sys

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'scripts'))
from evaluation import cer_vt, lev, _points
from page_reference_text import load_page_reference
from page_text_evaluation import markdown_text
from page_anchors import save_json, sha256
from evaluer_regions import geometric_order


def counts(ref, hyp):
    from rapidfuzz.distance import Levenshtein
    ops = Levenshtein.editops(ref, hyp)
    return dict(errors=len(ops), reference_characters=len(ref), prediction_characters=len(hyp),
                cer=len(ops) / len(ref) if ref else None,
                substitutions=sum(o.tag == 'replace' for o in ops),
                deletions=sum(o.tag == 'delete' for o in ops),
                insertions=sum(o.tag == 'insert' for o in ops))


def evaluate(manifest, transcription, regions_json):
    transcription = Path(transcription)
    provenance = json.loads((transcription / 'vt-provenance.json').read_text())
    markdown = (transcription / 'vt.gemini.md').read_text()
    if sha256(transcription / 'vt.gemini.md') != provenance['artifact_sha256']:
        raise ValueError('Transcription modifiée')
    page = [p for p in json.loads(Path(manifest).read_text())['pages']
            if p['image_sha256'] == provenance['image_sha256']]
    if len(page) != 1:
        raise ValueError('Référence unique requise')
    page = page[0]
    if sha256(page['reference']) != page['reference_sha256']:
        raise ValueError('Référence modifiée')
    rows, _ = load_page_reference(page['reference'])
    coords = {el.get('id'): _points(el) for el in etree.parse(page['reference']).findall('.//{*}TextLine')}
    regions = json.loads(Path(regions_json).read_text())['regions']
    grouped = {r['id']: [] for r in regions}
    orphan = []
    for row in rows:
        box = coords.get(row['id'])
        if box is None:
            orphan.append(row); continue
        x, y = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        inside = [r for r in regions if r['bbox'][0] <= x < r['bbox'][2] and r['bbox'][1] <= y < r['bbox'][3]]
        if not inside:  # au plus près
            inside = [min(regions, key=lambda r: abs(x - (r['bbox'][0] + r['bbox'][2]) / 2)
                          + abs(y - (r['bbox'][1] + r['bbox'][3]) / 2))]
        grouped[inside[0]['id']].append({**row, 'bbox': box})
    parts = {p['id']: p['span'] for p in provenance.get('parts', [])}
    report = dict(metric='cer_vt = HIPE-OCRepair norm() + NFKC + s long ; accents conservés ; '
                         'casse, ponctuation, apostrophes ignorées',
                  page_id=page['id'], markdown_sha256=provenance['artifact_sha256'], regions=[])
    spatial_ref, spatial_hyp = [], []
    for region in regions:
        ref_text = '\n'.join(r['text'] for r in geometric_order(grouped[region['id']]))
        span = parts.get(region['id'])
        hyp_text = markdown_text(markdown[span[0]:span[1]])[0] if span else ''
        spatial_ref.append(ref_text); spatial_hyp.append(hyp_text)
        report['regions'].append(dict(id=region['id'], **counts(cer_vt(ref_text), cer_vt(hyp_text))))
    whole, _ = markdown_text(markdown)
    report['page_xml_order'] = counts(cer_vt('\n'.join(r['text'] for r in rows)), cer_vt(whole))
    report['page_spatial_order'] = counts(cer_vt('\n'.join(spatial_ref)), cer_vt('\n'.join(spatial_hyp)))
    report['page_line_matching'] = line_matching([r['text'] for r in rows], whole)
    report['page_bag_of_words'] = bag_of_words('\n'.join(r['text'] for r in rows), whole)
    report['reference_lines_without_coordinates'] = len(orphan)
    return report


def bag_of_words(reference, hypothesis):
    """Mots (normalisation cer_vt) comptés en multiensemble : indépendant de l'ordre
    ET du découpage en lignes (tableaux transcrits en rangées longues ou par colonne)."""
    from collections import Counter
    ref, hyp = Counter(cer_vt(reference).split()), Counter(cer_vt(hypothesis).split())
    common = sum((ref & hyp).values())
    total_r, total_h = sum(ref.values()), sum(hyp.values())
    return dict(reference_words=total_r, hypothesis_words=total_h, common_words=common,
                recall=common/total_r if total_r else None, precision=common/total_h if total_h else None)


def line_matching(reference_lines, hypothesis_text):
    """CER indépendant de l'ordre (esprit Flexible Character Accuracy) : chaque
    ligne de référence est appariée à au plus une ligne de la transcription
    (affectation optimale sur la distance d'édition normalisée cer_vt) ; une
    ligne sans partenaire compte entièrement comme omission ou ajout. Les
    lignes coupées par une césure sont comparées telles quelles."""
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    from rapidfuzz.distance import Levenshtein
    from rapidfuzz.process import cdist
    ref = [x for x in (cer_vt(t) for t in reference_lines) if x]
    hyp = [x for x in (cer_vt(t) for t in hypothesis_text.splitlines()) if x]
    if not ref:
        return None
    dist = cdist(ref, hyp, scorer=Levenshtein.distance, workers=-1).astype(float)
    total = np.array([[len(a)+len(b) for b in hyp] for a in ref], dtype=float)
    # coût d'un appariement face au coût de laisser les deux lignes seules
    gain = total - dist
    rows, cols = linear_sum_assignment(-gain)
    errors, matched_h = 0, set()
    matched_r = set()
    for i, j in zip(rows, cols):
        # apparier seulement des lignes qui se ressemblent vraiment (<= 50 % d'écart)
        if gain[i, j] > 0 and dist[i, j] <= .5*max(len(ref[i]), len(hyp[j])):
            errors += int(dist[i, j]); matched_r.add(i); matched_h.add(j)
    deletions = sum(len(ref[i]) for i in range(len(ref)) if i not in matched_r)
    insertions = sum(len(hyp[j]) for j in range(len(hyp)) if j not in matched_h)
    chars = sum(len(x) for x in ref)
    return dict(errors=errors+deletions+insertions, reference_characters=chars,
                cer=(errors+deletions+insertions)/chars, matched_line_errors=errors,
                # côté VT : ce que la VT contient et que la transcription rate ou lit mal ;
                # le texte lu EN PLUS (absent de la VT) est compté à part, à vérifier à l'image
                cer_reference_side=(errors+deletions)/chars,
                unmatched_reference_characters=deletions, unmatched_hypothesis_characters=insertions,
                reference_lines=len(ref), hypothesis_lines=len(hyp))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest'); parser.add_argument('transcription'); parser.add_argument('regions_json')
    parser.add_argument('--output')
    args = parser.parse_args()
    report = evaluate(args.manifest, args.transcription, args.regions_json)
    if args.output:
        save_json(Path(args.output), report)
    print(json.dumps({k: report[k] for k in ('page_xml_order', 'page_spatial_order', 'page_line_matching',
                                             'page_bag_of_words')},
                     ensure_ascii=False, indent=1))
