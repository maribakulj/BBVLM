#!/usr/bin/env python
"""Inscrit la structure de la passe OLR (blocs, types, articles, ordre de lecture)
dans un ALTO déjà placé. Aucun mot ni aucune coordonnée de mot n'est modifié :
les TextLine sont seulement regroupées dans les TextBlock des blocs OLR.

Entrées : page.alto.xml (placement), olr-ancre.json (page_olr_gemini.anchor_blocks).
Une ligne couverte par plusieurs blocs va au premier dans l'ordre de lecture ;
une ligne qu'aucun bloc ne couvre va dans un bloc « non_attribue » (signalé).
"""
import argparse
import copy
import json
from pathlib import Path

from lxml import etree

NS = 'http://www.loc.gov/standards/alto/ns-v4#'
Q = lambda tag: f'{{{NS}}}{tag}'


def box(elements):
    xs = [(float(e.get('HPOS')), float(e.get('VPOS')), float(e.get('HPOS'))+float(e.get('WIDTH')),
           float(e.get('VPOS'))+float(e.get('HEIGHT'))) for e in elements]
    x0, y0 = min(b[0] for b in xs), min(b[1] for b in xs)
    x1, y1 = max(b[2] for b in xs), max(b[3] for b in xs)
    return dict(HPOS=str(int(x0)), VPOS=str(int(y0)), WIDTH=str(int(x1-x0)), HEIGHT=str(int(y1-y0)))


def apply(alto_path, olr_path, output):
    tree = etree.parse(str(alto_path))
    root = tree.getroot()
    blocs = json.loads(Path(olr_path).read_text())
    lines = {l.get('ID'): l for l in root.iter(Q('TextLine'))}
    # rattacher chaque ligne au premier bloc OLR (ordre de lecture) qui la cite ;
    # une ligne coupée (L0012_G1, L0823_S1) suit sa ligne d'origine
    owner = {}
    for bloc in sorted((b for b in blocs if b.get('status') == 'ancre'), key=lambda b: b['n']):
        for lid in bloc.get('lines', []):
            for candidate in [lid] + [k for k in lines if k.startswith(lid + '_')]:
                owner.setdefault(candidate, bloc['n'])
    print_space = root.find(f'.//{Q("PrintSpace")}')
    old_blocks = list(print_space.findall(Q('TextBlock')))
    for block in old_blocks:
        print_space.remove(block)
    groups = {}
    orphans = []
    for lid, line in lines.items():
        (groups.setdefault(owner[lid], []) if lid in owner else orphans).append(line)
    # étiquettes : types et articles
    tags = root.find(Q('Tags'))
    if tags is None:
        tags = etree.SubElement(root, Q('Tags'))
        root.insert(1, tags)
    for child in list(tags):
        tags.remove(child)
    types = sorted({b['type'] for b in blocs if b.get('status') == 'ancre'} | {'non_attribue'})
    for t in types:
        etree.SubElement(tags, Q('LayoutTag'), ID=f'TYPE_{t}', LABEL=t)
    articles = sorted({b['article'] for b in blocs if b.get('status') == 'ancre'})
    for a in articles:
        etree.SubElement(tags, Q('StructureTag'), ID=f'ART_{a}', TYPE='article', LABEL=f'article {a}')
    by_n = {b['n']: b for b in blocs}
    order = []
    for n in sorted(groups):
        members = sorted(groups[n], key=lambda l: (float(l.get('VPOS')), float(l.get('HPOS'))))
        bloc = by_n[n]
        element = etree.SubElement(print_space, Q('TextBlock'), ID=f'OLR_B{n:04d}',
                                   TAGREFS=f"TYPE_{bloc['type']} ART_{bloc['article']}", **box(members))
        for line in members:
            element.append(line)
        order.append(element.get('ID'))
    if orphans:
        element = etree.SubElement(print_space, Q('TextBlock'), ID='OLR_NON_ATTRIBUE', TAGREFS='TYPE_non_attribue',
                                   **box(orphans))
        for line in sorted(orphans, key=lambda l: (float(l.get('VPOS')), float(l.get('HPOS')))):
            element.append(line)
    reading = root.find(Q('ReadingOrder'))
    if reading is not None:
        root.remove(reading)
    reading = etree.Element(Q('ReadingOrder'))
    group = etree.SubElement(reading, Q('OrderedGroup'), ID='RO_OLR')
    for k, ref in enumerate(order, 1):
        etree.SubElement(group, Q('ElementRef'), ID=f'ROREF_{k}', REF=ref)
    root.insert(list(root).index(tags) + 1, reading)
    description = root.find(f'.//{Q("processingStepDescription")}')
    if description is not None:
        description.text = ('Mots placés par alignement CTC du texte Gemini (lecture par région). Blocs, types, '
                            'articles et ordre de lecture : passe OLR Gemini, blocs ancrés par leurs premiers '
                            'mots dans le texte, géométrie déduite des lignes alignées. Non certifié.')
    tree.write(str(output), xml_declaration=True, encoding='UTF-8', pretty_print=True)
    words_before = sum(1 for _ in etree.parse(str(alto_path)).getroot().iter(Q('String')))
    words_after = sum(1 for _ in root.iter(Q('String')))
    return dict(blocs_olr=len(groups), articles=len(articles), lignes=len(lines), lignes_non_attribuees=len(orphans),
                mots_avant=words_before, mots_apres=words_after)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('alto'); parser.add_argument('olr'); parser.add_argument('output')
    args = parser.parse_args()
    print(json.dumps(apply(args.alto, args.olr, args.output), ensure_ascii=False))
