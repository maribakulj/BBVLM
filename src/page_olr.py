"""Structure Markdown reliée aux IDs de lignes ; sémantique explicitement provisoire."""
from __future__ import annotations

from page_anchors import save_json


VERSION = 'markdown-linked-layout-v1'


def infer_structure(alignment, annotations=None):
    """L'ordre vient du Markdown, la géométrie des lignes de l'image.

    Un titre Markdown est une proposition de titre. Il ne prouve pas à lui
    seul une frontière d'article : les regroupements sont des candidats
    séparés, sans article_id promu dans les exports.
    """
    by_id = {a['line_id']: a for a in alignment['assignments']}
    if annotations is not None:
        for annotation in annotations:
            if annotation['id'] in by_id:
                by_id[annotation['id']] = {**by_id[annotation['id']], **annotation}
    blocks, unresolved, article_candidates = [], [], []
    current_article = None
    seen = set()
    for source in alignment['blocks']:
        kind = {'heading': 'heading', 'table_cell': 'table'}.get(source['role'], 'text')
        # Une frontière de titre existe dans le Markdown même si son
        # positionnement a échoué ; elle doit séparer les articles candidats.
        if kind == 'heading':
            current_article = dict(id='candidate_' + source['id'], title=source['text'],
                                   block_ids=[], line_ids=[], uncertain=True,
                                   heading_located=bool(source['line_ids']),
                                   reason='heading_to_next_heading_is_not_certified_article_boundary')
            article_candidates.append(current_article)
        members = [by_id[lid] for lid in source['line_ids']]
        if not members:
            if source['text'].strip():
                unresolved.append(dict(markdown_block_id=source['id'], start=source['start'],
                                       end=source['end'], text=source['text'], reason='no_spatial_match'))
            continue
        ids = [a['line_id'] for a in members]
        if seen.intersection(ids):
            raise ValueError('Une ligne appartient à plusieurs blocs Markdown')
        seen.update(ids)
        bbox = [min(a['bbox'][0] for a in members), min(a['bbox'][1] for a in members),
                max(a['bbox'][2] for a in members), max(a['bbox'][3] for a in members)]
        block = dict(id='B_' + source['id'], markdown_block_id=source['id'],
                     type=kind, type_source='markdown_structure', bbox=bbox, line_ids=ids,
                     article_id=None, uncertain=True, status='provisional_markdown_structure',
                     text_start=source['start'], text_end=source['end'])
        blocks.append(block)
        if current_article is not None:
            current_article['block_ids'].append(block['id'])
            current_article['line_ids'].extend(ids)
    if seen != set(by_id):
        raise ValueError('Des lignes appariées ne sont référencées par aucun bloc')
    return dict(version=VERSION, provider='bbvlm', model=VERSION, blocks=blocks,
                articles=[], article_candidates=article_candidates,
                reading_order=[b['id'] for b in blocks], line_reading_order=alignment['reading_order'],
                unlocated_markdown_blocks=unresolved, unmatched_lines=alignment['unmatched_lines'],
                text_coverage=alignment['text_coverage'],
                nontext_status='not_detected_by_markdown_parser',
                semantic_certified=False, complete_pipeline_certified=False,
                geometry_source='automatic_image_lines', text_source_sha256=alignment['markdown_sha256'])


def write_structure(alignment, output, annotations=None):
    from pathlib import Path
    result = infer_structure(alignment, annotations)
    save_json(Path(output) / 'olr.json', result)
    return result
