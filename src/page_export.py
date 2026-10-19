"""Exporter les placements de VT entière sans exiger d'articles certifiés.

Les types et groupes proposés par le Markdown restent provisoires. Leur
incertitude sémantique n'efface pas un texte dont le placement est contrôlé.
Le texte de référence de l'export est exclusivement la production Markdown
sauvegardée et son appariement, jamais une transcription d'évaluation.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import unicodedata

from PIL import Image
from lxml import etree

import alto
from export_training import PAGE_NS, page_xml, polygon
from page_text_view import compact_line_text_view
from page_character_audit import audit as audit_characters


VERSION = 'page-markdown-geometry-export-v4'


def _json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def _source(alignment):
    markdown, plain = alignment.get('markdown'), alignment.get('plain_text')
    if not isinstance(markdown, str) or not isinstance(plain, str):
        raise ValueError('Markdown et texte intégral source requis')
    digest = hashlib.sha256(markdown.encode('utf-8')).hexdigest()
    if digest != alignment.get('markdown_sha256'):
        raise ValueError('Empreinte du Markdown différente de l’appariement')
    from page_alignment import markdown_document
    if markdown_document(markdown)[0] != plain:
        raise ValueError('Texte intégral différent du contenu Markdown source')
    artifact = alignment.get('markdown_artifact')
    if artifact:
        path = Path(artifact)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Artefact Markdown source absent ou modifié')
    by_id = {}
    for assignment in alignment.get('assignments', []):
        lid = assignment.get('line_id', assignment.get('id'))
        if not isinstance(lid, str) or not lid or lid in by_id:
            raise ValueError('Identifiants d’appariement absents ou dupliqués')
        by_id[lid] = assignment
    return markdown, plain, digest, by_id


def _validate_line(annotation, assignment, plain, width, height):
    text = annotation.get('text')
    if not isinstance(text, str) or not text.strip() or text != unicodedata.normalize('NFC', text):
        raise ValueError('texte vide ou non NFC')
    if '\n' in text or '\r' in text:
        raise ValueError('texte contenant plusieurs lignes physiques')
    if assignment is None:
        raise ValueError('appariement au Markdown absent')
    start, end = assignment.get('start'), assignment.get('end')
    source_text = annotation.get('source_text', text)
    if (not isinstance(start, int) or not isinstance(end, int) or not 0 <= start < end <= len(plain)
            or plain[start:end] != source_text or assignment.get('text') != source_text):
        raise ValueError('texte différent de la tranche Markdown source')
    view = compact_line_text_view(source_text)
    if text != view['text'] or annotation.get('source_spans', view['source_spans']) != view['source_spans']:
        raise ValueError('vue de ligne différente du contenu lexical Markdown source')
    box = annotation.get('bbox')
    if (not isinstance(box, (list, tuple)) or len(box) != 4
            or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in box)
            or not (0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height)):
        raise ValueError('boîte de ligne hors page')
    baseline = annotation.get('baseline') or []
    if baseline and (not isinstance(baseline, (list, tuple)) or len(baseline) < 2 or any(
            not isinstance(point, (list, tuple)) or len(point) != 2
            or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in point)
            or not (0 <= point[0] <= width and 0 <= point[1] <= height) for point in baseline)):
        raise ValueError('ligne de base invalide ou hors page')
    words, tokens = annotation.get('words'), list(re.finditer(r'\S+', text))
    if not isinstance(words, list) or [word.get('text') for word in words] != [m.group() for m in tokens]:
        raise ValueError('mots différents de la transcription')
    previous = None
    for word in words:
        x0, y0, x1, y1 = (word.get(k) for k in ('x0', 'y0', 'x1', 'y1'))
        if (any(not isinstance(v, (int, float)) or not math.isfinite(v) or int(v) != v for v in (x0, y0, x1, y1))
                or not (box[0] <= x0 <= x1 < box[2] and box[1] <= y0 <= y1 < box[3])
                or previous is not None and previous >= x0):
            raise ValueError('mot hors de sa ligne ou mots superposés')
        if word.get('synthetic'):
            raise ValueError('boîte de mot synthétique')
        previous = x1
    # Les caractères ont un diagnostic séparé. Leur absence ou invalidité
    # n'annule pas une boîte de mot observée et contrôlée.
    return tokens


def _conflicts(annotations, source_assignments, permitted_word_overlaps=()):
    """Empêcher tout double emploi de glyphes ou d'une tranche de la VT."""
    conflicts, active = set(), []
    for annotation in sorted(annotations, key=lambda a: source_assignments[a['id']]['start']):
        assignment = source_assignments[annotation['id']]
        active = [(lid, end) for lid, end in active if end > assignment['start']]
        if active:
            conflicts.add(annotation['id'])
            conflicts.update(lid for lid, end in active)
        active.append((annotation['id'], assignment['end']))
    active = []
    permitted={frozenset(pair) for pair in permitted_word_overlaps}
    for lid, wid, word in sorted(((a['id'], f"{a['id']}_W{i+1:02d}", w) for a in annotations for i,w in enumerate(a['words'])), key=lambda pair: pair[2]['y0']):
        active = [(other, oid, b) for other, oid, b in active if b['y1'] >= word['y0']]
        for other, oid, box in active:
            if other != lid and min(box['x1'], word['x1']) >= max(box['x0'], word['x0']):
                if frozenset((wid,oid)) not in permitted:
                    conflicts.update((lid, other))
        active.append((lid, wid, word))
    return conflicts


def export(image, directory):
    """Écrire ALTO, PAGE, IR et JSONL ; conserver les incertitudes séparément."""
    image, directory = Path(image), Path(directory)
    annotations = json.loads((directory / 'annotations.json').read_text(encoding='utf-8'))
    provenance = json.loads((directory / 'provenance.json').read_text(encoding='utf-8'))
    alignment = json.loads((directory / 'page-alignment.json').read_text(encoding='utf-8'))
    olr = json.loads((directory / 'olr.json').read_text(encoding='utf-8'))
    reading_metadata = provenance.get('lecture_provenance') or {}
    page_reading_uncertain = provenance.get('page_reading_uncertain',
        reading_metadata.get('page_reading_uncertain', reading_metadata.get('uncertain')))
    markdown, plain, markdown_sha256, assignments = _source(alignment)
    with Image.open(image) as source_image:
        width, height = source_image.size
    if provenance.get('taille') != [width, height] or alignment.get('image_size') != [width, height]:
        raise ValueError('Dimensions de page incohérentes')
    image_sha256 = hashlib.sha256(image.read_bytes()).hexdigest()
    if provenance.get('image_sha256', image_sha256) != image_sha256:
        raise ValueError('Image différente de celle des placements')
    permitted_overlaps=[]
    ownership_path=directory/'ownership-overlap-permissions.json'
    if ownership_path.exists():
        ownership=json.loads(ownership_path.read_text())
        if (ownership.get('image_sha256')!=image_sha256 or
                ownership.get('annotations_sha256')!=hashlib.sha256((directory/'annotations.json').read_bytes()).hexdigest() or
                ownership.get('basis')!='zero_shared_owned_ink_pixels'):
            raise ValueError('Audit des chevauchements absent ou périmé')
        permitted_overlaps=ownership['pairs']
    by_id = {a['id']: a for a in annotations}
    if len(by_id) != len(annotations):
        raise ValueError('Identifiants d’annotations dupliqués')
    accepted, excluded = [], []
    for annotation in annotations:
        if annotation.get('training_eligible') is not True:
            excluded.append(dict(id=annotation['id'], text=annotation['text'], status=annotation['status'],
                                 reason='reading_or_geometry_unresolved', assignment_status=annotation.get('assignment_status')))
            continue
        try:
            _validate_line(annotation, assignments.get(annotation['id']), plain, width, height)
        except (ValueError, TypeError, KeyError) as exc:
            excluded.append(dict(id=annotation['id'], text=annotation.get('text'), status=annotation.get('status'),
                                 reason='export_validation_failed', detail=str(exc)))
            continue
        accepted.append(annotation)
    conflicts = _conflicts(accepted, assignments, permitted_overlaps)
    for annotation in accepted:
        if annotation['id'] in conflicts:
            excluded.append(dict(id=annotation['id'], text=annotation['text'], status=annotation['status'],
                                 reason='overlapping_source_text_or_word_geometry'))
    accepted = [a for a in accepted if a['id'] not in conflicts]
    accepted_by_id = {a['id']: a for a in accepted}
    character_audits = {a['id']: audit_characters(a, page_width=width) for a in accepted}

    # Une OLR incomplète ne doit pas retirer une ligne déjà placée : les lignes
    # absentes ou proposées dans plusieurs groupes ont une région provisoire.
    memberships = defaultdict(list)
    for block in olr.get('blocks', []):
        for lid in block.get('line_ids', []):
            memberships[lid].append(block.get('id'))
    grouped, blocks = set(), []
    used_ids = set(by_id)
    for original in olr.get('blocks', []):
        lids = [lid for lid in original.get('line_ids', [])
                if lid in accepted_by_id and len(memberships[lid]) == 1]
        if not lids:
            continue
        block_id = original.get('id')
        if not isinstance(block_id, str) or not block_id or block_id in used_ids:
            raise ValueError('Identifiant de bloc absent ou dupliqué')
        used_ids.add(block_id)
        grouped.update(lids)
        blocks.append(dict(original, id=block_id, line_ids=lids))
    for annotation in accepted:
        lid = annotation['id']
        if lid in grouped:
            continue
        block_id = 'B_UNGROUPED_' + lid
        while block_id in used_ids:
            block_id += '_'
        used_ids.add(block_id)
        blocks.append(dict(id=block_id, type='text', line_ids=[lid], uncertain=True,
                           type_source='unresolved_group', grouping_status='missing_or_ambiguous'))
    blocks.sort(key=lambda b: min(assignments[lid]['start'] for lid in b['line_ids']))
    target_image = directory / image.name
    if target_image.resolve() != image.resolve():
        if not target_image.exists() or hashlib.sha256(target_image.read_bytes()).hexdigest() != image_sha256:
            shutil.copy2(image, target_image)
    page_id = 'P_' + image_sha256[:24]
    ir = dict(id=page_id, width=width, height=height, image=str(target_image.resolve()), blocks=[], articles=[],
              provenance=dict(reader=str(provenance.get('lecture', 'page_markdown')),
                              geometry=str(provenance.get('geometrie', 'unknown')),
                              image_sha256=image_sha256, markdown_sha256=markdown_sha256,
                              export_version=VERSION, olr_model=str(olr.get('model', 'markdown_structure')),
                              olr_status='provisional_markdown_structure; article relations unassigned',
                              olr_provenance='olr.json', alignment_provenance='page-alignment.json',
                              geometry_provenance='annotations.json', certification='automatic; not independently certified'))
    ir['provenance'].update(page_reading_uncertain=json.dumps(page_reading_uncertain), reading_certified='false')
    alto_blocks, training = [], []
    block_provenance, line_provenance = {}, {}
    for block in blocks:
        members = sorted((accepted_by_id[lid] for lid in block['line_ids']), key=lambda a: assignments[a['id']]['start'])
        bb = [min(a['bbox'][0] for a in members), min(a['bbox'][1] for a in members),
              max(a['bbox'][2] for a in members), max(a['bbox'][3] for a in members)]
        kind = block.get('type', 'text')
        if kind not in {'text', 'heading', 'caption', 'advert', 'table', 'other'}:
            kind = 'other'
        olr_metadata = dict(uncertain=bool(block.get('uncertain', True)),
                            type_source=block.get('type_source', 'unknown'),
                            type=block.get('type'), proposed_article_id=block.get('article_id'),
                            status='provisional_markdown_structure', article_certified=False)
        block_provenance[block['id']] = deepcopy(olr_metadata)
        lines, alto_lines = [], []
        for annotation in members:
            lid, text, box = annotation['id'], annotation['text'], annotation['bbox']
            assigned = assignments[lid]
            exported_chars = annotation['chars'] if character_audits[lid]['transportable'] else []
            character_sources = (annotation.get('alignment') or {}).get('character_position_sources',
                                ['line_ctc'] * len(text))
            if not exported_chars or 'inconsistent_character_provenance' in character_audits[lid]['issue_counts']:
                character_sources = []
            line = dict(id=lid, polygon=polygon(box), baseline=annotation.get('baseline', []),
                        text=text, chars=exported_chars, article=None)
            line_provenance[lid] = dict(page_reading_uncertain=annotation.get('page_reading_uncertain', page_reading_uncertain),
                                       reading_certified=False, character_geometry=character_audits[lid],
                                       character_training_eligible=character_audits[lid]['consistent'])
            lines.append(line)
            alto_lines.append(dict(line, bbox=[box[0], box[1], box[2] - 1, box[3] - 1], words=annotation['words']))
            tokens = list(re.finditer(r'\S+', text))
            training.append(dict(page_id=page_id, line_id=lid, block_id=block['id'], article_id=None,
                image=ir['image'], image_relative=target_image.name, bbox=box, text=text, chars=exported_chars,
                raw_text=annotation.get('raw_text', annotation.get('source_text', text)), linebreak=annotation.get('linebreak'),
                reading_job_id=annotation.get('reading_job_id'), model_claim=annotation.get('model'),
                model_display_terminal=annotation.get('model_display_terminal'),
                character_scope=(annotation.get('alignment') or {}).get('character_scope', 'line'),
                character_position_sources=character_sources,
                original_character_positions_artifact='annotations.json',
                character_geometry=character_audits[lid],
                character_training_eligible=character_audits[lid]['consistent'],
                **({'character_realignments': annotation['character_realignments']} if annotation.get('character_realignments') else {}),
                **({'character_position_repairs': annotation['character_position_repairs']} if annotation.get('character_position_repairs') else {}),
                words=[dict(text=w['text'], start=m.start(), end=m.end(), bbox=[w['x0'], w['y0'], w['x1'] + 1, w['y1'] + 1])
                       for m, w in zip(tokens, annotation['words'])],
                source_text=dict(markdown_sha256=markdown_sha256, plain_start=assigned['start'], plain_end=assigned['end'],
                                 original=annotation.get('source_text', text),
                                 view_source_spans=compact_line_text_view(annotation.get('source_text', text))['source_spans'],
                                 view_transform=compact_line_text_view(annotation.get('source_text', text))['transform']),
                assignment_status=annotation.get('assignment_status', 'matched'),
                page_reading_uncertain=annotation.get('page_reading_uncertain', page_reading_uncertain),
                reading_certified=False,
                olr=deepcopy(olr_metadata), coordinate_convention='xyxy half-open pixels',
                quality_status='pseudo_annotation; not independently certified'))
        ir['blocks'].append(dict(id=block['id'], type=kind, polygon=polygon(bb), lines=lines))
        alto_blocks.append(dict(id=block['id'], type=kind, article_id=None,
                                x0=bb[0], y0=bb[1], x1=bb[2] - 1, y1=bb[3] - 1, lines=alto_lines))
    # Le contrat Axel n'a aucun champ extensible sur Block/Line : les extras
    # y sont silencieusement ignorés. Ses métadonnées résident exclusivement
    # dans Page.provenance, dont toutes les valeurs sont des chaînes.
    ir['provenance']['block_olr'] = json.dumps(block_provenance, ensure_ascii=False, sort_keys=True)
    ir['provenance']['line_reading_provenance'] = json.dumps(line_provenance, ensure_ascii=False, sort_keys=True)
    description = ('Placements contrôlés du Markdown intégral. Groupes, types et ordre issus du Markdown '
                   'provisoires ; relations d’articles non attribuées. Incertitudes conservées dans olr.json '
                   'et training.jsonl. Texte intégral conservé dans page-alignment.json. Non certifié.')
    alto_data = alto.build(width, height, image.name, alto_blocks, 'BBVLM Markdown/CTC', description)
    alto_result = alto.validate(alto_data, permitted_word_overlaps=permitted_overlaps)
    page_root = etree.fromstring(page_xml(ir, annotations))
    page_metadata = page_root.find('{' + PAGE_NS + '}Metadata')
    etree.SubElement(page_metadata, '{' + PAGE_NS + '}Comments').text = description
    for key, value in [('markdown_sha256', markdown_sha256), ('reading_certified', 'false'),
                       ('page_reading_uncertain', json.dumps(page_reading_uncertain))]:
        etree.SubElement(page_metadata, '{' + PAGE_NS + '}MetadataItem', type='other', name=key, value=value)
    for region in page_root.findall('.//{' + PAGE_NS + '}TextRegion'):
        region.set('custom', region.get('custom', '') + ' bbvlm {semantic_status:provisional_markdown_structure;}')
    page_data = etree.tostring(page_root, encoding='UTF-8', xml_declaration=True, pretty_print=True)
    schema = Path(__file__).resolve().parents[1] / 'schemas/page-2019.xsd'
    etree.XMLSchema(etree.parse(str(schema))).assertValid(page_root)
    intervals = sorted((assignments[a['id']]['start'], assignments[a['id']]['end']) for a in accepted)
    text_excluded, offset = [], 0
    for start, end in intervals + [(len(plain), len(plain))]:
        if start > offset:
            text = plain[offset:start]
            text_excluded.append(dict(start=offset, end=start, text=text,
                                      status='unplaced_text' if text.strip() else 'formatting_whitespace'))
        offset = end
    total = sum(not char.isspace() for char in plain)
    exported = sum(sum(not char.isspace() for char in a['text']) for a in accepted)
    report = dict(version=VERSION, lines_total=len(annotations), lines_exported=len(training), excluded=len(excluded),
                  coverage=len(training) / len(annotations) if annotations else 0,
                  text_coverage=dict(nonspace_characters=total, exported_nonspace_characters=exported,
                                     fraction=exported / total if total else None),
                  source_markdown_sha256=markdown_sha256, full_text_preserved=True, text_changed=False,
                  lexical_text_changed=False,
                  layout_whitespace_normalized_lines=sum(a.get('source_text', a['text']) != a['text'] for a in accepted),
                  page_reading_uncertain=page_reading_uncertain, reading_certified=False,
                  excluded_reasons=dict(Counter(item['reason'] for item in excluded)),
                  alto_validation=alto_result, page_validation=True, criteria_met=False,
                  olr_status='provisional_markdown_structure', articles_certified=0,
                  provisional_blocks=len(blocks), coordinate_convention='IR/PAGE/JSONL: half-open; boxer words: inclusive')
    report['lines_with_baselines'] = sum(bool(a.get('baseline')) for a in accepted)
    report['baseline_reader_compatible'] = report['lines_with_baselines'] == len(accepted)
    report['character_geometry'] = dict(
        consistent_lines=sum(a['consistent'] for a in character_audits.values()),
        inconsistent_lines=sum(not a['consistent'] for a in character_audits.values()),
        character_training_eligible_lines=sum(a['consistent'] for a in character_audits.values()),
        lines_without_exportable_character_positions=sum(not a['transportable'] for a in character_audits.values()),
        issue_counts=dict(sum((Counter(a['issue_counts']) for a in character_audits.values()), Counter())),
        certified=False, scope='coordinate consistency only; word exports retained independently')
    for filename, data in [('training.alto.xml', alto_data), ('page.alto.xml', alto_data),
                           ('training.page.xml', page_data), ('page.page.xml', page_data)]:
        (directory / filename).write_bytes(data)
    _json(directory / 'axel-ir.json', ir)
    (directory / 'training.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in training), encoding='utf-8')
    _json(directory / 'training-excluded.json', excluded)
    _json(directory / 'text-unplaced.json', text_excluded)
    _json(directory / 'character-geometry-audit.json', character_audits)
    _json(directory / 'training-export.json', report)
    _json(directory / 'page-export.json', report)
    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('image')
    parser.add_argument('directory')
    arguments = parser.parse_args()
    print(json.dumps(export(arguments.image, arguments.directory), ensure_ascii=False, indent=2))
