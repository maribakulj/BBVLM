"""Export de preuves de collisions, distinct des sorties d'entraînement.

Les enveloppes et transcriptions observées ne sont jamais réparées ici. L'ALTO
peut satisfaire le XSD tout en échouant au validateur de production : les deux
résultats sont conservés. Les masques restent des observations, pas des glyphes
certifiés. Aucun seuil d'acceptation ni statut d'annotation n'est modifié.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import html
import json
from pathlib import Path
import shutil

import cv2
from lxml import etree
import numpy as np

import alto
import ink
from page_collision_audit import collision_pairs, support_kind
from page_line_ink_v2 import PolygonBaselineInkV2


VERSION = 'collision-envelope-diagnostic-export-v1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def schema_check(xml, schema_path=None):
    """Vérifie le contrat XSD local, sans remplacer alto.validate."""
    path = Path(schema_path) if schema_path else Path(alto.__file__).resolve().parents[1]/'schemas/alto-4-4.xsd'

    class Local(etree.Resolver):
        def resolve(self, url, public, context):
            local = path.parent/Path(url).name
            if local.exists():
                return self.resolve_filename(str(local), context)

    parser = etree.XMLParser(no_network=True)
    parser.resolvers.add(Local())
    schema = etree.XMLSchema(etree.parse(str(path), parser))
    valid = schema.validate(etree.fromstring(xml))
    return dict(valid=valid, error=None if valid else str(schema.error_log.last_error),
                schema=str(path), schema_sha256=sha(path))


def schema_shape_contract():
    """Lit les déclarations du XSD utilisé, sans extrapoler aux lecteurs."""
    path = Path(alto.__file__).resolve().parents[1]/'schemas/alto-4-4.xsd'
    tree = etree.parse(str(path))
    ns = {'x': 'http://www.w3.org/2001/XMLSchema'}
    shape = tree.xpath('//x:complexType[@name="StringType"]/x:sequence/x:element[@name="Shape"]', namespaces=ns)[0]
    choices = tree.xpath('//x:complexType[@name="ShapeType"]/x:choice/x:element/@name', namespaces=ns)
    return dict(string_shape_min_occurs=int(shape.get('minOccurs', '1')),
                string_shape_max_occurs=int(shape.get('maxOccurs', '1')),
                alternatives=choices, multipolygon_declared='MultiPolygon' in choices,
                reader_polygon_support_tested=False, shapes_added_to_observed_words=False,
                source=str(path), sha256=sha(path))


def diagnostic_alto(annotations, width, height, source_name):
    """Conserve chaque mot existant, même si sa ligne est refusée en production."""
    blocks = []
    for annotation in annotations:
        words = annotation.get('words') or []
        if not words:
            continue
        box = [min(w['x0'] for w in words), min(w['y0'] for w in words),
               max(w['x1'] for w in words), max(w['y1'] for w in words)]
        # Les conteneurs du diagnostic sont les unions des mots inchangés ;
        # les boîtes de détection originales restent dans annotations.snapshot.json.
        line = dict(id=annotation['id'], bbox=box, words=words,
                    baseline=annotation.get('baseline'))
        blocks.append(dict(id='DIAG_'+annotation['id'], x0=box[0], y0=box[1],
                           x1=box[2], y1=box[3], lines=[line]))
    xml = alto.build(width, height, source_name, blocks, VERSION,
                     'DIAGNOSTIC ONLY; unchanged observed word envelopes; not training data; '
                     'reading and glyph extent are not certified; production rejection remains in force.')
    tree = etree.fromstring(xml)
    tags = etree.Element('{%s}Tags' % alto.NS)
    tag = etree.SubElement(tags, '{%s}OtherTag' % alto.NS, ID='DIAGNOSTIC_UNCERTIFIED',
                          TYPE='quality_status', LABEL='diagnostic_only_not_training')
    tree.insert(1, tags)
    expected = {}
    for annotation in annotations:
        for wi, word in enumerate(annotation.get('words') or [], 1):
            expected[f"{annotation['id']}_W{wi:02d}"] = word
    for element in tree.findall('.//{%s}String' % alto.NS):
        element.set('TAGREFS', tag.get('ID'))
        word = expected[element.get('ID')]
        if (element.get('CONTENT') != word['text'] or
            tuple(float(element.get(k)) for k in ('HPOS', 'VPOS', 'WIDTH', 'HEIGHT')) !=
            (word['x0'], word['y0'], word['x1']-word['x0']+1, word['y1']-word['y0']+1)):
            raise ValueError('Un mot a changé dans le diagnostic ALTO')
    return etree.tostring(tree, encoding='UTF-8', xml_declaration=True, pretty_print=True)


def pair_claim(pair, profiles):
    """Décrit séparément blanc brut, masques et attribution des mots entiers."""
    own_only = []
    for key in pair['word_profiles']:
        causes = profiles[key]['pixel_causes']
        own_only.append(bool(causes.get('proved_own_ink')) and set(causes) == {'proved_own_ink'})
    return dict(
        observed_support=pair['support_kind'],
        raw_intersection_has_no_dark_pixel_at_160=pair['raw_dark_pixels'] == 0,
        whole_word_masks_only_proved_own_ink=own_only,
        foreign_ink_in_either_word=any(pair['foreign_ink_anywhere_in_words']),
        glyph_overlap_certified=False,
        glyph_completeness_certified=False,
        acceptance_changed=False)


def _gallery(rows, summary):
    labels = dict(shared_mask_pixels='Pixels de masque partagés', disjoint_mask_pixels='Deux masques disjoints',
                  one_sided_mask_pixels='Encre d’un seul masque', no_mask_pixels='Aucun pixel des deux masques')
    cards = []
    for row in rows:
        kind = row['support_kind']
        claimed = row['diagnostic_claim']
        label = labels[kind]
        words = ' / '.join(row['texts'])
        flags = []
        if claimed['raw_intersection_has_no_dark_pixel_at_160']:
            flags.append('Aucun pixel gris < 160 dans l’intersection')
        if all(claimed['whole_word_masks_only_proved_own_ink']):
            flags.append('Les deux masques de mots entiers sont attribués à leurs lignes respectives')
        if claimed['foreign_ink_in_either_word']:
            flags.append('Encre étrangère présente ailleurs dans un des mots')
        cards.append(f'<article data-kind="{kind}" data-text="{html.escape(words.lower(), quote=True)}">'
            f'<h2>#{row["index"]} · {html.escape(words)}</h2>'
            f'<p>{row["line_a"]} / {row["line_b"]} · {label} · '
            f'{row["common_mask_pixels"]} pixels partagés · intersection {row["intersection_size"][0]} × {row["intersection_size"][1]} px</p>'
            f'<p>{html.escape(" ; ".join(flags))}</p>'
            '<div class="pictures">'+''.join(
                f'<figure><img loading="lazy" src="{row[key]}" alt="{caption}"><figcaption>{caption}</figcaption></figure>'
                for key, caption in [('source_crop', 'Pixels source, échelle native'),
                                     ('box_overlay', 'Boîtes existantes : A rouge, B bleu'),
                                     ('support_overlay', 'Masques : A rouge, B bleu, partage magenta')])+'</div></article>')
    options = '<option value="">Toutes les paires</option>'+''.join(f'<option value="{k}">{v}</option>' for k, v in labels.items())
    return ('<!doctype html><html lang="fr"><meta charset="utf-8"><title>Diagnostic des collisions</title>'
            '<style>body{font:16px system-ui;margin:24px;background:#faf9f6;color:#222}header{position:sticky;top:0;background:#faf9f6;padding:12px 0;border-bottom:1px solid #999}h1{font-size:23px}h2{font-size:18px}article{border-bottom:1px solid #aaa;padding:18px 0}.pictures{display:flex;gap:20px;flex-wrap:wrap}figure{margin:0;max-width:100%;overflow:auto}img{image-rendering:pixelated}figcaption{font-size:13px}select,input{font:inherit;padding:5px}article[hidden]{display:none}</style>'
            '<header><h1>Diagnostic : enveloppes des mots et pixels d’encre</h1>'
            f'<p>{summary["word_pairs"]} paires, {summary["colliding_lines"]} lignes. Boîtes, textes et refus de production conservés. '
            'Aucune certification des glyphes ; aucun export d’entraînement.</p>'
            f'<label>Catégorie <select id="kind">{options}</select></label> '
            '<label>Mot <input id="query" type="search"></label> <span id="count"></span></header>'
            '<p>Un rectangle sans pixel commun aux deux masques n’est pas nécessairement blanc dans l’image. '
            'Un partage de masque est un conflit observé, pas une preuve que deux glyphes imprimés se chevauchent. '
            'Les attributions de composantes sont automatiques et restent examinables dans les JSON.</p>'
            +''.join(cards)+'<script>const k=document.getElementById("kind"),q=document.getElementById("query");'
            'function filter(){let n=0;document.querySelectorAll("article").forEach(a=>{a.hidden=!!((k.value&&a.dataset.kind!==k.value)||(q.value&&!a.dataset.text.includes(q.value.toLowerCase())));if(!a.hidden)n++;});document.getElementById("count").textContent=n+" paires affichées";}k.onchange=q.oninput=filter;filter();</script></html>')


def export_diagnostic(image, source, variant, audit, output):
    image, source, variant, audit, output = map(Path, (image, source, variant, audit, output))
    if output.exists() and any(output.iterdir()):
        raise ValueError('Le dossier de diagnostic doit être vide pour figer les preuves')
    provenance = json.loads((audit/'provenance.json').read_text())
    ann_path = variant/'candidate-annotations.json'
    if provenance['image_sha256'] != sha(image) or provenance['annotations_sha256'] != sha(ann_path):
        raise ValueError('Les entrées diffèrent de celles de l’audit')
    signature = json.loads((source/'geometry-cache/state.json').read_text())['signature']
    if signature['image_sha256'] != sha(image) or signature['implementation']['ink'] != sha(ink.__file__):
        raise ValueError('Les masques historiques ont changé')
    annotations = json.loads(ann_path.read_text())
    by_id = {a['id']: a for a in annotations}
    pairs = json.loads((audit/'word-pairs.json').read_text())
    profiles = json.loads((audit/'word-profiles.json').read_text())
    recomputed = collision_pairs(annotations)
    if [{k: p[k] for k in ('line_a', 'word_a', 'line_b', 'word_b', 'intersection')} for p in pairs] != recomputed:
        raise ValueError('L’inventaire de collisions ne correspond pas aux annotations')
    gray = cv2.imread(str(image), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise ValueError('Image illisible')
    height, width = gray.shape
    rows = json.loads((source/'segmentation.json').read_text())
    rows = [{k: v for k, v in row.items() if k in {'id', 'bbox', 'detector_bbox', 'source', 'baseline', 'polygon'}} for row in rows]
    native = PolygonBaselineInkV2(gray, rows)
    masks = {}
    for lid in {p[k] for p in pairs for k in ('line_a', 'line_b')}:
        a = by_id[lid]
        if (a.get('alignment') or {}).get('word_geometry', {}).get('version') != 'ctc-ink-whitespace-v4':
            raise ValueError('Masque historique non pris en charge')
        mask, ox, oy = ink.alignment_mask(gray, a['reading_bbox'], True, True, True)
        masks[lid] = (*native.filter_mask(lid, mask, ox, oy)[:1], ox, oy)
    output.mkdir(parents=True, exist_ok=True)
    (output/'pairs').mkdir()
    (output/'masks').mkdir()
    mask_manifest = {}
    for lid, (mask, ox, oy) in masks.items():
        name = 'masks/'+lid+'.png'
        cv2.imwrite(str(output/name), (mask > 0).astype(np.uint8)*255)
        mask_manifest[lid] = dict(path=name, origin=[ox, oy], shape=list(mask.shape), sha256=sha(output/name))
    xml = diagnostic_alto(annotations, width, height, image.name)
    (output/'diagnostic-observed-envelopes.alto.xml').write_bytes(xml)
    xsd = schema_check(xml)
    try:
        production = alto.validate(xml)
    except (ValueError, etree.DocumentInvalid) as exc:
        production = dict(valid=False, error=str(exc))
    shutil.copyfile(ann_path, output/'annotations.snapshot.json')
    for path in audit.glob('*.json'):
        shutil.copyfile(path, output/('audit-'+path.name))
    diagnostic_pairs = []
    for pair in pairs:
        words = [by_id[pair['line_'+side]]['words'][pair['word_'+side]] for side in ('a', 'b')]
        crop = [max(0, min(w['x0'] for w in words)-12), max(0, min(w['y0'] for w in words)-12),
                min(width, max(w['x1'] for w in words)+13), min(height, max(w['y1'] for w in words)+13)]
        x0, y0, x1, y1 = crop
        source_crop = gray[y0:y1, x0:x1]
        boxes = cv2.cvtColor(source_crop, cv2.COLOR_GRAY2BGR)
        support = cv2.cvtColor(source_crop, cv2.COLOR_GRAY2BGR)
        supports = []
        for side, word, color in zip(('a', 'b'), words, ((0, 0, 255), (255, 0, 0))):
            cv2.rectangle(boxes, (word['x0']-x0, word['y0']-y0), (word['x1']-x0, word['y1']-y0), color, 1)
            mask, ox, oy = masks[pair['line_'+side]]
            local = np.zeros(source_crop.shape, bool)
            a, b, c, d = word['x0'], word['y0'], word['x1']+1, word['y1']+1
            local[b-y0:d-y0, a-x0:c-x0] = mask[b-oy:d-oy, a-ox:c-ox] > 0
            supports.append(local)
        support[supports[0]] = (0, 0, 255)
        support[supports[1]] = (255, 0, 0)
        support[supports[0] & supports[1]] = (255, 0, 255)
        a, b, c, d = pair['intersection']
        kind, counts, shared = support_kind(*(s[b-y0:d-y0, a-x0:c-x0] for s in supports))
        if (kind, counts, shared) != (pair['support_kind'], pair['mask_pixels'], pair['common_mask_pixels']):
            raise ValueError('Les pixels des masques ont changé depuis l’audit')
        prefix = f'pairs/{pair["index"]:03d}'
        images = {'source_crop': (prefix+'-source.png', source_crop),
                  'box_overlay': (prefix+'-boxes.png', boxes),
                  'support_overlay': (prefix+'-support.png', support)}
        for name, pixels in images.values():
            cv2.imwrite(str(output/name), pixels)
        diagnostic_pairs.append(dict(pair, texts=[w['text'] for w in words], crop=crop,
            intersection_size=[c-a, d-b], diagnostic_claim=pair_claim(pair, profiles),
            **{key: name for key, (name, _) in images.items()}))
    colliding = {p[k] for p in pairs for k in ('line_a', 'line_b')}
    shared = {p[k] for p in pairs if p['common_mask_pixels'] for k in ('line_a', 'line_b')}
    summary = dict(version=VERSION, word_pairs=len(pairs), colliding_lines=len(colliding),
        lines_with_at_least_one_shared_mask_collision=len(shared),
        lines_without_any_shared_mask_collision=len(colliding-shared),
        pair_support_kinds=dict(Counter(p['support_kind'] for p in pairs)),
        no_common_mask_pairs_without_raw_dark_pixels=sum(not p['common_mask_pixels'] and p['raw_dark_pixels'] == 0 for p in pairs),
        no_common_mask_pairs_with_entirely_proved_own_word_masks=sum(not p['common_mask_pixels'] and all(p['diagnostic_claim']['whole_word_masks_only_proved_own_ink']) for p in diagnostic_pairs),
        annotations_preserved=len(annotations), lines_with_words=sum(bool(a.get('words')) for a in annotations),
        words_preserved=sum(len(a.get('words') or []) for a in annotations),
        xsd_validation=xsd, production_validation=production, shape_contract=schema_shape_contract(),
        annotations_sha256_unchanged=sha(ann_path) == sha(output/'annotations.snapshot.json'),
        annotation_statuses_changed=False, training_export=False, promoted=False, criteria_met=False,
        reading_certified=False, glyphs_certified=False, ctc_calls=0, reading_calls=0, reference_inputs=False)
    sources = [image, ann_path, source/'segmentation.json', source/'geometry-cache/state.json',
               audit/'provenance.json', audit/'word-pairs.json', audit/'word-profiles.json']
    inputs = {str(path.resolve()): sha(path) for path in sources}
    (output/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    (output/'diagnostic-pairs.json').write_text(json.dumps(diagnostic_pairs, ensure_ascii=False, indent=2))
    (output/'mask-manifest.json').write_text(json.dumps(mask_manifest, ensure_ascii=False, indent=2))
    (output/'index.html').write_text(_gallery(diagnostic_pairs, summary))
    (output/'provenance.json').write_text(json.dumps(dict(inputs=inputs, implementation_sha256=sha(__file__),
        mask_implementations={name: sha(path) for name, path in [('ink', ink.__file__),
            ('page_line_ink', Path(__file__).with_name('page_line_ink.py')),
            ('page_line_ink_v2', Path(__file__).with_name('page_line_ink_v2.py'))]},
        reference_inputs=False, promoted=False), ensure_ascii=False, indent=2))
    return summary


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('image', 'source', 'variant', 'audit', 'output'):
        parser.add_argument(name)
    args = parser.parse_args()
    print(json.dumps(export_diagnostic(args.image, args.source, args.variant, args.audit, args.output), ensure_ascii=False, indent=2))
