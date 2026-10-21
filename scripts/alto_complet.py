#!/usr/bin/env python
"""ALTO complet : ne rien jeter de ce que Gemini a lu.

Les lignes que le contrôle géométrique refuse (frontière de mots sans blanc,
mot sans encre, alignement forcé impossible) disparaissent de page.alto.xml
alors que leur texte Gemini est juste. Ce script écrit, À CÔTÉ, un
page.complet.alto.xml où chaque ligne refusée est remise dans son bloc :
- boîte de ligne : celle de la ligne détectée (exacte) ;
- boîtes de mots : celles calculées par l'alignement quand elles existent et
  correspondent mot à mot au texte, sinon une estimation proportionnelle au
  nombre de caractères dans la boîte de la ligne ;
- WC (confiance du mot, ALTO) = 0.3 pour toute boîte de ce type, et l'ID de la
  ligne finit par « _EST » : l'utilisateur sait où les boîtes sont approchées.
Le texte n'est jamais modifié ; page.alto.xml n'est pas touché.
"""
import argparse
import json
from pathlib import Path

from lxml import etree

NS = 'http://www.loc.gov/standards/alto/ns-v4#'
Q = lambda tag: f'{{{NS}}}{tag}'
ESTIMATED_WC = '0.3'


def word_boxes(annotation):
    """[(texte, x0, y0, x1, y1)] : boîtes calculées si elles couvrent le texte mot à mot, sinon estimées."""
    tokens = annotation['source_text'].split()
    words = annotation.get('words') if isinstance(annotation.get('words'), list) else []
    if words and [w.get('text') for w in words] == tokens:
        return [(w['text'], w['x0'], w['y0'], w['x1'], w['y1']) for w in words], 'alignement'
    x0, y0, x1, y1 = annotation['bbox']
    total = sum(len(t) for t in tokens) + max(0, len(tokens) - 1)
    out, pos = [], 0
    for t in tokens:
        a = x0 + (x1 - x0) * pos / max(1, total)
        b = x0 + (x1 - x0) * (pos + len(t)) / max(1, total)
        out.append((t, int(a), y0, max(int(a) + 1, int(b) - 1), y1 - 1))
        pos += len(t) + 1
    return out, 'proportionnelle'


def line_element(annotation):
    x0, y0, x1, y1 = annotation['bbox']
    line = etree.Element(Q('TextLine'), ID=annotation['id'] + '_EST', HPOS=str(x0), VPOS=str(y0),
                         WIDTH=str(x1 - x0), HEIGHT=str(y1 - y0))
    if annotation.get('baseline'):
        line.set('BASELINE', ' '.join(f'{x:.3f},{y:.3f}' for x, y in annotation['baseline']))
    boxes, method = word_boxes(annotation)
    for k, (text, a, b, c, d) in enumerate(boxes, 1):
        if k > 1:
            prev = boxes[k - 2]
            etree.SubElement(line, Q('SP'), HPOS=str(prev[3] + 1), VPOS=str(b), WIDTH=str(max(0, a - prev[3] - 1)))
        etree.SubElement(line, Q('String'), ID=f"{annotation['id']}_EST_W{k:02d}", CONTENT=text, HPOS=str(a),
                         VPOS=str(b), WIDTH=str(c - a + 1), HEIGHT=str(d - b + 1), WC=ESTIMATED_WC)
    return line, method, len(boxes)


def complete(inspection, output=None):
    inspection = Path(inspection)
    annotations = json.loads((inspection / 'annotations.json').read_text())
    tree = etree.parse(str(inspection / 'page.alto.xml'))
    root = tree.getroot()
    blocks = {b.get('ID'): b for b in root.iter(Q('TextBlock'))}
    space = next(root.iter(Q('PrintSpace')))
    order = next(root.iter(Q('OrderedGroup')), None)
    present = {l.get('ID') for l in root.iter(Q('TextLine'))}
    report = dict(lignes_ajoutees=0, mots_ajoutes=0, boites=dict(alignement=0, proportionnelle=0), par_statut={},
                  ecartees_doublon=0)
    kept = [a['bbox'] for a in annotations if a.get('alto_eligible')]

    def inter(p, q):
        return max(0, min(p[2], q[2]) - max(p[0], q[0])) * max(0, min(p[3], q[3]) - max(p[1], q[1]))
    for a in annotations:
        if not (a.get('source_text') or '').strip() or a.get('alto_eligible') or a['id'] in present:
            continue
        # Ligne qui recouvre une ligne déjà placée (même ligne détectée deux fois,
        # entière et en cellules) : la remettre doublerait du texte.
        area = max(1, (a['bbox'][2] - a['bbox'][0]) * (a['bbox'][3] - a['bbox'][1]))
        if any(inter(a['bbox'], k) > .1 * area for k in kept):
            report['ecartees_doublon'] += 1
            continue
        kept.append(a['bbox'])
        line, method, n = line_element(a)
        bid = 'B_' + (a.get('block_id') or 'SANS_BLOC')
        block = blocks.get(bid)
        if block is None:
            x0, y0, x1, y1 = a['bbox']
            block = etree.SubElement(space, Q('TextBlock'), ID=bid, HPOS=str(x0), VPOS=str(y0),
                                     WIDTH=str(x1 - x0), HEIGHT=str(y1 - y0))
            blocks[bid] = block
            if order is not None:
                etree.SubElement(order, Q('ElementRef'), ID='ROREF_' + bid, REF=bid)
        # ligne insérée à sa place verticale dans le bloc
        lines = list(block.iter(Q('TextLine')))
        after = [l for l in lines if int(l.get('VPOS')) <= a['bbox'][1]]
        (after[-1].addnext(line) if after else block.append(line))
        # le bloc englobe ses lignes
        bx0, by0 = min(int(block.get('HPOS')), a['bbox'][0]), min(int(block.get('VPOS')), a['bbox'][1])
        bx1 = max(int(block.get('HPOS')) + int(block.get('WIDTH')), a['bbox'][2])
        by1 = max(int(block.get('VPOS')) + int(block.get('HEIGHT')), a['bbox'][3])
        block.set('HPOS', str(bx0)); block.set('VPOS', str(by0))
        block.set('WIDTH', str(bx1 - bx0)); block.set('HEIGHT', str(by1 - by0))
        report['lignes_ajoutees'] += 1; report['mots_ajoutes'] += n; report['boites'][method] += 1
        report['par_statut'][a['status']] = report['par_statut'].get(a['status'], 0) + 1
    output = Path(output) if output else inspection / 'page.complet.alto.xml'
    tree.write(str(output), xml_declaration=True, encoding='UTF-8', pretty_print=True)
    report['alto'] = str(output)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inspection', help='dossier inspection(-refined) : annotations.json + page.alto.xml')
    parser.add_argument('--output')
    args = parser.parse_args()
    print(json.dumps(complete(args.inspection, args.output), ensure_ascii=False, indent=1))
